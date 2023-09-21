- [NAME](#name)
- [SYNOPSIS](#synopsis)
- [DESCRIPTION](#description)
- [POSITIONAL ARGUMENTS](#positional-arguments)
- [COMMAND `genius TestSpoutCtlSpout`](#command-genius-testspoutctlspout)
- [POSITIONAL ARGUMENTS _`genius TestSpoutCtlSpout`_](#positional-arguments-genius-testspoutctlspout)
- [COMMAND `genius TestSpoutCtlSpout rise`](#command-genius-testspoutctlspout-rise)
- [OPTIONS `genius TestSpoutCtlSpout rise`](#options-genius-testspoutctlspout-rise)
- [COMMAND `genius TestSpoutCtlSpout deploy`](#command-genius-testspoutctlspout-deploy)
- [OPTIONS `genius TestSpoutCtlSpout deploy`](#options-genius-testspoutctlspout-deploy)
- [COMMAND `genius TestSpoutCtlSpout help`](#command-genius-testspoutctlspout-help)
- [COMMAND `genius TestBoltCtlBolt`](#command-genius-testboltctlbolt)
- [POSITIONAL ARGUMENTS _`genius TestBoltCtlBolt`_](#positional-arguments-genius-testboltctlbolt)
- [COMMAND `genius TestBoltCtlBolt rise`](#command-genius-testboltctlbolt-rise)
- [OPTIONS `genius TestBoltCtlBolt rise`](#options-genius-testboltctlbolt-rise)
- [COMMAND `genius TestBoltCtlBolt deploy`](#command-genius-testboltctlbolt-deploy)
- [OPTIONS `genius TestBoltCtlBolt deploy`](#options-genius-testboltctlbolt-deploy)
- [COMMAND `genius TestBoltCtlBolt help`](#command-genius-testboltctlbolt-help)
- [COMMAND `genius rise`](#command-genius-rise)
- [OPTIONS `genius rise`](#options-genius-rise)
- [COMMAND `genius docker`](#command-genius-docker)
- [POSITIONAL ARGUMENTS _`genius docker`_](#positional-arguments-genius-docker)
- [COMMAND `genius docker package`](#command-genius-docker-package)
- [OPTIONS `genius docker package`](#options-genius-docker-package)
- [COMMAND `genius pod`](#command-genius-pod)
- [POSITIONAL ARGUMENTS _`genius pod`_](#positional-arguments-genius-pod)
- [COMMAND `genius pod status`](#command-genius-pod-status)
- [OPTIONS `genius pod status`](#options-genius-pod-status)
- [COMMAND `genius pod show`](#command-genius-pod-show)
- [OPTIONS `genius pod show`](#options-genius-pod-show)
- [COMMAND `genius pod describe`](#command-genius-pod-describe)
- [OPTIONS `genius pod describe`](#options-genius-pod-describe)
- [COMMAND `genius pod logs`](#command-genius-pod-logs)
- [OPTIONS `genius pod logs`](#options-genius-pod-logs)
- [COMMAND `genius deployment`](#command-genius-deployment)
- [POSITIONAL ARGUMENTS _`genius deployment`_](#positional-arguments-genius-deployment)
- [COMMAND `genius deployment create`](#command-genius-deployment-create)
- [OPTIONS `genius deployment create`](#options-genius-deployment-create)
- [COMMAND `genius deployment scale`](#command-genius-deployment-scale)
- [OPTIONS `genius deployment scale`](#options-genius-deployment-scale)
- [COMMAND `genius deployment describe`](#command-genius-deployment-describe)
- [OPTIONS `genius deployment describe`](#options-genius-deployment-describe)
- [COMMAND `genius deployment show`](#command-genius-deployment-show)
- [OPTIONS `genius deployment show`](#options-genius-deployment-show)
- [COMMAND `genius deployment delete`](#command-genius-deployment-delete)
- [OPTIONS `genius deployment delete`](#options-genius-deployment-delete)
- [COMMAND `genius deployment status`](#command-genius-deployment-status)
- [OPTIONS `genius deployment status`](#options-genius-deployment-status)
- [COMMAND `genius service`](#command-genius-service)
- [POSITIONAL ARGUMENTS _`genius service`_](#positional-arguments-genius-service)
- [COMMAND `genius service create`](#command-genius-service-create)
- [OPTIONS `genius service create`](#options-genius-service-create)
- [COMMAND `genius service delete`](#command-genius-service-delete)
- [OPTIONS `genius service delete`](#options-genius-service-delete)
- [COMMAND `genius service describe`](#command-genius-service-describe)
- [OPTIONS `genius service describe`](#options-genius-service-describe)
- [COMMAND `genius service show`](#command-genius-service-show)
- [OPTIONS `genius service show`](#options-genius-service-show)
- [COMMAND `genius job`](#command-genius-job)
- [POSITIONAL ARGUMENTS _`genius job`_](#positional-arguments-genius-job)
- [COMMAND `genius job create`](#command-genius-job-create)
- [OPTIONS `genius job create`](#options-genius-job-create)
- [COMMAND `genius job delete`](#command-genius-job-delete)
- [OPTIONS `genius job delete`](#options-genius-job-delete)
- [COMMAND `genius job status`](#command-genius-job-status)
- [OPTIONS `genius job status`](#options-genius-job-status)
- [COMMAND `genius cron_job`](#command-genius-cron_job)
- [POSITIONAL ARGUMENTS _`genius cron_job`_](#positional-arguments-genius-cron_job)
- [COMMAND `genius cron_job create_cronjob`](#command-genius-cron_job-create_cronjob)
- [OPTIONS `genius cron_job create_cronjob`](#options-genius-cron_job-create_cronjob)
- [COMMAND `genius cron_job delete_cronjob`](#command-genius-cron_job-delete_cronjob)
- [OPTIONS `genius cron_job delete_cronjob`](#options-genius-cron_job-delete_cronjob)
- [COMMAND `genius cron_job get_cronjob_status`](#command-genius-cron_job-get_cronjob_status)
- [OPTIONS `genius cron_job get_cronjob_status`](#options-genius-cron_job-get_cronjob_status)
- [COMMAND `genius plugins`](#command-genius-plugins)
- [COMMAND `genius list`](#command-genius-list)
- [OPTIONS `genius list`](#options-genius-list)

# NAME

genius

# SYNOPSIS

**genius** [-h]
{TestSpoutCtlSpout,TestBoltCtlBolt,rise,docker,pod,deployment,service,job,cron_job,plugins,list}
\...

# DESCRIPTION

Geniusrise

# POSITIONAL ARGUMENTS

**genius** _TestSpoutCtlSpout_: Manage spout TestSpoutCtlSpout.

**genius** _TestBoltCtlBolt_: Manage bolt TestBoltCtlBolt.

**genius** _rise_: Manage spouts and bolts with a YAML file.

**genius** _docker_: Package this application into a Docker image.

**genius** _pod_: Manage spouts and bolts as kubernetes pod

**genius** _deployment_: Manage spouts and bolts as kubernetes deployment

**genius** _service_: Manage spouts and bolts as kubernetes service

**genius** _job_: Manage spouts and bolts as kubernetes job

**genius** _cron_job_: Manage spouts and bolts as kubernetes cron_job

**genius** _plugins_: Print help for all spouts and bolts.

**genius** _list_: List all discovered spouts and bolts.

# COMMAND `genius TestSpoutCtlSpout`

Usage: genius TestSpoutCtlSpout [-h] {rise,deploy,help} \...

# POSITIONAL ARGUMENTS _`genius TestSpoutCtlSpout`_

**genius TestSpoutCtlSpout** _rise_: Run a spout locally.

**genius TestSpoutCtlSpout** _deploy_: Run a spout remotely.

**genius TestSpoutCtlSpout** _help_: Print help for the spout.

# COMMAND `genius TestSpoutCtlSpout rise`

Usage: genius TestSpoutCtlSpout rise [-h] [--buffer_size BUFFER_SIZE]
[--output_folder OUTPUT_FOLDER] [--output_kafka_topic OUTPUT_KAFKA_TOPIC]
[--output_kafka_cluster_connection_string
OUTPUT_KAFKA_CLUSTER_CONNECTION_STRING] [--output_s3_bucket OUTPUT_S3_BUCKET]
[--output_s3_folder OUTPUT_S3_FOLDER] [--redis_host REDIS_HOST] [--redis_port
REDIS_PORT] [--redis_db REDIS_DB] [--postgres_host POSTGRES_HOST]
[--postgres_port POSTGRES_PORT] [--postgres_user POSTGRES_USER]
[--postgres_password POSTGRES_PASSWORD] [--postgres_database POSTGRES_DATABASE]
[--postgres_table POSTGRES_TABLE] [--dynamodb_table_name DYNAMODB_TABLE_NAME]
[--dynamodb_region_name DYNAMODB_REGION_NAME] [--prometheus_gateway
PROMETHEUS_GATEWAY] [--args \...] {batch,streaming,stream_to_batch}
{none,redis,postgres,dynamodb,prometheus} method_name

**{batch,streaming,stream_to_batch}**: Choose the type of output data: batch or
streaming.

**{none,redis,postgres,dynamodb,prometheus}**: Select the type of state manager:
none, redis, postgres, or dynamodb.

**method_name**: The name of the method to execute on the spout.

# OPTIONS `genius TestSpoutCtlSpout rise`

**--buffer_size** _BUFFER_SIZE_: Specify the size of the buffer.

**--output_folder** _OUTPUT_FOLDER_: Specify the directory where output files
should be stored temporarily.

**--output_kafka_topic** _OUTPUT_KAFKA_TOPIC_: Kafka output topic for streaming
spouts.

**--output_kafka_cluster_connection_string**
_OUTPUT_KAFKA_CLUSTER_CONNECTION_STRING_: Kafka connection string for streaming
spouts.

**--output_s3_bucket** _OUTPUT_S3_BUCKET_: Provide the name of the S3 bucket for
output storage.

**--output_s3_folder** _OUTPUT_S3_FOLDER_: Indicate the S3 folder for output
storage.

**--redis_host** _REDIS_HOST_: Enter the host address for the Redis server.

**--redis_port** _REDIS_PORT_: Enter the port number for the Redis server.

**--redis_db** _REDIS_DB_: Specify the Redis database to be used.

**--postgres_host** _POSTGRES_HOST_: Enter the host address for the PostgreSQL
server.

**--postgres_port** _POSTGRES_PORT_: Enter the port number for the PostgreSQL
server.

**--postgres_user** _POSTGRES_USER_: Provide the username for the PostgreSQL
server.

**--postgres_password** _POSTGRES_PASSWORD_: Provide the password for the
PostgreSQL server.

**--postgres_database** _POSTGRES_DATABASE_: Specify the PostgreSQL database to
be used.

**--postgres_table** _POSTGRES_TABLE_: Specify the PostgreSQL table to be used.

**--dynamodb_table_name** _DYNAMODB_TABLE_NAME_: Provide the name of the
DynamoDB table.

**--dynamodb_region_name** _DYNAMODB_REGION_NAME_: Specify the AWS region for
DynamoDB.

**--prometheus_gateway** _PROMETHEUS_GATEWAY_: Specify the prometheus gateway
URL.

**--args** _\..._: Additional keyword arguments to pass to the spout.

# COMMAND `genius TestSpoutCtlSpout deploy`

Usage: genius TestSpoutCtlSpout deploy [-h] [--buffer_size BUFFER_SIZE]
[--output_folder OUTPUT_FOLDER] [--output_kafka_topic OUTPUT_KAFKA_TOPIC]
[--output_kafka_cluster_connection_string
OUTPUT_KAFKA_CLUSTER_CONNECTION_STRING] [--output_s3_bucket OUTPUT_S3_BUCKET]
[--output_s3_folder OUTPUT_S3_FOLDER] [--redis_host REDIS_HOST] [--redis_port
REDIS_PORT] [--redis_db REDIS_DB] [--postgres_host POSTGRES_HOST]
[--postgres_port POSTGRES_PORT] [--postgres_user POSTGRES_USER]
[--postgres_password POSTGRES_PASSWORD] [--postgres_database POSTGRES_DATABASE]
[--postgres_table POSTGRES_TABLE] [--dynamodb_table_name DYNAMODB_TABLE_NAME]
[--dynamodb_region_name DYNAMODB_REGION_NAME] [--prometheus_gateway
PROMETHEUS_GATEWAY] [--k8s_kind {deployment,service,job,cron_job}] [--k8s_name
K8S_NAME] [--k8s_image K8S_IMAGE] [--k8s_replicas K8S_REPLICAS] [--k8s_env_vars
K8S_ENV_VARS] [--k8s_cpu K8S_CPU] [--k8s_memory K8S_MEMORY] [--k8s_storage
K8S_STORAGE] [--k8s_gpu K8S_GPU] [--k8s_kube_config_path K8S_KUBE_CONFIG_PATH]
[--k8s_api_key K8S_API_KEY] [--k8s_api_host K8S_API_HOST] [--k8s_verify_ssl
K8S_VERIFY_SSL] [--k8s_ssl_ca_cert K8S_SSL_CA_CERT] [--k8s_cluster_name
K8S_CLUSTER_NAME] [--k8s_context_name K8S_CONTEXT_NAME] [--k8s_namespace
K8S_NAMESPACE] [--k8s_labels K8S_LABELS] [--k8s_annotations K8S_ANNOTATIONS]
[--k8s_port K8S_PORT] [--k8s_target_port K8S_TARGET_PORT] [--k8s_schedule
K8S_SCHEDULE] [--args \...] {batch,streaming,stream_to_batch}
{none,redis,postgres,dynamodb,prometheus} {k8s} method_name

**{batch,streaming,stream_to_batch}**: Choose the type of output data: batch or
streaming.

**{none,redis,postgres,dynamodb,prometheus}**: Select the type of state manager:
none, redis, postgres, or dynamodb.

**{k8s}**: Choose the type of deployment.

**method_name**: The name of the method to execute on the spout.

# OPTIONS `genius TestSpoutCtlSpout deploy`

**--buffer_size** _BUFFER_SIZE_: Specify the size of the buffer.

**--output_folder** _OUTPUT_FOLDER_: Specify the directory where output files
should be stored temporarily.

**--output_kafka_topic** _OUTPUT_KAFKA_TOPIC_: Kafka output topic for streaming
spouts.

**--output_kafka_cluster_connection_string**
_OUTPUT_KAFKA_CLUSTER_CONNECTION_STRING_: Kafka connection string for streaming
spouts.

**--output_s3_bucket** _OUTPUT_S3_BUCKET_: Provide the name of the S3 bucket for
output storage.

**--output_s3_folder** _OUTPUT_S3_FOLDER_: Indicate the S3 folder for output
storage.

**--redis_host** _REDIS_HOST_: Enter the host address for the Redis server.

**--redis_port** _REDIS_PORT_: Enter the port number for the Redis server.

**--redis_db** _REDIS_DB_: Specify the Redis database to be used.

**--postgres_host** _POSTGRES_HOST_: Enter the host address for the PostgreSQL
server.

**--postgres_port** _POSTGRES_PORT_: Enter the port number for the PostgreSQL
server.

**--postgres_user** _POSTGRES_USER_: Provide the username for the PostgreSQL
server.

**--postgres_password** _POSTGRES_PASSWORD_: Provide the password for the
PostgreSQL server.

**--postgres_database** _POSTGRES_DATABASE_: Specify the PostgreSQL database to
be used.

**--postgres_table** _POSTGRES_TABLE_: Specify the PostgreSQL table to be used.

**--dynamodb_table_name** _DYNAMODB_TABLE_NAME_: Provide the name of the
DynamoDB table.

**--dynamodb_region_name** _DYNAMODB_REGION_NAME_: Specify the AWS region for
DynamoDB.

**--prometheus_gateway** _PROMETHEUS_GATEWAY_: Specify the prometheus gateway
URL.

**--k8s_kind** _{deployment,service,job,cron_job}_: Choose the type of
kubernetes resource.

**--k8s_name** _K8S_NAME_: Name of the Kubernetes resource.

**--k8s_image** _K8S_IMAGE_: Docker image for the Kubernetes resource.

**--k8s_replicas** _K8S_REPLICAS_: Number of replicas.

**--k8s_env_vars** _K8S_ENV_VARS_: Environment variables as a JSON string.

**--k8s_cpu** _K8S_CPU_: CPU requirements.

**--k8s_memory** _K8S_MEMORY_: Memory requirements.

**--k8s_storage** _K8S_STORAGE_: Storage requirements.

**--k8s_gpu** _K8S_GPU_: GPU requirements.

**--k8s_kube_config_path** _K8S_KUBE_CONFIG_PATH_: Name of the Kubernetes
cluster local config.

**--k8s_api_key** _K8S_API_KEY_: GPU requirements.

**--k8s_api_host** _K8S_API_HOST_: GPU requirements.

**--k8s_verify_ssl** _K8S_VERIFY_SSL_: GPU requirements.

**--k8s_ssl_ca_cert** _K8S_SSL_CA_CERT_: GPU requirements.

**--k8s_cluster_name** _K8S_CLUSTER_NAME_: Name of the Kubernetes cluster.

**--k8s_context_name** _K8S_CONTEXT_NAME_: Name of the kubeconfig context.

**--k8s_namespace** _K8S_NAMESPACE_: Kubernetes namespace.

**--k8s_labels** _K8S_LABELS_: Labels for Kubernetes resources, as a JSON
string.

**--k8s_annotations** _K8S_ANNOTATIONS_: Annotations for Kubernetes resources,
as a JSON string.

**--k8s_port** _K8S_PORT_: Port to run the spout on as a service.

**--k8s_target_port** _K8S_TARGET_PORT_: Port to expose the spout on as a
service.

**--k8s_schedule** _K8S_SCHEDULE_: Schedule to run the spout on as a cron job.

**--args** _\..._: Additional keyword arguments to pass to the spout.

# COMMAND `genius TestSpoutCtlSpout help`

Usage: genius TestSpoutCtlSpout help [-h] method

**method**: The method to execute.

# COMMAND `genius TestBoltCtlBolt`

Usage: genius TestBoltCtlBolt [-h] {rise,deploy,help} \...

# POSITIONAL ARGUMENTS _`genius TestBoltCtlBolt`_

**genius TestBoltCtlBolt** _rise_: Run a bolt locally.

**genius TestBoltCtlBolt** _deploy_: Run a spout remotely.

**genius TestBoltCtlBolt** _help_: Print help for the bolt.

# COMMAND `genius TestBoltCtlBolt rise`

Usage: genius TestBoltCtlBolt rise [-h] [--buffer_size BUFFER_SIZE]
[--input_folder INPUT_FOLDER] [--input_kafka_topic INPUT_KAFKA_TOPIC]
[--input_kafka_cluster_connection_string INPUT_KAFKA_CLUSTER_CONNECTION_STRING]
[--input_kafka_consumer_group_id INPUT_KAFKA_CONSUMER_GROUP_ID]
[--input_s3_bucket INPUT_S3_BUCKET] [--input_s3_folder INPUT_S3_FOLDER]
[--output_folder OUTPUT_FOLDER] [--output_kafka_topic OUTPUT_KAFKA_TOPIC]
[--output_kafka_cluster_connection_string
OUTPUT_KAFKA_CLUSTER_CONNECTION_STRING] [--output_s3_bucket OUTPUT_S3_BUCKET]
[--output_s3_folder OUTPUT_S3_FOLDER] [--redis_host REDIS_HOST] [--redis_port
REDIS_PORT] [--redis_db REDIS_DB] [--postgres_host POSTGRES_HOST]
[--postgres_port POSTGRES_PORT] [--postgres_user POSTGRES_USER]
[--postgres_password POSTGRES_PASSWORD] [--postgres_database POSTGRES_DATABASE]
[--postgres_table POSTGRES_TABLE] [--dynamodb_table_name DYNAMODB_TABLE_NAME]
[--dynamodb_region_name DYNAMODB_REGION_NAME] [--prometheus_gateway
PROMETHEUS_GATEWAY] [--args \...]
{batch,streaming,batch_to_stream,stream_to_batch}
{batch,streaming,stream_to_batch} {none,redis,postgres,dynamodb,prometheus}
method_name

**{batch,streaming,batch_to_stream,stream_to_batch}**: Choose the type of input
data: batch or streaming.

**{batch,streaming,stream_to_batch}**: Choose the type of output data: batch or
streaming.

**{none,redis,postgres,dynamodb,prometheus}**: Select the type of state manager:
none, redis, postgres, or dynamodb.

**method_name**: The name of the method to execute on the bolt.

# OPTIONS `genius TestBoltCtlBolt rise`

**--buffer_size** _BUFFER_SIZE_: Specify the size of the buffer.

**--input_folder** _INPUT_FOLDER_: Specify the directory where output files
should be stored temporarily.

**--input_kafka_topic** _INPUT_KAFKA_TOPIC_: Kafka output topic for streaming
spouts.

**--input_kafka_cluster_connection_string**
_INPUT_KAFKA_CLUSTER_CONNECTION_STRING_: Kafka connection string for streaming
spouts.

**--input_kafka_consumer_group_id** _INPUT_KAFKA_CONSUMER_GROUP_ID_: Kafka
consumer group id to use.

**--input_s3_bucket** _INPUT_S3_BUCKET_: Provide the name of the S3 bucket for
output storage.

**--input_s3_folder** _INPUT_S3_FOLDER_: Indicate the S3 folder for output
storage.

**--output_folder** _OUTPUT_FOLDER_: Specify the directory where output files
should be stored temporarily.

**--output_kafka_topic** _OUTPUT_KAFKA_TOPIC_: Kafka output topic for streaming
spouts.

**--output_kafka_cluster_connection_string**
_OUTPUT_KAFKA_CLUSTER_CONNECTION_STRING_: Kafka connection string for streaming
spouts.

**--output_s3_bucket** _OUTPUT_S3_BUCKET_: Provide the name of the S3 bucket for
output storage.

**--output_s3_folder** _OUTPUT_S3_FOLDER_: Indicate the S3 folder for output
storage.

**--redis_host** _REDIS_HOST_: Enter the host address for the Redis server.

**--redis_port** _REDIS_PORT_: Enter the port number for the Redis server.

**--redis_db** _REDIS_DB_: Specify the Redis database to be used.

**--postgres_host** _POSTGRES_HOST_: Enter the host address for the PostgreSQL
server.

**--postgres_port** _POSTGRES_PORT_: Enter the port number for the PostgreSQL
server.

**--postgres_user** _POSTGRES_USER_: Provide the username for the PostgreSQL
server.

**--postgres_password** _POSTGRES_PASSWORD_: Provide the password for the
PostgreSQL server.

**--postgres_database** _POSTGRES_DATABASE_: Specify the PostgreSQL database to
be used.

**--postgres_table** _POSTGRES_TABLE_: Specify the PostgreSQL table to be used.

**--dynamodb_table_name** _DYNAMODB_TABLE_NAME_: Provide the name of the
DynamoDB table.

**--dynamodb_region_name** _DYNAMODB_REGION_NAME_: Specify the AWS region for
DynamoDB.

**--prometheus_gateway** _PROMETHEUS_GATEWAY_: Specify the prometheus gateway
URL.

**--args** _\..._: Additional keyword arguments to pass to the bolt.

# COMMAND `genius TestBoltCtlBolt deploy`

Usage: genius TestBoltCtlBolt deploy [-h] [--buffer_size BUFFER_SIZE]
[--input_folder INPUT_FOLDER] [--input_kafka_topic INPUT_KAFKA_TOPIC]
[--input_kafka_cluster_connection_string INPUT_KAFKA_CLUSTER_CONNECTION_STRING]
[--input_kafka_consumer_group_id INPUT_KAFKA_CONSUMER_GROUP_ID]
[--input_s3_bucket INPUT_S3_BUCKET] [--input_s3_folder INPUT_S3_FOLDER]
[--output_folder OUTPUT_FOLDER] [--output_kafka_topic OUTPUT_KAFKA_TOPIC]
[--output_kafka_cluster_connection_string
OUTPUT_KAFKA_CLUSTER_CONNECTION_STRING] [--output_s3_bucket OUTPUT_S3_BUCKET]
[--output_s3_folder OUTPUT_S3_FOLDER] [--redis_host REDIS_HOST] [--redis_port
REDIS_PORT] [--redis_db REDIS_DB] [--postgres_host POSTGRES_HOST]
[--postgres_port POSTGRES_PORT] [--postgres_user POSTGRES_USER]
[--postgres_password POSTGRES_PASSWORD] [--postgres_database POSTGRES_DATABASE]
[--postgres_table POSTGRES_TABLE] [--dynamodb_table_name DYNAMODB_TABLE_NAME]
[--dynamodb_region_name DYNAMODB_REGION_NAME] [--prometheus_gateway
PROMETHEUS_GATEWAY] [--k8s_kind {deployment,service,job,cron_job}] [--k8s_name
K8S_NAME] [--k8s_image K8S_IMAGE] [--k8s_replicas K8S_REPLICAS] [--k8s_env_vars
K8S_ENV_VARS] [--k8s_cpu K8S_CPU] [--k8s_memory K8S_MEMORY] [--k8s_storage
K8S_STORAGE] [--k8s_gpu K8S_GPU] [--k8s_kube_config_path K8S_KUBE_CONFIG_PATH]
[--k8s_api_key K8S_API_KEY] [--k8s_api_host K8S_API_HOST] [--k8s_verify_ssl
K8S_VERIFY_SSL] [--k8s_ssl_ca_cert K8S_SSL_CA_CERT] [--k8s_cluster_name
K8S_CLUSTER_NAME] [--k8s_context_name K8S_CONTEXT_NAME] [--k8s_namespace
K8S_NAMESPACE] [--k8s_labels K8S_LABELS] [--k8s_annotations K8S_ANNOTATIONS]
[--k8s_port K8S_PORT] [--k8s_target_port K8S_TARGET_PORT] [--k8s_schedule
K8S_SCHEDULE] [--args \...] {batch,streaming,stream_to_batch}
{none,redis,postgres,dynamodb,prometheus} {k8s} method_name

**{batch,streaming,stream_to_batch}**: Choose the type of output data: batch or
streaming.

**{none,redis,postgres,dynamodb,prometheus}**: Select the type of state manager:
none, redis, postgres, or dynamodb.

**{k8s}**: Choose the type of deployment.

**method_name**: The name of the method to execute on the spout.

# OPTIONS `genius TestBoltCtlBolt deploy`

**--buffer_size** _BUFFER_SIZE_: Specify the size of the buffer.

**--input_folder** _INPUT_FOLDER_: Specify the directory where output files
should be stored temporarily.

**--input_kafka_topic** _INPUT_KAFKA_TOPIC_: Kafka output topic for streaming
spouts.

**--input_kafka_cluster_connection_string**
_INPUT_KAFKA_CLUSTER_CONNECTION_STRING_: Kafka connection string for streaming
spouts.

**--input_kafka_consumer_group_id** _INPUT_KAFKA_CONSUMER_GROUP_ID_: Kafka
consumer group id to use.

**--input_s3_bucket** _INPUT_S3_BUCKET_: Provide the name of the S3 bucket for
output storage.

**--input_s3_folder** _INPUT_S3_FOLDER_: Indicate the S3 folder for output
storage.

**--output_folder** _OUTPUT_FOLDER_: Specify the directory where output files
should be stored temporarily.

**--output_kafka_topic** _OUTPUT_KAFKA_TOPIC_: Kafka output topic for streaming
spouts.

**--output_kafka_cluster_connection_string**
_OUTPUT_KAFKA_CLUSTER_CONNECTION_STRING_: Kafka connection string for streaming
spouts.

**--output_s3_bucket** _OUTPUT_S3_BUCKET_: Provide the name of the S3 bucket for
output storage.

**--output_s3_folder** _OUTPUT_S3_FOLDER_: Indicate the S3 folder for output
storage.

**--redis_host** _REDIS_HOST_: Enter the host address for the Redis server.

**--redis_port** _REDIS_PORT_: Enter the port number for the Redis server.

**--redis_db** _REDIS_DB_: Specify the Redis database to be used.

**--postgres_host** _POSTGRES_HOST_: Enter the host address for the PostgreSQL
server.

**--postgres_port** _POSTGRES_PORT_: Enter the port number for the PostgreSQL
server.

**--postgres_user** _POSTGRES_USER_: Provide the username for the PostgreSQL
server.

**--postgres_password** _POSTGRES_PASSWORD_: Provide the password for the
PostgreSQL server.

**--postgres_database** _POSTGRES_DATABASE_: Specify the PostgreSQL database to
be used.

**--postgres_table** _POSTGRES_TABLE_: Specify the PostgreSQL table to be used.

**--dynamodb_table_name** _DYNAMODB_TABLE_NAME_: Provide the name of the
DynamoDB table.

**--dynamodb_region_name** _DYNAMODB_REGION_NAME_: Specify the AWS region for
DynamoDB.

**--prometheus_gateway** _PROMETHEUS_GATEWAY_: Specify the prometheus gateway
URL.

**--k8s_kind** _{deployment,service,job,cron_job}_: Choose the type of
kubernetes resource.

**--k8s_name** _K8S_NAME_: Name of the Kubernetes resource.

**--k8s_image** _K8S_IMAGE_: Docker image for the Kubernetes resource.

**--k8s_replicas** _K8S_REPLICAS_: Number of replicas.

**--k8s_env_vars** _K8S_ENV_VARS_: Environment variables as a JSON string.

**--k8s_cpu** _K8S_CPU_: CPU requirements.

**--k8s_memory** _K8S_MEMORY_: Memory requirements.

**--k8s_storage** _K8S_STORAGE_: Storage requirements.

**--k8s_gpu** _K8S_GPU_: GPU requirements.

**--k8s_kube_config_path** _K8S_KUBE_CONFIG_PATH_: Name of the Kubernetes
cluster local config.

**--k8s_api_key** _K8S_API_KEY_: GPU requirements.

**--k8s_api_host** _K8S_API_HOST_: GPU requirements.

**--k8s_verify_ssl** _K8S_VERIFY_SSL_: GPU requirements.

**--k8s_ssl_ca_cert** _K8S_SSL_CA_CERT_: GPU requirements.

**--k8s_cluster_name** _K8S_CLUSTER_NAME_: Name of the Kubernetes cluster.

**--k8s_context_name** _K8S_CONTEXT_NAME_: Name of the kubeconfig context.

**--k8s_namespace** _K8S_NAMESPACE_: Kubernetes namespace.

**--k8s_labels** _K8S_LABELS_: Labels for Kubernetes resources, as a JSON
string.

**--k8s_annotations** _K8S_ANNOTATIONS_: Annotations for Kubernetes resources,
as a JSON string.

**--k8s_port** _K8S_PORT_: Port to run the spout on as a service.

**--k8s_target_port** _K8S_TARGET_PORT_: Port to expose the spout on as a
service.

**--k8s_schedule** _K8S_SCHEDULE_: Schedule to run the spout on as a cron job.

**--args** _\..._: Additional keyword arguments to pass to the spout.

# COMMAND `genius TestBoltCtlBolt help`

Usage: genius TestBoltCtlBolt help [-h] method

**method**: The method to execute.

# COMMAND `genius rise`

Usage: genius rise [-h] [--spout SPOUT] [--bolt BOLT] [--file FILE]

# OPTIONS `genius rise`

**--spout** _SPOUT_: Name of the specific spout to run.

**--bolt** _BOLT_: Name of the specific bolt to run.

**--file** _FILE_: Path of the genius.yml file, default to .

# COMMAND `genius docker`

usage: genius docker [-h] {package} \...

# POSITIONAL ARGUMENTS _`genius docker`_

**genius docker** _package_: Build and upload a Docker image.

# COMMAND `genius docker package`

Usage: genius docker package [-h] [--auth AUTH] [--base_image BASE_IMAGE]
[--workdir WORKDIR] [--local_dir LOCAL_DIR] [--packages [PACKAGES \...]]
[--os_packages [OS_PACKAGES \...]] [--env_vars ENV_VARS] image_name repository

**image_name**: Name of the Docker image.

**repository**: Container repository to upload to.

# OPTIONS `genius docker package`

**--auth** _AUTH_: Authentication credentials as a JSON string.

**--base_image** _BASE_IMAGE_: The base image to use for the Docker container.

**--workdir** _WORKDIR_: The working directory in the Docker container.

**--local_dir** _LOCAL_DIR_: The local directory to copy into the Docker
container.

**--packages** _[PACKAGES \...]_: List of Python packages to install in the
Docker container.

**--os_packages** _[OS_PACKAGES \...]_: List of OS packages to install in the
Docker container.

**--env_vars** _ENV_VARS_: Environment variables to set in the Docker container.

# COMMAND `genius pod`

usage: genius pod [-h] {status,show,describe,logs} \...

# POSITIONAL ARGUMENTS _`genius pod`_

**genius pod** _status_: Get the status of the Kubernetes pod.

**genius pod** _show_: List all pods.

**genius pod** _describe_: Describe a pod.

**genius pod** _logs_: Get the logs of a pod.

# COMMAND `genius pod status`

usage: genius pod status [-h] [--kube_config_path KUBE_CONFIG_PATH]
[--cluster_name CLUSTER_NAME] [--context_name CONTEXT_NAME] [--namespace
NAMESPACE] [--labels LABELS] [--annotations ANNOTATIONS] [--api_key API_KEY]
[--api_host API_HOST] [--verify_ssl VERIFY_SSL] [--ssl_ca_cert SSL_CA_CERT] name

**name**: Name of the Kubernetes pod.

# OPTIONS `genius pod status`

**--kube_config_path** _KUBE_CONFIG_PATH_: Path to the kubeconfig file.

**--cluster_name** _CLUSTER_NAME_: Name of the Kubernetes cluster.

**--context_name** _CONTEXT_NAME_: Name of the kubeconfig context.

**--namespace** _NAMESPACE_: Kubernetes namespace.

**--labels** _LABELS_: Labels for Kubernetes resources, as a JSON string.

**--annotations** _ANNOTATIONS_: Annotations for Kubernetes resources, as a JSON
string.

**--api_key** _API_KEY_: API key for Kubernetes cluster.

**--api_host** _API_HOST_: API host for Kubernetes cluster.

**--verify_ssl** _VERIFY_SSL_: Whether to verify SSL certificates.

**--ssl_ca_cert** _SSL_CA_CERT_: Path to the SSL CA certificate.

# COMMAND `genius pod show`

usage: genius pod show [-h] [--kube_config_path KUBE_CONFIG_PATH]
[--cluster_name CLUSTER_NAME] [--context_name CONTEXT_NAME] [--namespace
NAMESPACE] [--labels LABELS] [--annotations ANNOTATIONS] [--api_key API_KEY]
[--api_host API_HOST] [--verify_ssl VERIFY_SSL] [--ssl_ca_cert SSL_CA_CERT]

# OPTIONS `genius pod show`

**--kube_config_path** _KUBE_CONFIG_PATH_: Path to the kubeconfig file.

**--cluster_name** _CLUSTER_NAME_: Name of the Kubernetes cluster.

**--context_name** _CONTEXT_NAME_: Name of the kubeconfig context.

**--namespace** _NAMESPACE_: Kubernetes namespace.

**--labels** _LABELS_: Labels for Kubernetes resources, as a JSON string.

**--annotations** _ANNOTATIONS_: Annotations for Kubernetes resources, as a JSON
string.

**--api_key** _API_KEY_: API key for Kubernetes cluster.

**--api_host** _API_HOST_: API host for Kubernetes cluster.

**--verify_ssl** _VERIFY_SSL_: Whether to verify SSL certificates.

**--ssl_ca_cert** _SSL_CA_CERT_: Path to the SSL CA certificate.

# COMMAND `genius pod describe`

usage: genius pod describe [-h] [--kube_config_path KUBE_CONFIG_PATH]
[--cluster_name CLUSTER_NAME] [--context_name CONTEXT_NAME] [--namespace
NAMESPACE] [--labels LABELS] [--annotations ANNOTATIONS] [--api_key API_KEY]
[--api_host API_HOST] [--verify_ssl VERIFY_SSL] [--ssl_ca_cert SSL_CA_CERT] name

**name**: Name of the pod.

# OPTIONS `genius pod describe`

**--kube_config_path** _KUBE_CONFIG_PATH_: Path to the kubeconfig file.

**--cluster_name** _CLUSTER_NAME_: Name of the Kubernetes cluster.

**--context_name** _CONTEXT_NAME_: Name of the kubeconfig context.

**--namespace** _NAMESPACE_: Kubernetes namespace.

**--labels** _LABELS_: Labels for Kubernetes resources, as a JSON string.

**--annotations** _ANNOTATIONS_: Annotations for Kubernetes resources, as a JSON
string.

**--api_key** _API_KEY_: API key for Kubernetes cluster.

**--api_host** _API_HOST_: API host for Kubernetes cluster.

**--verify_ssl** _VERIFY_SSL_: Whether to verify SSL certificates.

**--ssl_ca_cert** _SSL_CA_CERT_: Path to the SSL CA certificate.

# COMMAND `genius pod logs`

usage: genius pod logs [-h] [--follow FOLLOW] [--tail TAIL] [--kube_config_path
KUBE_CONFIG_PATH] [--cluster_name CLUSTER_NAME] [--context_name CONTEXT_NAME]
[--namespace NAMESPACE] [--labels LABELS] [--annotations ANNOTATIONS] [--api_key
API_KEY] [--api_host API_HOST] [--verify_ssl VERIFY_SSL] [--ssl_ca_cert
SSL_CA_CERT] name

**name**: Name of the pod.

# OPTIONS `genius pod logs`

**--follow** _FOLLOW_: Whether to follow the logs.

**--tail** _TAIL_: Number of lines to show from the end of the logs.

**--kube_config_path** _KUBE_CONFIG_PATH_: Path to the kubeconfig file.

**--cluster_name** _CLUSTER_NAME_: Name of the Kubernetes cluster.

**--context_name** _CONTEXT_NAME_: Name of the kubeconfig context.

**--namespace** _NAMESPACE_: Kubernetes namespace.

**--labels** _LABELS_: Labels for Kubernetes resources, as a JSON string.

**--annotations** _ANNOTATIONS_: Annotations for Kubernetes resources, as a JSON
string.

**--api_key** _API_KEY_: API key for Kubernetes cluster.

**--api_host** _API_HOST_: API host for Kubernetes cluster.

**--verify_ssl** _VERIFY_SSL_: Whether to verify SSL certificates.

**--ssl_ca_cert** _SSL_CA_CERT_: Path to the SSL CA certificate.

# COMMAND `genius deployment`

usage: genius deployment [-h] {create,scale,describe,show,delete,status} \...

# POSITIONAL ARGUMENTS _`genius deployment`_

**genius deployment** _create_: Create a new deployment.

**genius deployment** _scale_: Scale a deployment.

**genius deployment** _describe_: Describe a deployment.

**genius deployment** _show_: List all deployments.

**genius deployment** _delete_: Delete a deployment.

**genius deployment** _status_: Get the status of a deployment.

# COMMAND `genius deployment create`

usage: genius deployment create [-h] [--replicas REPLICAS] [--env_vars ENV_VARS]
[--cpu CPU] [--memory MEMORY] [--storage STORAGE] [--gpu GPU]
[--kube_config_path KUBE_CONFIG_PATH] [--cluster_name CLUSTER_NAME]
[--context_name CONTEXT_NAME] [--namespace NAMESPACE] [--labels LABELS]
[--annotations ANNOTATIONS] [--api_key API_KEY] [--api_host API_HOST]
[--verify_ssl VERIFY_SSL] [--ssl_ca_cert SSL_CA_CERT] name image command

**name**: Name of the deployment.

**image**: Docker image for the deployment.

**command**: Command to run in the container.

# OPTIONS `genius deployment create`

**--replicas** _REPLICAS_: Number of replicas.

**--env_vars** _ENV_VARS_: Environment variables as a JSON string.

**--cpu** _CPU_: CPU requirements.

**--memory** _MEMORY_: Memory requirements.

**--storage** _STORAGE_: Storage requirements.

**--gpu** _GPU_: GPU requirements.

**--kube_config_path** _KUBE_CONFIG_PATH_: Path to the kubeconfig file.

**--cluster_name** _CLUSTER_NAME_: Name of the Kubernetes cluster.

**--context_name** _CONTEXT_NAME_: Name of the kubeconfig context.

**--namespace** _NAMESPACE_: Kubernetes namespace.

**--labels** _LABELS_: Labels for Kubernetes resources, as a JSON string.

**--annotations** _ANNOTATIONS_: Annotations for Kubernetes resources, as a JSON
string.

**--api_key** _API_KEY_: API key for Kubernetes cluster.

**--api_host** _API_HOST_: API host for Kubernetes cluster.

**--verify_ssl** _VERIFY_SSL_: Whether to verify SSL certificates.

**--ssl_ca_cert** _SSL_CA_CERT_: Path to the SSL CA certificate.

# COMMAND `genius deployment scale`

usage: genius deployment scale [-h] [--kube_config_path KUBE_CONFIG_PATH]
[--cluster_name CLUSTER_NAME] [--context_name CONTEXT_NAME] [--namespace
NAMESPACE] [--labels LABELS] [--annotations ANNOTATIONS] [--api_key API_KEY]
[--api_host API_HOST] [--verify_ssl VERIFY_SSL] [--ssl_ca_cert SSL_CA_CERT] name
replicas

**name**: Name of the deployment.

**replicas**: Number of replicas.

# OPTIONS `genius deployment scale`

**--kube_config_path** _KUBE_CONFIG_PATH_: Path to the kubeconfig file.

**--cluster_name** _CLUSTER_NAME_: Name of the Kubernetes cluster.

**--context_name** _CONTEXT_NAME_: Name of the kubeconfig context.

**--namespace** _NAMESPACE_: Kubernetes namespace.

**--labels** _LABELS_: Labels for Kubernetes resources, as a JSON string.

**--annotations** _ANNOTATIONS_: Annotations for Kubernetes resources, as a JSON
string.

**--api_key** _API_KEY_: API key for Kubernetes cluster.

**--api_host** _API_HOST_: API host for Kubernetes cluster.

**--verify_ssl** _VERIFY_SSL_: Whether to verify SSL certificates.

**--ssl_ca_cert** _SSL_CA_CERT_: Path to the SSL CA certificate.

# COMMAND `genius deployment describe`

usage: genius deployment describe [-h] [--kube_config_path KUBE_CONFIG_PATH]
[--cluster_name CLUSTER_NAME] [--context_name CONTEXT_NAME] [--namespace
NAMESPACE] [--labels LABELS] [--annotations ANNOTATIONS] [--api_key API_KEY]
[--api_host API_HOST] [--verify_ssl VERIFY_SSL] [--ssl_ca_cert SSL_CA_CERT] name

**name**: Name of the deployment.

# OPTIONS `genius deployment describe`

**--kube_config_path** _KUBE_CONFIG_PATH_: Path to the kubeconfig file.

**--cluster_name** _CLUSTER_NAME_: Name of the Kubernetes cluster.

**--context_name** _CONTEXT_NAME_: Name of the kubeconfig context.

**--namespace** _NAMESPACE_: Kubernetes namespace.

**--labels** _LABELS_: Labels for Kubernetes resources, as a JSON string.

**--annotations** _ANNOTATIONS_: Annotations for Kubernetes resources, as a JSON
string.

**--api_key** _API_KEY_: API key for Kubernetes cluster.

**--api_host** _API_HOST_: API host for Kubernetes cluster.

**--verify_ssl** _VERIFY_SSL_: Whether to verify SSL certificates.

**--ssl_ca_cert** _SSL_CA_CERT_: Path to the SSL CA certificate.

# COMMAND `genius deployment show`

usage: genius deployment show [-h] [--kube_config_path KUBE_CONFIG_PATH]
[--cluster_name CLUSTER_NAME] [--context_name CONTEXT_NAME] [--namespace
NAMESPACE] [--labels LABELS] [--annotations ANNOTATIONS] [--api_key API_KEY]
[--api_host API_HOST] [--verify_ssl VERIFY_SSL] [--ssl_ca_cert SSL_CA_CERT]

# OPTIONS `genius deployment show`

**--kube_config_path** _KUBE_CONFIG_PATH_: Path to the kubeconfig file.

**--cluster_name** _CLUSTER_NAME_: Name of the Kubernetes cluster.

**--context_name** _CONTEXT_NAME_: Name of the kubeconfig context.

**--namespace** _NAMESPACE_: Kubernetes namespace.

**--labels** _LABELS_: Labels for Kubernetes resources, as a JSON string.

**--annotations** _ANNOTATIONS_: Annotations for Kubernetes resources, as a JSON
string.

**--api_key** _API_KEY_: API key for Kubernetes cluster.

**--api_host** _API_HOST_: API host for Kubernetes cluster.

**--verify_ssl** _VERIFY_SSL_: Whether to verify SSL certificates.

**--ssl_ca_cert** _SSL_CA_CERT_: Path to the SSL CA certificate.

# COMMAND `genius deployment delete`

usage: genius deployment delete [-h] [--kube_config_path KUBE_CONFIG_PATH]
[--cluster_name CLUSTER_NAME] [--context_name CONTEXT_NAME] [--namespace
NAMESPACE] [--labels LABELS] [--annotations ANNOTATIONS] [--api_key API_KEY]
[--api_host API_HOST] [--verify_ssl VERIFY_SSL] [--ssl_ca_cert SSL_CA_CERT] name

**name**: Name of the deployment.

# OPTIONS `genius deployment delete`

**--kube_config_path** _KUBE_CONFIG_PATH_: Path to the kubeconfig file.

**--cluster_name** _CLUSTER_NAME_: Name of the Kubernetes cluster.

**--context_name** _CONTEXT_NAME_: Name of the kubeconfig context.

**--namespace** _NAMESPACE_: Kubernetes namespace.

**--labels** _LABELS_: Labels for Kubernetes resources, as a JSON string.

**--annotations** _ANNOTATIONS_: Annotations for Kubernetes resources, as a JSON
string.

**--api_key** _API_KEY_: API key for Kubernetes cluster.

**--api_host** _API_HOST_: API host for Kubernetes cluster.

**--verify_ssl** _VERIFY_SSL_: Whether to verify SSL certificates.

**--ssl_ca_cert** _SSL_CA_CERT_: Path to the SSL CA certificate.

# COMMAND `genius deployment status`

usage: genius deployment status [-h] [--kube_config_path KUBE_CONFIG_PATH]
[--cluster_name CLUSTER_NAME] [--context_name CONTEXT_NAME] [--namespace
NAMESPACE] [--labels LABELS] [--annotations ANNOTATIONS] [--api_key API_KEY]
[--api_host API_HOST] [--verify_ssl VERIFY_SSL] [--ssl_ca_cert SSL_CA_CERT] name

**name**: Name of the deployment.

# OPTIONS `genius deployment status`

**--kube_config_path** _KUBE_CONFIG_PATH_: Path to the kubeconfig file.

**--cluster_name** _CLUSTER_NAME_: Name of the Kubernetes cluster.

**--context_name** _CONTEXT_NAME_: Name of the kubeconfig context.

**--namespace** _NAMESPACE_: Kubernetes namespace.

**--labels** _LABELS_: Labels for Kubernetes resources, as a JSON string.

**--annotations** _ANNOTATIONS_: Annotations for Kubernetes resources, as a JSON
string.

**--api_key** _API_KEY_: API key for Kubernetes cluster.

**--api_host** _API_HOST_: API host for Kubernetes cluster.

**--verify_ssl** _VERIFY_SSL_: Whether to verify SSL certificates.

**--ssl_ca_cert** _SSL_CA_CERT_: Path to the SSL CA certificate.

# COMMAND `genius service`

usage: genius service [-h] {create,delete,describe,show} \...

# POSITIONAL ARGUMENTS _`genius service`_

**genius service** _create_: Create a new service.

**genius service** _delete_: Delete a service.

**genius service** _describe_: Describe a service.

**genius service** _show_: List all services.

# COMMAND `genius service create`

usage: genius service create [-h] [--replicas REPLICAS] [--port PORT]
[--target_port TARGET_PORT] [--env_vars ENV_VARS] [--cpu CPU] [--memory MEMORY]
[--storage STORAGE] [--gpu GPU] [--kube_config_path KUBE_CONFIG_PATH]
[--cluster_name CLUSTER_NAME] [--context_name CONTEXT_NAME] [--namespace
NAMESPACE] [--labels LABELS] [--annotations ANNOTATIONS] [--api_key API_KEY]
[--api_host API_HOST] [--verify_ssl VERIFY_SSL] [--ssl_ca_cert SSL_CA_CERT] name
image command

**name**: Name of the service.

**image**: Docker image for the service.

**command**: Command to run in the container.

# OPTIONS `genius service create`

**--replicas** _REPLICAS_: Number of replicas.

**--port** _PORT_: Service port.

**--target_port** _TARGET_PORT_: Container target port.

**--env_vars** _ENV_VARS_: Environment variables as a JSON string.

**--cpu** _CPU_: CPU requirements.

**--memory** _MEMORY_: Memory requirements.

**--storage** _STORAGE_: Storage requirements.

**--gpu** _GPU_: GPU requirements.

**--kube_config_path** _KUBE_CONFIG_PATH_: Path to the kubeconfig file.

**--cluster_name** _CLUSTER_NAME_: Name of the Kubernetes cluster.

**--context_name** _CONTEXT_NAME_: Name of the kubeconfig context.

**--namespace** _NAMESPACE_: Kubernetes namespace.

**--labels** _LABELS_: Labels for Kubernetes resources, as a JSON string.

**--annotations** _ANNOTATIONS_: Annotations for Kubernetes resources, as a JSON
string.

**--api_key** _API_KEY_: API key for Kubernetes cluster.

**--api_host** _API_HOST_: API host for Kubernetes cluster.

**--verify_ssl** _VERIFY_SSL_: Whether to verify SSL certificates.

**--ssl_ca_cert** _SSL_CA_CERT_: Path to the SSL CA certificate.

# COMMAND `genius service delete`

usage: genius service delete [-h] [--kube_config_path KUBE_CONFIG_PATH]
[--cluster_name CLUSTER_NAME] [--context_name CONTEXT_NAME] [--namespace
NAMESPACE] [--labels LABELS] [--annotations ANNOTATIONS] [--api_key API_KEY]
[--api_host API_HOST] [--verify_ssl VERIFY_SSL] [--ssl_ca_cert SSL_CA_CERT] name

**name**: Name of the service.

# OPTIONS `genius service delete`

**--kube_config_path** _KUBE_CONFIG_PATH_: Path to the kubeconfig file.

**--cluster_name** _CLUSTER_NAME_: Name of the Kubernetes cluster.

**--context_name** _CONTEXT_NAME_: Name of the kubeconfig context.

**--namespace** _NAMESPACE_: Kubernetes namespace.

**--labels** _LABELS_: Labels for Kubernetes resources, as a JSON string.

**--annotations** _ANNOTATIONS_: Annotations for Kubernetes resources, as a JSON
string.

**--api_key** _API_KEY_: API key for Kubernetes cluster.

**--api_host** _API_HOST_: API host for Kubernetes cluster.

**--verify_ssl** _VERIFY_SSL_: Whether to verify SSL certificates.

**--ssl_ca_cert** _SSL_CA_CERT_: Path to the SSL CA certificate.

# COMMAND `genius service describe`

usage: genius service describe [-h] [--kube_config_path KUBE_CONFIG_PATH]
[--cluster_name CLUSTER_NAME] [--context_name CONTEXT_NAME] [--namespace
NAMESPACE] [--labels LABELS] [--annotations ANNOTATIONS] [--api_key API_KEY]
[--api_host API_HOST] [--verify_ssl VERIFY_SSL] [--ssl_ca_cert SSL_CA_CERT] name

**name**: Name of the service.

# OPTIONS `genius service describe`

**--kube_config_path** _KUBE_CONFIG_PATH_: Path to the kubeconfig file.

**--cluster_name** _CLUSTER_NAME_: Name of the Kubernetes cluster.

**--context_name** _CONTEXT_NAME_: Name of the kubeconfig context.

**--namespace** _NAMESPACE_: Kubernetes namespace.

**--labels** _LABELS_: Labels for Kubernetes resources, as a JSON string.

**--annotations** _ANNOTATIONS_: Annotations for Kubernetes resources, as a JSON
string.

**--api_key** _API_KEY_: API key for Kubernetes cluster.

**--api_host** _API_HOST_: API host for Kubernetes cluster.

**--verify_ssl** _VERIFY_SSL_: Whether to verify SSL certificates.

**--ssl_ca_cert** _SSL_CA_CERT_: Path to the SSL CA certificate.

# COMMAND `genius service show`

usage: genius service show [-h] [--kube_config_path KUBE_CONFIG_PATH]
[--cluster_name CLUSTER_NAME] [--context_name CONTEXT_NAME] [--namespace
NAMESPACE] [--labels LABELS] [--annotations ANNOTATIONS] [--api_key API_KEY]
[--api_host API_HOST] [--verify_ssl VERIFY_SSL] [--ssl_ca_cert SSL_CA_CERT]

# OPTIONS `genius service show`

**--kube_config_path** _KUBE_CONFIG_PATH_: Path to the kubeconfig file.

**--cluster_name** _CLUSTER_NAME_: Name of the Kubernetes cluster.

**--context_name** _CONTEXT_NAME_: Name of the kubeconfig context.

**--namespace** _NAMESPACE_: Kubernetes namespace.

**--labels** _LABELS_: Labels for Kubernetes resources, as a JSON string.

**--annotations** _ANNOTATIONS_: Annotations for Kubernetes resources, as a JSON
string.

**--api_key** _API_KEY_: API key for Kubernetes cluster.

**--api_host** _API_HOST_: API host for Kubernetes cluster.

**--verify_ssl** _VERIFY_SSL_: Whether to verify SSL certificates.

**--ssl_ca_cert** _SSL_CA_CERT_: Path to the SSL CA certificate.

# COMMAND `genius job`

usage: genius job [-h] {create,delete,status} \...

# POSITIONAL ARGUMENTS _`genius job`_

**genius job** _create_: Create a new job.

**genius job** _delete_: Delete a job.

**genius job** _status_: Get the status of a job.

# COMMAND `genius job create`

usage: genius job create [-h] [--env_vars ENV_VARS] [--cpu CPU] [--memory
MEMORY] [--storage STORAGE] [--gpu GPU] [--kube_config_path KUBE_CONFIG_PATH]
[--cluster_name CLUSTER_NAME] [--context_name CONTEXT_NAME] [--namespace
NAMESPACE] [--labels LABELS] [--annotations ANNOTATIONS] [--api_key API_KEY]
[--api_host API_HOST] [--verify_ssl VERIFY_SSL] [--ssl_ca_cert SSL_CA_CERT] name
image command

**name**: Name of the job.

**image**: Docker image for the job.

**command**: Command to run in the container.

# OPTIONS `genius job create`

**--env_vars** _ENV_VARS_: Environment variables as a JSON string.

**--cpu** _CPU_: CPU requirements.

**--memory** _MEMORY_: Memory requirements.

**--storage** _STORAGE_: Storage requirements.

**--gpu** _GPU_: GPU requirements.

**--kube_config_path** _KUBE_CONFIG_PATH_: Path to the kubeconfig file.

**--cluster_name** _CLUSTER_NAME_: Name of the Kubernetes cluster.

**--context_name** _CONTEXT_NAME_: Name of the kubeconfig context.

**--namespace** _NAMESPACE_: Kubernetes namespace.

**--labels** _LABELS_: Labels for Kubernetes resources, as a JSON string.

**--annotations** _ANNOTATIONS_: Annotations for Kubernetes resources, as a JSON
string.

**--api_key** _API_KEY_: API key for Kubernetes cluster.

**--api_host** _API_HOST_: API host for Kubernetes cluster.

**--verify_ssl** _VERIFY_SSL_: Whether to verify SSL certificates.

**--ssl_ca_cert** _SSL_CA_CERT_: Path to the SSL CA certificate.

# COMMAND `genius job delete`

usage: genius job delete [-h] [--kube_config_path KUBE_CONFIG_PATH]
[--cluster_name CLUSTER_NAME] [--context_name CONTEXT_NAME] [--namespace
NAMESPACE] [--labels LABELS] [--annotations ANNOTATIONS] [--api_key API_KEY]
[--api_host API_HOST] [--verify_ssl VERIFY_SSL] [--ssl_ca_cert SSL_CA_CERT] name

**name**: Name of the job.

# OPTIONS `genius job delete`

**--kube_config_path** _KUBE_CONFIG_PATH_: Path to the kubeconfig file.

**--cluster_name** _CLUSTER_NAME_: Name of the Kubernetes cluster.

**--context_name** _CONTEXT_NAME_: Name of the kubeconfig context.

**--namespace** _NAMESPACE_: Kubernetes namespace.

**--labels** _LABELS_: Labels for Kubernetes resources, as a JSON string.

**--annotations** _ANNOTATIONS_: Annotations for Kubernetes resources, as a JSON
string.

**--api_key** _API_KEY_: API key for Kubernetes cluster.

**--api_host** _API_HOST_: API host for Kubernetes cluster.

**--verify_ssl** _VERIFY_SSL_: Whether to verify SSL certificates.

**--ssl_ca_cert** _SSL_CA_CERT_: Path to the SSL CA certificate.

# COMMAND `genius job status`

usage: genius job status [-h] [--kube_config_path KUBE_CONFIG_PATH]
[--cluster_name CLUSTER_NAME] [--context_name CONTEXT_NAME] [--namespace
NAMESPACE] [--labels LABELS] [--annotations ANNOTATIONS] [--api_key API_KEY]
[--api_host API_HOST] [--verify_ssl VERIFY_SSL] [--ssl_ca_cert SSL_CA_CERT] name

**name**: Name of the job.

# OPTIONS `genius job status`

**--kube_config_path** _KUBE_CONFIG_PATH_: Path to the kubeconfig file.

**--cluster_name** _CLUSTER_NAME_: Name of the Kubernetes cluster.

**--context_name** _CONTEXT_NAME_: Name of the kubeconfig context.

**--namespace** _NAMESPACE_: Kubernetes namespace.

**--labels** _LABELS_: Labels for Kubernetes resources, as a JSON string.

**--annotations** _ANNOTATIONS_: Annotations for Kubernetes resources, as a JSON
string.

**--api_key** _API_KEY_: API key for Kubernetes cluster.

**--api_host** _API_HOST_: API host for Kubernetes cluster.

**--verify_ssl** _VERIFY_SSL_: Whether to verify SSL certificates.

**--ssl_ca_cert** _SSL_CA_CERT_: Path to the SSL CA certificate.

# COMMAND `genius cron_job`

usage: genius cron_job [-h] {create_cronjob,delete_cronjob,get_cronjob_status}
\...

# POSITIONAL ARGUMENTS _`genius cron_job`_

**genius cron_job** _create_cronjob_: Create a new cronjob.

**genius cron_job** _delete_cronjob_: Delete a cronjob.

**genius cron_job** _get_cronjob_status_: Get the status of a cronjob.

# COMMAND `genius cron_job create_cronjob`

usage: genius cron_job create_cronjob [-h] [--env_vars ENV_VARS] [--cpu CPU]
[--memory MEMORY] [--storage STORAGE] [--gpu GPU] [--kube_config_path
KUBE_CONFIG_PATH] [--cluster_name CLUSTER_NAME] [--context_name CONTEXT_NAME]
[--namespace NAMESPACE] [--labels LABELS] [--annotations ANNOTATIONS] [--api_key
API_KEY] [--api_host API_HOST] [--verify_ssl VERIFY_SSL] [--ssl_ca_cert
SSL_CA_CERT] name image command schedule

**name**: Name of the cronjob.

**image**: Docker image for the cronjob.

**command**: Command to run in the container.

**schedule**: Cron schedule.

# OPTIONS `genius cron_job create_cronjob`

**--env_vars** _ENV_VARS_: Environment variables as a JSON string.

**--cpu** _CPU_: CPU requirements.

**--memory** _MEMORY_: Memory requirements.

**--storage** _STORAGE_: Storage requirements.

**--gpu** _GPU_: GPU requirements.

**--kube_config_path** _KUBE_CONFIG_PATH_: Path to the kubeconfig file.

**--cluster_name** _CLUSTER_NAME_: Name of the Kubernetes cluster.

**--context_name** _CONTEXT_NAME_: Name of the kubeconfig context.

**--namespace** _NAMESPACE_: Kubernetes namespace.

**--labels** _LABELS_: Labels for Kubernetes resources, as a JSON string.

**--annotations** _ANNOTATIONS_: Annotations for Kubernetes resources, as a JSON
string.

**--api_key** _API_KEY_: API key for Kubernetes cluster.

**--api_host** _API_HOST_: API host for Kubernetes cluster.

**--verify_ssl** _VERIFY_SSL_: Whether to verify SSL certificates.

**--ssl_ca_cert** _SSL_CA_CERT_: Path to the SSL CA certificate.

# COMMAND `genius cron_job delete_cronjob`

usage: genius cron_job delete_cronjob [-h] [--kube_config_path KUBE_CONFIG_PATH]
[--cluster_name CLUSTER_NAME] [--context_name CONTEXT_NAME] [--namespace
NAMESPACE] [--labels LABELS] [--annotations ANNOTATIONS] [--api_key API_KEY]
[--api_host API_HOST] [--verify_ssl VERIFY_SSL] [--ssl_ca_cert SSL_CA_CERT] name

**name**: Name of the cronjob.

# OPTIONS `genius cron_job delete_cronjob`

**--kube_config_path** _KUBE_CONFIG_PATH_: Path to the kubeconfig file.

**--cluster_name** _CLUSTER_NAME_: Name of the Kubernetes cluster.

**--context_name** _CONTEXT_NAME_: Name of the kubeconfig context.

**--namespace** _NAMESPACE_: Kubernetes namespace.

**--labels** _LABELS_: Labels for Kubernetes resources, as a JSON string.

**--annotations** _ANNOTATIONS_: Annotations for Kubernetes resources, as a JSON
string.

**--api_key** _API_KEY_: API key for Kubernetes cluster.

**--api_host** _API_HOST_: API host for Kubernetes cluster.

**--verify_ssl** _VERIFY_SSL_: Whether to verify SSL certificates.

**--ssl_ca_cert** _SSL_CA_CERT_: Path to the SSL CA certificate.

# COMMAND `genius cron_job get_cronjob_status`

usage: genius cron_job get_cronjob_status [-h] [--kube_config_path
KUBE_CONFIG_PATH] [--cluster_name CLUSTER_NAME] [--context_name CONTEXT_NAME]
[--namespace NAMESPACE] [--labels LABELS] [--annotations ANNOTATIONS] [--api_key
API_KEY] [--api_host API_HOST] [--verify_ssl VERIFY_SSL] [--ssl_ca_cert
SSL_CA_CERT] name

**name**: Name of the cronjob.

# OPTIONS `genius cron_job get_cronjob_status`

**--kube_config_path** _KUBE_CONFIG_PATH_: Path to the kubeconfig file.

**--cluster_name** _CLUSTER_NAME_: Name of the Kubernetes cluster.

**--context_name** _CONTEXT_NAME_: Name of the kubeconfig context.

**--namespace** _NAMESPACE_: Kubernetes namespace.

**--labels** _LABELS_: Labels for Kubernetes resources, as a JSON string.

**--annotations** _ANNOTATIONS_: Annotations for Kubernetes resources, as a JSON
string.

**--api_key** _API_KEY_: API key for Kubernetes cluster.

**--api_host** _API_HOST_: API host for Kubernetes cluster.

**--verify_ssl** _VERIFY_SSL_: Whether to verify SSL certificates.

**--ssl_ca_cert** _SSL_CA_CERT_: Path to the SSL CA certificate.

# COMMAND `genius plugins`

Usage: genius plugins [-h] [spout_or_bolt]

**spout_or_bolt**: The spout or bolt to print help for.

# COMMAND `genius list`

Usage: genius list [-h] [--verbose]

# OPTIONS `genius list`

**--verbose**: Print verbose output.
