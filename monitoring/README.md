# Monitoring Stack

## Overview

This project uses the Prometheus monitoring stack and Grafana dashboards to monitor the Secure Banking Transaction Portal deployed on Kubernetes.

Monitoring components are deployed using the kube-prometheus-stack Helm chart.

---

## Components Installed

### Prometheus
- Metrics collection and storage
- Kubernetes cluster monitoring
- Application performance monitoring

### Grafana
- Dashboard visualization
- Prometheus data source integration
- Real-time monitoring dashboards

### Alertmanager
- Alert management
- Notification routing

### Node Exporter
- Node-level metrics collection
- CPU, Memory, Disk and Network monitoring

### kube-state-metrics
- Kubernetes object metrics
- Deployments
- Pods
- Services
- HPA metrics

---

## Kubernetes Namespace

```bash
monitoring
```

---

## Installation

### Add Helm Repository

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts

helm repo update
```

### Install Monitoring Stack

```bash
helm install monitoring prometheus-community/kube-prometheus-stack \
-n monitoring
```

---

## Verify Installation

### Check Pods

```bash
kubectl get pods -n monitoring
```

### Check Services

```bash
kubectl get svc -n monitoring
```

---

## Access Prometheus

### Port Forward

```bash
kubectl port-forward \
-n monitoring \
svc/monitoring-kube-prometheus-prometheus \
9090:9090
```

### URL

```text
http://localhost:9090
```

---

## Access Grafana

### Port Forward

```bash
kubectl port-forward \
-n monitoring \
svc/monitoring-grafana \
3000:80
```

### URL

```text
http://localhost:3000
```

---

## Useful Prometheus Queries

### Verify Targets

```promql
up
```

### Pod Information

```promql
kube_pod_info
```

### Memory Usage

```promql
container_memory_usage_bytes
```

### CPU Usage

```promql
rate(container_cpu_usage_seconds_total[5m])
```

---

## Grafana Dashboards

Recommended Dashboard IDs:

### Kubernetes Cluster Monitoring

```text
315
```

### Kubernetes Views

```text
15757
```

---

## Current Project Architecture

GitHub Repository
        |
        v
GitHub Actions
        |
        v
GHCR Container Registry
        |
        v
Argo CD
        |
        v
Kubernetes Cluster
        |
        +--------------------+
        |                    |
        v                    v
Prometheus            Grafana
        |
        v
Alertmanager

---

## Sprint Progress

### Sprint 1
- Secure Banking Application

### Sprint 2
- Docker Containerization

### Sprint 3
- Kubernetes Deployment
- Service Configuration
- Scaling

### Sprint 4
- Horizontal Pod Autoscaler
- Security Scanning
- SonarQube
- Snyk

### Sprint 5
- GitHub Container Registry (GHCR)
- Argo CD GitOps Deployment
- Prometheus Monitoring
- Grafana Dashboards

---

## Author

Saravanan T H

GitHub:
https://github.com/irish-saravananth

Repository:
https://github.com/irish-saravananth/secure-banking-transaction-portal
