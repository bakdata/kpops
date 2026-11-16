"""Generate the unversioned llms.txt at the root of the gh-pages branch."""

import json
import sys
from pathlib import Path

SITE_URL = "https://bakdata.github.io/kpops/"


def generate(pages: Path) -> str:
    versions = json.loads((pages / "versions.json").read_text())
    lines = [
        "# KPOps",
        "",
        "> Deploy Kafka pipelines to Kubernetes.",
        "",
        "The documentation is versioned. Use the version matching the KPOps version of the project.",
        "",
        "## Versions",
        "",
    ]
    for version in versions:
        name = version["version"]
        if not (pages / name / "llms.txt").is_file():
            continue
        aliases = f" ({', '.join(version['aliases'])})" if version["aliases"] else ""
        url = f"{SITE_URL}{name}/"
        entry = f"- [{version['title']}{aliases}]({url}llms.txt)"
        if (pages / name / "llms-full.txt").is_file():
            entry += f": [full text]({url}llms-full.txt)"
        lines.append(entry)
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    pages = Path(sys.argv[1])
    (pages / "llms.txt").write_text(generate(pages))
