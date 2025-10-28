Kafka on Kubernetes (Strimzi)

This folder contains manifests to deploy Apache Kafka using the Strimzi operator. We are choosing Strimzi to avoid recent Bitnami licensing changes and keep the stack free/open-source by default. You can switch later if desired.

Includes:
- Namespace-scoped Strimzi operator install
- A minimal single-broker Kafka cluster for dev
- A Kafka topic example

Quick usage

1) Install the Strimzi operator (cluster-scoped CRDs):
   kubectl create namespace kafka
   kubectl apply -f https://strimzi.io/install/latest?namespace=kafka -n kafka

2) Apply the dev Kafka cluster and topic:
   kubectl apply -f kafka-cluster.yaml -n kafka
   kubectl apply -f kafka-topic.yaml -n kafka

3) Verify:
   kubectl get pods -n kafka
   kubectl get kafka.kafka.strimzi.io -n kafka
   kubectl get kafkatopics.kafka.strimzi.io -n kafka

Notes
- This is a minimal dev setup (1 broker, ephemeral storage). For staging/prod, use 3 replicas and persistent volumes.
- Clients inside the cluster should use the bootstrap service name: my-cluster-kafka-bootstrap.kafka:9092
- Consider adding a Kafka Exporter and dashboards later.
