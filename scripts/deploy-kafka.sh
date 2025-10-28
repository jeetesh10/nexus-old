#!/usr/bin/env bash
set -euo pipefail

# Deploy Strimzi Kafka in a 'kafka' namespace for development.
# Requires kubectl configured to target your cluster.

NAMESPACE="kafka"

echo "[deploy-kafka] Creating namespace ${NAMESPACE} (if not exists)"
kubectl get namespace ${NAMESPACE} >/dev/null 2>&1 || kubectl create namespace ${NAMESPACE}

echo "[deploy-kafka] Installing Strimzi operator CRDs and deployment"
kubectl apply -f "https://strimzi.io/install/latest?namespace=${NAMESPACE}" -n ${NAMESPACE}

echo "[deploy-kafka] Applying Kafka cluster and topic"
kubectl apply -f iac/kubernetes/kafka/kafka-cluster.yaml -n ${NAMESPACE}
kubectl apply -f iac/kubernetes/kafka/kafka-topic.yaml -n ${NAMESPACE}

cat <<EOF

Strimzi Kafka deployed.

- Pods:
  kubectl get pods -n ${NAMESPACE}

- Kafka bootstrap:
  my-cluster-kafka-bootstrap.${NAMESPACE}:9092

- Example topic:
  kafkatopic/events in namespace ${NAMESPACE}

- To delete:
  kubectl delete -f iac/kubernetes/kafka/kafka-topic.yaml -n ${NAMESPACE}
  kubectl delete -f iac/kubernetes/kafka/kafka-cluster.yaml -n ${NAMESPACE}
  kubectl delete -f "https://strimzi.io/install/latest?namespace=${NAMESPACE}" -n ${NAMESPACE}
  kubectl delete namespace ${NAMESPACE}

EOF
