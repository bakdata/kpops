These variables are a lower priority alternative to the commands' flags. If a variable is set, the corresponding flag does not have to be specified in commands. Variables marked as required can instead be set as flags.

|        Name        |Default Value|Required|                                                                                Description                                                                                 |
|--------------------|-------------|--------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|KPOPS_CONFIG_PATH   |.            |False   |Path to the dir containing config.yaml files                                                                                                                                |
|KPOPS_DEFAULT_PATH  |             |False   |Path to defaults folder                                                                                                                                                     |
|KPOPS_DOTENV_PATH   |             |False   |Path to dotenv file. Multiple files can be provided. The files will be loaded in order, with each file overriding the previous one.                                         |
|KPOPS_ENVIRONMENT   |             |False   |The environment you want to generate and deploy the pipeline to. Suffix your environment files with this value (e.g. defaults_development.yaml for environment=development).|
|KPOPS_PIPELINE_PATH |             |True    |Path to YAML with pipeline definition                                                                                                                                       |
|KPOPS_PIPELINE_STEPS|             |False   |Comma separated list of steps to apply the command on                                                                                                                       |
