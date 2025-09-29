from typing import ClassVar

from croniter import croniter
from pydantic import ConfigDict, field_validator

from kpops.components.common.kubernetes_model import RestartPolicy
from kpops.components.streams_bootstrap.model import (
    KafkaConfig,
    StreamsBootstrapValues,
)
from kpops.core.exception import ValidationError


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

    kafka: ProducerConfig = ProducerConfig()  # pyright: ignore[reportIncompatibleVariableOverride]
    deployment: bool | None = None
    restart_policy: RestartPolicy | None = None
    schedule: str | None = None
    suspend: bool | None = None
    successful_jobs_history_limit: int | None = None
    failed_jobs_history_limit: int | None = None
    backoff_limit: int | None = None
    ttl_seconds_after_finished: int | None = None

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow")

    @field_validator("schedule")
    @classmethod
    def schedule_cron_validator(cls, schedule: str | None) -> str | None:
        """Ensure that the defined schedule value is valid."""
        if schedule and not croniter.is_valid(schedule):
            msg = f"The schedule field '{schedule}' must be a valid cron expression."
            raise ValidationError(msg)
        return schedule
