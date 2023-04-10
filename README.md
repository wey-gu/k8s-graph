

## Prepare Environment

1. Install miniKube and create a cluster

> Assuming on a Ubuntu 20.04 server with Docker installed.

```bash
curl -Lo minikube https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
chmod +x minikube
sudo mv minikube /usr/local/bin/
minikube start --vm-driver=none
```

2. Create some resources

- Deploy NebulaGraph with [Nebula-Operator](https://github.com/vesoft-inc/nebula-operator)
- Deploy APISIX following [this blog](https://www.siwei.io/apisix-and-nebulagraph/)
- Deploy other sample resources as follows:

```bash
kubectl apply -f resources/sample.yaml
```

## Pull data from Kubernetes Cluster

1. get resources and save to files

```bash
cd data
kubectl get pods -o json > pods.json
kubectl get services -o json > services.json
kubectl get deployments -o json > deployments.json
kubectl get replicasets -o json > replicasets.json
kubectl get statefulsets -o json > statefulsets.json
kubectl get daemonsets -o json > daemonsets.json
kubectl get persistentvolumeclaims -o json > persistentvolumeclaims.json
kubectl get persistentvolumes -o json > persistentvolumes.json
kubectl get ingresses -o json > ingresses.json
kubectl get configmaps -o json > configmaps.json
kubectl get secrets -o json > secrets.json
kubectl get horizontalpodautoscalers -o json > horizontalpodautoscalers.json
```

2. convert json to csv and .ngql NebulaGraph query file

```bash
cd data
python3 ../utils/pull_k8s_resources.py
```

You will get `relations.csv` and `graph.ngql` in `data` folder.

## Import data to NebulaGraph

1. Prepare the test NebulaGraph cluster

For docker desktop, we could get the NebulaGraph cluster ready with [Docker Extension](https://hub.docker.com/extensions/weygu/nebulagraph-dd-ext), click Install will do the work.

2. Create a graph space from NebulaGraph Studio

```ngql
CREATE SPACE `k8s` (partition_num = 10, replica_factor = 1, vid_type = FIXED_STRING(256));
USE `k8s`;
```

3. Load the `graph.ngql` generated with `pull_k8s_resources.py` to NebulaGraph in Console of NebulaGraph Studio.
