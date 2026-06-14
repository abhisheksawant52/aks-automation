# AKS Automation

End-to-end tooling for provisioning and managing **Azure Kubernetes Service (AKS)** clusters. This repo combines:

- **Terraform** — declarative infrastructure provisioning
- **Python CLI** (`aks_manager.py`) — day-two operations (scale, credentials, list)
- **GitHub Actions** — CI/CD pipeline with plan-on-PR and apply-on-merge
- **Kubernetes manifests** — a sample nginx workload to smoke-test the cluster

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Repository Structure](#repository-structure)
3. [Quick Start](#quick-start)
4. [Authentication](#authentication)
5. [Terraform Usage](#terraform-usage)
6. [Python CLI Usage](#python-cli-usage)
7. [GitHub Actions Setup](#github-actions-setup)
8. [Deploying the Sample App](#deploying-the-sample-app)
9. [Cleanup](#cleanup)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

| Tool | Minimum Version | Install |
|------|----------------|---------|
| Azure CLI | 2.60+ | [docs.microsoft.com](https://learn.microsoft.com/cli/azure/install-azure-cli) |
| Terraform | 1.5+ | [developer.hashicorp.com](https://developer.hashicorp.com/terraform/install) |
| Python | 3.11+ | [python.org](https://www.python.org/downloads/) |
| kubectl | 1.29+ | [kubernetes.io](https://kubernetes.io/docs/tasks/tools/) |

An Azure subscription with sufficient quota for the chosen VM size and node count is also required.

---

## Repository Structure

```
aks-automation/
├── .github/
│   └── workflows/
│       └── aks-deploy.yml      # CI/CD pipeline
├── ansible/                    # (reserved for configuration management)
├── kubernetes/
│   └── deployment.yaml         # Sample nginx app + service + HPA
├── src/
│   ├── aks_manager.py          # Python CLI tool
│   └── requirements.txt        # Pinned Python dependencies
├── terraform/
│   ├── main.tf                 # Provider + AKS resources
│   ├── variables.tf            # All input variables with defaults
│   └── outputs.tf              # Cluster ID, kubeconfig, host, certs
└── README.md
```

---

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/abhisheksawant52/aks-automation.git
cd aks-automation

# 2. Authenticate with Azure
az login
az account set --subscription "<YOUR_SUBSCRIPTION_ID>"
export AZURE_SUBSCRIPTION_ID=$(az account show --query id -o tsv)

# 3. Provision the cluster with Terraform
cd terraform
terraform init
terraform apply -var="resource_group_name=my-rg" -var="cluster_name=my-cluster"

# 4. Get credentials
cd ..
pip install -r src/requirements.txt
python src/aks_manager.py get-credentials --resource-group my-rg --cluster-name my-cluster

# 5. Deploy sample app
kubectl apply -f kubernetes/deployment.yaml

# 6. Get the external IP
kubectl get svc nginx-service -n sample-app --watch
```

---

## Authentication

All tools rely on **DefaultAzureCredential**, which tries the following sources in order:

1. Environment variables (`AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`)
2. Azure CLI (`az login`)
3. Managed Identity (when running in Azure)

For local development, `az login` is the simplest option.

For CI/CD and Terraform, set the following environment variables (or use the GitHub secrets described below):

```bash
export AZURE_SUBSCRIPTION_ID="<subscription-id>"
export ARM_CLIENT_ID="<service-principal-client-id>"
export ARM_CLIENT_SECRET="<service-principal-client-secret>"
export ARM_TENANT_ID="<tenant-id>"
```

### Creating a Service Principal

```bash
az ad sp create-for-rbac \
  --name "aks-automation-sp" \
  --role Contributor \
  --scopes /subscriptions/<SUBSCRIPTION_ID> \
  --sdk-auth
```

Save the JSON output — you will need it for the `AZURE_CREDENTIALS` secret.

---

## Terraform Usage

### Variables

All variables have sensible defaults. Override them via `-var` flags, a `terraform.tfvars` file, or environment variables prefixed with `TF_VAR_`.

| Variable | Default | Description |
|----------|---------|-------------|
| `resource_group_name` | `aks-automation-rg` | Resource group name |
| `location` | `eastus` | Azure region |
| `cluster_name` | `aks-automation-cluster` | AKS cluster name |
| `kubernetes_version` | latest stable | Kubernetes version |
| `node_count` | `3` | Initial node count |
| `node_size` | `Standard_D2s_v3` | VM SKU |
| `os_disk_size_gb` | `128` | OS disk size |
| `availability_zones` | `["1","2","3"]` | AZ spread |
| `enable_auto_scaling` | `false` | Enable cluster autoscaler |
| `min_node_count` | `1` | Autoscaler minimum |
| `max_node_count` | `10` | Autoscaler maximum |
| `network_plugin` | `kubenet` | `kubenet` or `azure` |
| `log_analytics_workspace_id` | `""` | Azure Monitor workspace ID |
| `tags` | see `variables.tf` | Resource tags |

### Commands

```bash
cd terraform

# Initialise providers and backend
terraform init

# Preview changes
terraform plan \
  -var="resource_group_name=my-rg" \
  -var="cluster_name=my-cluster" \
  -var="location=eastus" \
  -var="node_count=3"

# Apply
terraform apply \
  -var="resource_group_name=my-rg" \
  -var="cluster_name=my-cluster"

# Read outputs
terraform output cluster_id
terraform output -raw kube_config   # returns the raw kubeconfig YAML

# Destroy
terraform destroy \
  -var="resource_group_name=my-rg" \
  -var="cluster_name=my-cluster"
```

### Using a tfvars file

Create `terraform/terraform.tfvars`:

```hcl
resource_group_name = "my-rg"
location            = "westeurope"
cluster_name        = "prod-cluster"
node_count          = 5
node_size           = "Standard_D4s_v3"
kubernetes_version  = "1.29.0"
enable_auto_scaling = true
min_node_count      = 3
max_node_count      = 20
tags = {
  project     = "aks-automation"
  environment = "production"
  owner       = "platform-team"
}
```

Then run `terraform apply` without extra `-var` flags.

---

## Python CLI Usage

### Installation

```bash
pip install -r src/requirements.txt
```

Set the required environment variable:

```bash
export AZURE_SUBSCRIPTION_ID="<your-subscription-id>"
```

Optionally, create `src/.env`:

```dotenv
AZURE_SUBSCRIPTION_ID=<your-subscription-id>
AKS_RESOURCE_GROUP=my-rg
AKS_CLUSTER_NAME=my-cluster
```

### Commands

#### `create-cluster`

Create a new AKS cluster (creates the resource group if it does not exist).

```bash
python src/aks_manager.py create-cluster \
  --resource-group my-rg \
  --cluster-name my-cluster \
  --location eastus \
  --node-count 3 \
  --node-size Standard_D2s_v3 \
  --kubernetes-version 1.29.0
```

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--resource-group` / `-g` | ✅ | — | Resource group name |
| `--cluster-name` / `-n` | ✅ | — | Cluster name |
| `--location` / `-l` | | `eastus` | Azure region |
| `--node-count` | | `3` | Number of nodes (1–100) |
| `--node-size` | | `Standard_D2s_v3` | VM SKU |
| `--kubernetes-version` | | latest | Kubernetes version |
| `--dns-prefix` | | cluster name | DNS prefix for FQDN |

---

#### `delete-cluster`

Delete an AKS cluster (prompts for confirmation unless `--yes` is passed).

```bash
python src/aks_manager.py delete-cluster \
  --resource-group my-rg \
  --cluster-name my-cluster \
  --yes
```

---

#### `get-credentials`

Fetch the kubeconfig and merge it into `~/.kube/config`.

```bash
# Merge into ~/.kube/config (default)
python src/aks_manager.py get-credentials \
  --resource-group my-rg \
  --cluster-name my-cluster

# Write to a custom path
python src/aks_manager.py get-credentials \
  --resource-group my-rg \
  --cluster-name my-cluster \
  --output-file ./my-cluster.yaml

# Fetch admin credentials
python src/aks_manager.py get-credentials \
  --resource-group my-rg \
  --cluster-name my-cluster \
  --admin
```

---

#### `list-clusters`

List all AKS clusters in the subscription.

```bash
# Table output (default)
python src/aks_manager.py list-clusters

# Filter by resource group
python src/aks_manager.py list-clusters --resource-group my-rg

# JSON output
python src/aks_manager.py list-clusters --output json
```

---

#### `scale-nodepool`

Scale a node pool to a given count.

```bash
python src/aks_manager.py scale-nodepool \
  --resource-group my-rg \
  --cluster-name my-cluster \
  --nodepool-name nodepool1 \
  --node-count 5
```

---

### Help

Every command supports `--help`:

```bash
python src/aks_manager.py --help
python src/aks_manager.py create-cluster --help
```

---

## GitHub Actions Setup

### Required Secrets

Go to **Settings → Secrets and variables → Actions** in your GitHub repository and add:

| Secret | Description |
|--------|-------------|
| `AZURE_CREDENTIALS` | JSON output of `az ad sp create-for-rbac --sdk-auth` |
| `AZURE_SUBSCRIPTION_ID` | Your Azure subscription ID |
| `ARM_CLIENT_ID` | Service principal client ID |
| `ARM_CLIENT_SECRET` | Service principal client secret |
| `ARM_TENANT_ID` | Azure AD tenant ID |

`AZURE_CREDENTIALS` is a JSON blob that looks like:

```json
{
  "clientId": "...",
  "clientSecret": "...",
  "subscriptionId": "...",
  "tenantId": "...",
  "activeDirectoryEndpointUrl": "https://login.microsoftonline.com",
  "resourceManagerEndpointUrl": "https://management.azure.com/",
  "activeDirectoryGraphResourceId": "https://graph.windows.net/",
  "sqlManagementEndpointUrl": "https://management.core.windows.net:8443/",
  "galleryEndpointUrl": "https://gallery.azure.com/",
  "managementEndpointUrl": "https://management.core.windows.net/"
}
```

### Workflow Behaviour

| Event | Jobs that run |
|-------|--------------|
| Pull request targeting `main` | `terraform-plan` — posts plan as a PR comment |
| Push to `main` | `terraform-apply` — requires `production` environment approval |
| `workflow_dispatch` (plan) | `terraform-plan` |
| `workflow_dispatch` (apply) | `terraform-apply` |
| `workflow_dispatch` (destroy) | `terraform-destroy` |

### Production Environment (optional)

To require a manual approval before `terraform apply` runs:

1. Go to **Settings → Environments → New environment** and name it `production`.
2. Enable **Required reviewers** and add the relevant team or individuals.

---

## Deploying the Sample App

After the cluster is up and kubeconfig is merged:

```bash
# Apply all resources (Namespace, Deployment, ConfigMap, Service, HPA)
kubectl apply -f kubernetes/deployment.yaml

# Watch the pods come up
kubectl get pods -n sample-app --watch

# Get the LoadBalancer external IP (may take 1–3 minutes to assign)
kubectl get svc nginx-service -n sample-app

# Open in browser once EXTERNAL-IP is assigned
curl http://<EXTERNAL-IP>
```

Expected output: an HTML page reading "🎉 AKS Cluster is Live!"

### Scaling manually

```bash
# Via kubectl
kubectl scale deployment nginx-deployment -n sample-app --replicas=4

# Via Python CLI (scales the underlying node pool, not the deployment)
python src/aks_manager.py scale-nodepool \
  --resource-group my-rg \
  --cluster-name my-cluster \
  --node-count 5
```

---

## Cleanup

### Remove Kubernetes resources

```bash
kubectl delete namespace sample-app
```

### Destroy infrastructure (Terraform)

```bash
cd terraform
terraform destroy \
  -var="resource_group_name=my-rg" \
  -var="cluster_name=my-cluster"
```

### Delete resource group entirely (Azure CLI)

```bash
az group delete --name my-rg --yes --no-wait
```

> **Warning:** This deletes the resource group and **all** resources inside it. It cannot be undone.

---

## Troubleshooting

**`AZURE_SUBSCRIPTION_ID` not set**
Export the variable or add it to `src/.env`.

**`az login` token expired**
Run `az login` and re-export `AZURE_SUBSCRIPTION_ID`.

**Terraform: `InsufficientQuota`**
Request a quota increase in the Azure portal for the selected VM SKU and region, or choose a smaller `node_size`.

**`kubectl` not found when running `get-credentials`**
Install kubectl or pass `--output-file` to write the kubeconfig to a custom path and use it manually.

**LoadBalancer stuck in `<pending>`**
Check that the AKS cluster's managed identity has the `Network Contributor` role on the subnet / VNet. On most fresh clusters this resolves automatically within a few minutes.

**GitHub Actions: `The client does not have authorization to perform action`**
Ensure the service principal has at minimum the `Contributor` role on the subscription (or targeted resource group).
