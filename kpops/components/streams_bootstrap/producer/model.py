from croniter import croniter
from pydantic import ConfigDict, Field, field_validator

from kpops.api.exception import ValidationError
from kpops.components.common.kubernetes_model import RestartPolicy
from kpops.components.streams_bootstrap.model import (
    KafkaConfig,
    StreamsBootstrapValues,
)
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

    kafka: ProducerConfig = Field(description=describe_attr("kafka", __doc__))

    deployment: bool = Field(
        default=False, description=describe_attr("deployment", __doc__)
    )

    restart_policy: RestartPolicy = Field(
        default=RestartPolicy.ON_FAILURE,
        description=describe_attr("restart_policy", __doc__),
    )

    schedule: str | None = Field(
        default=None, description=describe_attr("schedule", __doc__)
    )

    suspend: bool = Field(default=False, description=describe_attr("suspend", __doc__))

    successful_jobs_history_limit: int = Field(
        default=1, description=describe_attr("successful_jobs_history_limit", __doc__)
    )

    failed_jobs_history_limit: int = Field(
        default=1, description=describe_attr("failed_jobs_history_limit", __doc__)
    )

    backoff_limit: int = Field(
        default=6, description=describe_attr("backoff_limit", __doc__)
    )

    ttl_seconds_after_finished: int = Field(
        default=100, description=describe_attr("ttl_seconds_after_finished", __doc__)
    )

    model_config = ConfigDict(extra="allow")

    @field_validator("schedule")
    @classmethod
    def schedule_cron_validator(cls, schedule: str) -> str:
        """Ensure that the defined schedule value is valid."""
        if schedule and not croniter.is_valid(schedule):
            msg = f"The schedule field '{schedule}' must be a valid cron expression."
            raise ValidationError(msg)
        return schedule
