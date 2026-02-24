from enum import Enum


class AppType(Enum):
    STREAMS_APP = "streams-app"
    PRODUCER_APP = "producer-app"
    CONSUMER_APP = "consumer-app"
    CLEANUP_STREAMS_APP = "streams-app-cleanup-job"
    CLEANUP_PRODUCER_APP = "producer-app-cleanup-job"
    CLEANUP_CONSUMER_APP = "consumer-app-cleanup-job"
