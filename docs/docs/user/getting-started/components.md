# Components

This section will cover the KPOps components and how `kpops deploy/destroy/clean/reset` affect them.

## KubernetesApp

### Deploy

### Destroy

### Clean

### Reset


## StreamsApp

### Deploy

### Destroy

### Clean

### Reset


## Producer

### Deploy

A Kubernetes job or cron job is deployed.
The output topics are created, and schemas are registered in the Schema registry if configured.

### Destroy

The associated Kubernetes resources are removed.

### Clean

The output topics of the Kafka producer are deleted as well as all associated schemas in the Schema Registry.

### Reset

Producers are not affected by reset as they are stateless.

## KafkaSinkConnector

### Deploy

### Destroy

### Clean

### Reset


## KafkaSourceConnector

### Deploy

### Destroy

### Clean

### Reset
