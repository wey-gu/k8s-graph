"""
Get resources:

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
"""

import json
import csv

# Load Kubernetes resources as JSON
with open('pods.json', 'r') as file:
    pods_data = json.load(file)

with open('services.json', 'r') as file:
    services_data = json.load(file)

with open('deployments.json', 'r') as file:
    deployments_data = json.load(file)

with open('replicasets.json', 'r') as file:
    replicasets_data = json.load(file)

with open('statefulsets.json', 'r') as file:
    statefulsets_data = json.load(file)

with open('daemonsets.json', 'r') as file:
    daemonsets_data = json.load(file)

with open('persistentvolumeclaims.json', 'r') as file:
    pvcs_data = json.load(file)

with open('persistentvolumes.json', 'r') as file:
    pvs_data = json.load(file)

with open('ingresses.json', 'r') as file:
    ingresses_data = json.load(file)

with open('configmaps.json', 'r') as file:
    configmaps_data = json.load(file)

with open('secrets.json', 'r') as file:
    secrets_data = json.load(file)

with open('horizontalpodautoscalers.json', 'r') as file:
    hpa_data = json.load(file)

with open('nodes.json', 'r') as file:
    nodes_data = json.load(file)

# Functions to find relations
def get_owner_references(item):
    return item['metadata'].get('ownerReferences', [])

def find_related_pods(controller, controller_data):
    related_pods = []
    for pod in pods_data['items']:
        owner_refs = get_owner_references(pod)
        if any(ref['uid'] == controller['metadata']['uid'] for ref in owner_refs):
            related_pods.append(pod['metadata']['name'])
    return related_pods

def find_related_replicasets(deployment):
    related_replicasets = []
    for replicaset in replicasets_data['items']:
        owner_refs = get_owner_references(replicaset)
        if any(ref['uid'] == deployment['metadata']['uid'] for ref in owner_refs):
            related_replicasets.append(replicaset['metadata']['name'])
    return related_replicasets

def find_related_persistentvolumeclaims(pod):
    related_pvcs = []
    for volume in pod['spec'].get('volumes', []):
        pvc_name = volume.get('persistentVolumeClaim', {}).get('claimName')
        if pvc_name:
            related_pvcs.append(pvc_name)
    return related_pvcs

def find_related_persistentvolumes(pvc):
    for pv in pvs_data['items']:
        if pv['spec']['claimRef']['uid'] == pvc['metadata']['uid']:
            return pv['metadata']['name']
    return None

def find_related_configmaps_and_secrets(pod):
    related_configmaps = set()
    related_secrets = set()

    # Check environment variables
    for container in pod['spec'].get('containers', []):
        for env_var in container.get('env', []):
            if 'configMapKeyRef' in env_var:
                related_configmaps.add(env_var['configMapKeyRef']['name'])
            if 'secretKeyRef' in env_var:
                related_secrets.add(env_var['secretKeyRef']['name'])

    # Check volume mounts
    for volume in pod['spec'].get('volumes', []):
        if 'configMap' in volume:
            related_configmaps.add(volume['configMap']['name'])
        if 'secret' in volume:
            related_secrets.add(volume['secret']['secretName'])

    return list(related_configmaps), list(related_secrets)

def find_related_ingress_services(ingress):
    related_services = []
    for rule in ingress['spec'].get('rules', []):
        for path in rule.get('http', {}).get('paths', []):
            related_services.append(path['backend']['service']['name'])
    return related_services

def find_related_hpa_scalable_resource(hpa):
    scalable_resource = hpa['spec']['scaleTargetRef']
    return scalable_resource['kind'], scalable_resource['name']

# Process relations
relations = []

# Service to Pod relations
for service in services_data['items']:
    selector = service['spec'].get('selector', {})
    if not selector:
        continue

    related_pods = []
    for pod in pods_data['items']:
        pod_labels = pod['metadata'].get('labels', {})
        if all(key in pod_labels and pod_labels[key] == value for key, value in selector.items()):
            related_pods.append(pod['metadata']['name'])

    relations.append({
        'source': 'Service',
        'source_name': service['metadata']['name'],
        'relationship': 'selects',
        'target': 'Pod',
        'target_name': ', '.join(related_pods)
    })

# Deployment, StatefulSet, DaemonSet and ReplicaSet to Pod relations
for resource_type, resource_data in [('Deployment', deployments_data), ('StatefulSet', statefulsets_data), ('DaemonSet', daemonsets_data), ('ReplicaSet', replicasets_data)]:
    for resource in resource_data['items']:
        related_pods = find_related_pods(resource, resource_data)
        relations.append({
            'source': resource_type,
            'source_name': resource['metadata']['name'],
            'relationship': 'controls',
            'target': 'Pod',
            'target_name': ', '.join(related_pods)
        })

# Deployment to ReplicaSet relations
for deployment in deployments_data['items']:
    related_replicasets = find_related_replicasets(deployment)
    relations.append({
        'source': 'Deployment',
        'source_name': deployment['metadata']['name'],
        'relationship': 'creates',
        'target': 'ReplicaSet',
        'target_name': ', '.join(related_replicasets)
    })

# Pod to PersistentVolumeClaim relations
for pod in pods_data['items']:
    related_pvcs = find_related_persistentvolumeclaims(pod)
    relations.append({
        'source': 'Pod',
        'source_name': pod['metadata']['name'],
        'relationship': 'uses',
        'target': 'PersistentVolumeClaim',
        'target_name': ', '.join(related_pvcs)
    })

# PersistentVolumeClaim to PersistentVolume relations
for pvc in pvcs_data['items']:
    related_pv = find_related_persistentvolumes(pvc)
    if related_pv:
        relations.append({
            'source': 'PersistentVolumeClaim',
            'source_name': pvc['metadata']['name'],
            'relationship': 'binds to',
            'target': 'PersistentVolume',
            'target_name': related_pv
        })

# Ingress to Service relations
for ingress in ingresses_data['items']:
    related_services = find_related_ingress_services(ingress)
    relations.append({
        'source': 'Ingress',
        'source_name': ingress['metadata']['name'],
        'relationship': 'routes to',
        'target': 'Service',
        'target_name': ', '.join(related_services)
    })

# Pod to ConfigMap and Secret relations
for pod in pods_data['items']:
    related_configmaps, related_secrets = find_related_configmaps_and_secrets(pod)

    if related_configmaps:
        relations.append({
            'source': 'Pod',
            'source_name': pod['metadata']['name'],
            'relationship': 'uses',
            'target': 'ConfigMap',
            'target_name': ', '.join(related_configmaps)
        })

    if related_secrets:
        relations.append({
            'source': 'Pod',
            'source_name': pod['metadata']['name'],
            'relationship': 'uses',
            'target': 'Secret',
            'target_name': ', '.join(related_secrets)
        })

# HorizontalPodAutoscaler to scalable resource relations
for hpa in hpa_data['items']:
    resource_kind, resource_name = find_related_hpa_scalable_resource(hpa)
    relations.append({
        'source': 'HorizontalPodAutoscaler',
        'source_name': hpa['metadata']['name'],
        'relationship': 'scales',
        'target': resource_kind,
        'target_name': resource_name
    })

# Node to Pod relations
for node in nodes_data['items']:
    node_name = node['metadata']['name']
    pods_on_node = []
    for pod in pods_data['items']:
        if pod['spec'].get('nodeName') == node_name:
            pod_name = pod['metadata']['name']
            pods_on_node.append(pod_name)

            relations.append({
                'source': 'Node',
                'source_name': node_name,
                'relationship': 'schedules',
                'target': 'Pod',
                'target_name': pod_name
            })

# Filter out relations with empty target_name
filtered_relations = [relation for relation in relations if relation['target_name'].strip()]


# Save relations to CSV
with open('relations.csv', 'w', newline='') as file:
    writer = csv.DictWriter(file, fieldnames=['source', 'source_name', 'relationship', 'target', 'target_name'])
    writer.writeheader()
    
    for relation in filtered_relations:
        target_names = relation['target_name'].split(', ')
        for target_name in target_names:
            writer.writerow({
                'source': relation['source'],
                'source_name': relation['source_name'],
                'relationship': relation['relationship'],
                'target': relation['target'],
                'target_name': target_name
            })


def generate_nebula_statements(csv_file, ngql_file):
    import csv
    
    with open(csv_file, 'r', newline='') as file:
        reader = csv.DictReader(file)
        relations = [row for row in reader]

    tags = set()
    ddl_statements = []
    dml_statements = []

    for relation in relations:
        source_tag = relation['source']
        target_tag = relation['target']

        # Add tags to the set
        tags.add(source_tag)
        tags.add(target_tag)

        source_name = relation['source_name']
        target_name = relation['target_name']
        relationship = relation['relationship']

        # DML statements
        dml_statements.append(f'INSERT VERTEX `{source_tag}`() VALUES "{source_name}":();')
        dml_statements.append(f'INSERT VERTEX `{target_tag}`() VALUES "{target_name}":();')
        dml_statements.append(f'INSERT EDGE `rel`(`verb`) VALUES "{source_name}"->"{target_name}":("{relationship}");')

    # DDL statements
    for tag in tags:
        ddl_statements.append(f'CREATE TAG IF NOT EXISTS `{tag}`();')

    ddl_statements.append('CREATE EDGE IF NOT EXISTS `rel`(`verb` string);')

    # Combine DDL and DML statements and remove duplicates
    unique_ddl_statements = list(set(ddl_statements))
    unique_dml_statements = list(set(dml_statements))

    # Save to file
    with open(ngql_file, 'w') as file:
        file.write('\n'.join(unique_ddl_statements))
        file.write('\n')
        file.write('\n'.join(unique_dml_statements))


generate_nebula_statements('relations.csv', 'graph.ngql')
