from pydantic import BaseSettings


class HelmCommandConfig(BaseSettings):
    debug: bool = False
    force: bool = False
    timeout: str = "5m0s"
    wait: bool = True
    wait_for_jobs: bool = False

    class Config:
        env_prefix = "HELM_COMMAND_CONFIG_"