from __future__ import annotations

import logging
from pathlib import Path

from kpops.cli.options import FilterType
from kpops.config import KpopsConfig
from kpops.pipeline import (
    Pipeline,
)

log = logging.getLogger("KPOpsAPI")


def parse_steps(steps: str) -> set[str]:
    return set(steps.split(","))


def generate(
    pipeline_path: Path,
    dotenv: list[Path] | None = None,
    config: Path = Path(),
    steps: str | None = None,
    filter_type: FilterType = FilterType.INCLUDE,
    environment: str | None = None,
    verbose: bool = False,
) -> Pipeline:
    kpops_config = KpopsConfig.create(
        config,
        dotenv,
        environment,
        verbose,
    )
    pipeline = Pipeline.create(pipeline_path, kpops_config, environment)
    log.info(f"Picked up pipeline '{pipeline_path.parent.name}'")
    if steps:
        component_names = parse_steps(steps)
        log.debug(
            f"KPOPS_PIPELINE_STEPS is defined with values: {component_names} and filter type of {filter_type.value}"
        )

        predicate = filter_type.create_default_step_names_filter_predicate(
            component_names
        )
        pipeline.filter(predicate)
        log.info(f"Filtered pipeline:\n{pipeline.step_names}")
    return pipeline
