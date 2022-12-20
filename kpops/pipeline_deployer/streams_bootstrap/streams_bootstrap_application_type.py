from enum import Enum


class ApplicationType(Enum):
    STREAMS_APP = "streams-app"
    PRODUCER_APP = "producer-app"
    CLEANUP_STREAMS_APP = "streams-app-cleanup-job"
    CLEANUP_PRODUCER_APP = "producer-app-cleanup-job"
