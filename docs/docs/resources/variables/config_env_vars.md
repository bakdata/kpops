
These variables are a lower priority alternative to the settings in `config.yaml`. Variables marked as required can instead be set in the pipeline config.

|         Name          |    Default Value    |Required|                                                                                Description                                                                                 |  Setting name   |
|-----------------------|---------------------|--------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------|
|KPOPS_ENVIRONMENT      |                     |True    |The environment you want to generate and deploy the pipeline to. Suffix your environment files with this value (e.g. defaults_development.yaml for environment=development).|environment      |
|KPOPS_KAFKA_BROKERS    |                     |True    |The comma separated Kafka brokers address.                                                                                                                                  |brokers          |
|KPOPS_REST_PROXY_HOST  |http://localhost:8082|False   |Address of the Kafka REST Proxy.                                                                                                                                            |kafka_rest_url   |
|KPOPS_CONNECT_HOST     |http://localhost:8083|False   |Address of Kafka Connect.                                                                                                                                                   |kafka_connect_url|
|KPOPS_TIMEOUT          |                  300|False   |The timeout in seconds that specifies when actions like deletion or deploy timeout.                                                                                         |timeout          |
|KPOPS_RETAIN_CLEAN_JOBS|False                |False   |Whether to retain clean up jobs in the cluster or uninstall the, after completion.                                                                                          |retain_clean_jobs|
