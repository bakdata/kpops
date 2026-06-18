These variables take precedence over the commands' flags. If a variable is set, the corresponding flag does not have to be specified in commands. Variables marked as required can instead be set as flags.

|        Name        |Default Value|Required|                                                                                Description                                                                                 |
|--------------------|-------------|--------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|KPOPS_CONFIG_PATH   |.            |False   |Path to the dir containing config.yaml files                                                                                                                                |
|KPOPS_DOTENV_PATH   |             |False   |Path to dotenv file. Multiple files can be provided. The files will be loaded in order, with each file overriding the previous one.                                         |
|KPOPS_ENVIRONMENT   |             |False   |The environment you want to generate and deploy the pipeline to. Suffix your environment files with this value (e.g. defaults_development.yaml for environment=development).|
|KPOPS_OPERATION_MODE|managed      |False   |How KPOps should operate.                                                                                                                                                   |
|KPOPS_PIPELINE_PATHS|             |True    |Paths to dir containing 'pipeline.yaml' or files named 'pipeline.yaml'.                                                                                                     |
|KPOPS_PIPELINE_STEPS|             |False   |Comma separated list of steps to apply the command on                                                                                                                       |
