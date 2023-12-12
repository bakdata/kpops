These variables are a lower priority alternative to the commands' flags. If a variable is set, the corresponding flag does not have to be specified in commands. Variables marked as required can instead be set as flags.

|         Name          |Default Value|Required|                                                            Description                                                            |
|-----------------------|-------------|--------|-----------------------------------------------------------------------------------------------------------------------------------|
|KPOPS_PIPELINE_BASE_DIR|.            |False   |Base directory to the pipelines (default is current working directory)                                                             |
|KPOPS_CONFIG_PATH      |config.yaml  |False   |Path to the config.yaml file                                                                                                       |
|KPOPS_DEFAULT_PATH     |             |False   |Path to defaults folder                                                                                                            |
|KPOPS_DOTENV_PATH      |             |False   |Path to dotenv file. Multiple files can be provided. The files will be loaded in order, with each file overriding the previous one.|
|KPOPS_PIPELINE_PATH    |             |True    |Path to YAML with pipeline definition                                                                                              |
|KPOPS_PIPELINE_STEPS   |             |False   |Comma separated list of steps to apply the command on                                                                              |
