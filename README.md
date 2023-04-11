# Graph Enabled Kubernetes Infra Ops

This is a follow-up blog of [Graph Enabled Infra Ops](https://siwei.io/graph-enabled-infra-ops/), which was a demo of how to use NebulaGraph to help OpenStack Infra Ops. In this blog, we will explore how to use NebulaGraph to help Kubernetes Infra Ops.

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
kubectl apply -f https://github.com/MrSupiri/kube-ebpf/raw/main/deployment.yaml
kubectl apply -f https://github.com/MrSupiri/kube-ebpf/raw/main/prometheus-deployment.yaml
```

## Pull data from Kubernetes Cluster

1. get resources and save to files

Get resources from Kubernetes cluster.

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
kubectl get nodes -o json > nodes.json
kubectl get crds --all-namespaces -o json > crds.json
crd_names=$(jq -r '.items[].metadata.name' crds.json)
mkdir -p custom_resources
for crd_name in $crd_names; do
  kubectl get $crd_name --all-namespaces -o json > custom_resources/$crd_name.json
done
```

Get resources with eBPF.

```bash
minikube ssh -- sudo apt update
minikube ssh -- sudo apt install linux-headers-5.4.0-146-generic
minikube ssh

# Install bcc from source following https://github.com/iovisor/bcc/blob/master/INSTALL.md#ubuntu---source
apt install zip
export PATH="/usr/share/bcc/tools/:/usr/share/bcc/tools/old/:$PATH"
# replace python to python3 for /usr/share/bcc/tools/tcptracer
grep python3 /usr/share/bcc/tools/tcptracer || sed -i 's/python/python3/g' /usr/share/bcc/tools/tcptracer
/usr/share/bcc/tools/tcptracer > tcptracer_output.txt
exit

# copy tcptracer_output.txt to local
minikube ssh -- cat tcptracer_output.txt > tcptracer_output.txt
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

<img width="2032" alt="k8s-graph-nebulagraph" src="https://user-images.githubusercontent.com/1651790/230852511-fbead10c-0b27-411b-8eac-72f455710ad3.png">


## Get insights from the K8s Graph

Refer to [k8s.ipynb](https://github.com/wey-gu/k8s-graph/blob/main/k8s.ipynb) for more details.
