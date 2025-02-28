from typing import ClassVar

from croniter import croniter
from pydantic import ConfigDict, Field, field_validator

from kpops.components.common.kubernetes_model import RestartPolicy
from kpops.components.streams_bootstrap.model import (
    KafkaConfig,
    StreamsBootstrapValues,
)
from kpops.core.exception import ValidationError
from kpops.utils.docstring import describe_attr


class ProducerConfig(KafkaConfig):
    """Kafka Streams settings specific to Producer."""


class ProducerAppValues(StreamsBootstrapValues):
    """Settings specific to producers.

    :param kafka: Kafka Streams settings
    :param deployment: Deploy the producer as a Kubernetes Deployment (thereby ignoring Job-related configurations)
    :param restart_policy: See https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#restart-policy
    :param schedule: Cron expression to denote a schedule this producer app should be run on. It will then be deployed as a CronJob instead of a Job.
    :param suspend: Whether to suspend the execution of the cron job.
    :param successful_jobs_history_limit: The number of successful jobs to retain.
    :param failed_jobs_history_limit: The number of unsuccessful jobs to retain.
    :param backoff_limit: The number of times to restart an unsuccessful job.
    :param ttl_seconds_after_finished: See https://kubernetes.io/docs/concepts/workloads/controllers/ttlafterfinished/#ttl-after-finished-controller
    """

    kafka: ProducerConfig = Field(description=describe_attr("kafka", __doc__))  # pyright: ignore[reportIncompatibleVariableOverride]

    deployment: bool | None = Field(
        default=None, description=describe_attr("deployment", __doc__)
    )

    restart_policy: RestartPolicy | None = Field(
        default=None,
        description=describe_attr("restart_policy", __doc__),
    )

    schedule: str | None = Field(
        default=None, description=describe_attr("schedule", __doc__)
    )

    suspend: bool | None = Field(
        default=None, description=describe_attr("suspend", __doc__)
    )

    successful_jobs_history_limit: int | None = Field(
        default=None,
        description=describe_attr("successful_jobs_history_limit", __doc__),
    )

    failed_jobs_history_limit: int | None = Field(
        default=None, description=describe_attr("failed_jobs_history_limit", __doc__)
    )

    backoff_limit: int | None = Field(
        default=None, description=describe_attr("backoff_limit", __doc__)
    )

    ttl_seconds_after_finished: int | None = Field(
        default=None, description=describe_attr("ttl_seconds_after_finished", __doc__)
    )

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow")

    @field_validator("schedule")
    @classmethod
    def schedule_cron_validator(cls, schedule: str | None) -> str | None:
        """Ensure that the defined schedule value is valid."""
        if schedule and not croniter.is_valid(schedule):
            msg = f"The schedule field '{schedule}' must be a valid cron expression."
            raise ValidationError(msg)
        return schedule
