import { readFileSync } from "node:fs";

const MARKER = "<!-- pr-review-agent -->";
const BOT_LOGIN = "github-actions[bot]";

export function parseReview(text) {
  const start = text.indexOf("{");
  const end = text.lastIndexOf("}");
  if (start === -1 || end < start) throw new Error(`No JSON object in agent output:\n${text}`);
  const review = JSON.parse(text.slice(start, end + 1));
  if (!["approve", "comment"].includes(review.verdict)) throw new Error(`Invalid verdict: ${review.verdict}`);
  return {
    verdict: review.verdict,
    summary: (review.summary ?? "").trim(),
    findings: (review.findings ?? []).filter((f) => f?.path && Number.isInteger(f.line) && f.body?.trim()),
  };
}

export function commentableLines(patch) {
  const lines = new Map();
  let hunk = 0;
  let next = 0;
  for (const raw of patch.split("\n")) {
    if (raw.startsWith("@@ ")) {
      next = Number(/\+(\d+)/.exec(raw)[1]);
      hunk++;
    } else if (hunk > 0 && (raw.startsWith(" ") || raw.startsWith("+"))) {
      lines.set(next++, hunk);
    }
  }
  return lines;
}

function anchor(finding, files) {
  const hunks = files.get(finding.path);
  const hunk = hunks?.get(finding.line);
  if (hunk === undefined) return null;
  const comment = { path: finding.path, line: finding.line, side: "RIGHT", body: finding.body.trim() };
  const start = finding.start_line;
  if (Number.isInteger(start) && start < finding.line && hunks.get(start) === hunk) {
    Object.assign(comment, { start_line: start, start_side: "RIGHT" });
  }
  return comment;
}

function formatBody(summary, bodyFindings, hasFindings) {
  const parts = [summary, ...bodyFindings.map((f) => `\`${f.path}:${f.line}\`: ${f.body.trim()}`)].filter(Boolean);
  if (parts.length === 0 && !hasFindings) parts.push("No findings.");
  return [...parts, MARKER].join("\n\n");
}

export default async function postReview({ github, context, core }) {
  const { PR_NUMBER, HEAD_SHA, REVIEW_FILE } = process.env;
  const pr = { ...context.repo, pull_number: Number(PR_NUMBER) };

  const review = parseReview(readFileSync(REVIEW_FILE, "utf8"));
  const { data: current } = await github.rest.pulls.get(pr);
  const outdated = current.head.sha !== HEAD_SHA;
  const files = new Map();
  // the files API only returns patches for the current head, so line anchors for an older head can't be checked
  if (!outdated) {
    for (const file of await github.paginate(github.rest.pulls.listFiles, { ...pr, per_page: 100 })) {
      if (file.patch) files.set(file.filename, commentableLines(file.patch));
    }
  }

  const inline = [];
  const unanchored = [];
  for (const finding of review.findings) {
    const comment = anchor(finding, files);
    comment ? inline.push(comment) : unanchored.push(finding);
  }

  let summary = review.summary;
  let event = review.verdict === "approve" && review.findings.length === 0 ? "APPROVE" : "COMMENT";
  if (event === "APPROVE" && outdated) {
    event = "COMMENT";
    summary = `Not approved: new commits were pushed during the review of ${HEAD_SHA.slice(0, 7)}.`;
  }

  if (event !== "APPROVE") {
    const reviews = await github.paginate(github.rest.pulls.listReviews, { ...pr, per_page: 100 });
    for (const r of reviews.filter((r) => r.user?.login === BOT_LOGIN && r.state === "APPROVED")) {
      await github.rest.pulls.dismissReview({
        ...pr,
        review_id: r.id,
        message: "Superseded by a newer review.",
        event: "DISMISS",
      });
    }
  }

  const post = (comments, bodyFindings) =>
    github.rest.pulls.createReview({
      ...pr,
      commit_id: HEAD_SHA,
      event,
      body: formatBody(summary, bodyFindings, review.findings.length > 0),
      comments,
    });

  try {
    await post(inline, unanchored);
  } catch (error) {
    if (error.status !== 422) throw error;
    if (event === "APPROVE") {
      core.warning(`Approval rejected, posting a comment instead: ${error.message}`);
      event = "COMMENT";
      summary = "No findings. Approval failed, check whether GitHub Actions may approve pull requests in this repository.";
      await post([], []);
    } else if (inline.length > 0) {
      core.warning(`Inline comments rejected, posting all findings in the review body: ${error.message}`);
      await post([], review.findings);
    } else {
      throw error;
    }
  }
  core.info(`Posted ${event} review with ${inline.length} inline and ${unanchored.length} body findings.`);
}
