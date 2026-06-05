# Setting up a GKE Cluster with Multi-TPU Types (PoC)

This document outlines the steps to set up a Google Kubernetes Engine (GKE) cluster with different types of TPUs and submit a job to it, based on a proof-of-concept (PoC) deployment.

## Goal
Set up a GKE cluster with different types of TPUs and submit a job to it.

## Context and Constraints
- **Multi-Region Limitation**: Currently, our cluster cannot be multi-region.
- **Current Strategy**: For this PoC, we focus on setting up `tpu7-8` (TPU v7 with 8 chips) in `us-central1-c`.
- **Future Plan**: Implement a CLI wrapper that maps the right cluster for the desired TPU type.

## Project & Quota
- **Project ID**: `tpu-prod-env-one-vm`
- **Quota Dashboard**: Monitor current limits and usage on the Quotas & System Limits page.
- **Note**: We are focusing on securing `tpu7-8` quota for this exercise.

---

## Setup Steps

### 1. Environment Variables & Setup

Set up the necessary environment variables before running the commands.

```bash
export PROJECT_ID="tpu-prod-env-one-vm"
export CLUSTER_NAME="vllm-multi-tpu-cluster-regional-poc"
export REGION_NAME="us-central1"
# We target us-central1-c for the node pool, based on the TPU v7 VM location.
export ZONE_V6E="us-central1-c"
export NAMESPACE="default"
export HF_TOKEN="<YOUR_HF_TOKEN>"

# Using existing vllm-network and vllm-subnet
export NETWORK_NAME="vllm-network"
export SUBNET_NAME="vllm-subnet"

/usr/bin/gcloud config set project ${PROJECT_ID}
```

### 2. Network Creation (Using Existing vLLM Network)

Due to quota limits on networks, we use the existing `vllm-network` and its subnet `vllm-subnet` in `us-central1`. We only need to create a proxy-only subnet if using the Gateway API.

```bash
# We skip creating the VPC and Primary Subnet as we use the 'vllm-network'.

# Create proxy-only subnet (Required for the regional Gateway API / Load Balancer)
/usr/bin/gcloud compute networks subnets create ${NETWORK_NAME}-proxy-only \
    --purpose=REGIONAL_MANAGED_PROXY \
    --role=ACTIVE \
    --region=$REGION_NAME \
    --network=$NETWORK_NAME \
    --range=172.16.0.0/26 \
    --project=$PROJECT_ID
```

> [!NOTE]
> Firewall rules allowing `tcp`, `icmp`, and `udp` are required for internal multi-host TPU communication.

### 3. Regional GKE Cluster Creation

Create a regional GKE cluster.

```bash
/usr/bin/gcloud container clusters create $CLUSTER_NAME \
    --location=$REGION_NAME \
    --gateway-api=standard \
    --monitoring=SYSTEM,DCGM \
    --network=${NETWORK_NAME} \
    --subnetwork=${SUBNET_NAME} \
    --addons GcsFuseCsiDriver,\
HttpLoadBalancing,\
HorizontalPodAutoscaling,\
NodeLocalDNS \
    --workload-pool=$PROJECT_ID.svc.id.goog \
    --release-channel=regular
```

> [!NOTE]
> - We use a regional cluster (`--location=$REGION_NAME`) instead of a zonal one to provide high availability and allow attaching node pools in different zones.
> - We omit `--cluster-version` and use `--release-channel=regular` to let GKE pick a supported version and avoid "unsupported version" errors.

### 4. TPU v7 Node Pool Creation

We created both Spot and On-Demand node pools to test capacity.

**Create On-Demand Node Pool:**
```bash
/usr/bin/gcloud container node-pools create nodepool-v7-ondemand \
  --cluster=${CLUSTER_NAME} \
  --location=${REGION_NAME} \
  --node-locations=${ZONE_V6E} \
  --machine-type=tpu7x-standard-4t \
  --project=${PROJECT_ID} \
  --num-nodes=1 \
  --workload-metadata=GKE_METADATA
```

**Create Spot Node Pool:**
```bash
/usr/bin/gcloud container node-pools create nodepool-v7-spot \
  --cluster=${CLUSTER_NAME} \
  --location=${REGION_NAME} \
  --node-locations=${ZONE_V6E} \
  --machine-type=tpu7x-standard-4t \
  --project=${PROJECT_ID} \
  --num-nodes=1 \
  --spot \
  --workload-metadata=GKE_METADATA
```
*Note: The Spot pool successfully provisioned a node, while the On-Demand pool did not get nodes due to capacity constraints.*

> [!IMPORTANT]
> - **Quota vs Capacity**: Even if your quota shows ample limits, On-Demand requests can fail due to physical datacenter stockouts (`RESOURCE_EXHAUSTED`).
> - We are targeting `v7` using the `--spot` flag (or on-demand if quota allows).
> - If this step fails with an `HDB_TOTAL_GB` quota error, it means you have hit your Hyperdisk Balanced limit and must clean up abandoned disks using `/usr/bin/gcloud compute disks delete`.

### 5. Cluster Authentication & Configuration

Get credentials and apply necessary secrets.

```bash
/usr/bin/gcloud container clusters get-credentials $CLUSTER_NAME \
    --location=$REGION_NAME \
    --project=${PROJECT_ID}

# Apply the Hugging Face token required to download gated models
export HF_TOKEN_NAME=${HF_TOKEN_NAME:-llm-d-hf-token}
kubectl create secret generic ${HF_TOKEN_NAME} \
    --from-literal="HF_TOKEN=${HF_TOKEN}" \
    --namespace "${NAMESPACE}" \
    --dry-run=client -o yaml | kubectl apply -f -
```

### 6. Resize the TPU Node Pool

To scale up the cluster, we resized the Spot node pool to 2 nodes (and subsequently scaled it to 8 nodes).

```bash
/usr/bin/gcloud container clusters resize ${CLUSTER_NAME} \
    --node-pool=nodepool-v7-spot \
    --num-nodes=8 \
    --location=${REGION_NAME} \
    --project=${PROJECT_ID}
```

Verify that you have 8 nodes in the spot pool:
```bash
kubectl get nodes
```

---

## vLLM Deployment on TPU v7x

After setting up the `tpu7x` node pool, follow these steps to build the Docker image and deploy vLLM.

### 1. Build Docker Image

We build vLLM from source for TPU, pinning it to a known good commit hash to ensure compatibility with `tpu_inference`.

```bash
# Get the LKG commit hash from tpu-inference repo
export VLLM_COMMIT_HASH="08bfedc152f064d8e84f85c4f42b810e5a564229"
export REGISTRY="us-central1-docker.pkg.dev/tpu-prod-env-one-vm/vllm-tpu-repo"

docker build \
  --build-arg VLLM_COMMIT_HASH=${VLLM_COMMIT_HASH} \
  -t ${REGISTRY}/vllm-tpu:v4 \
  -f /usr/local/google/home/${USER}/projects/tpu-inference/docker/Dockerfile \
  /usr/local/google/home/${USER}/projects/tpu-inference
```

### 2. Push to Artifact Registry
Authenticate Docker and push the image.

```bash
# Authenticate Docker with Artifact Registry
/usr/bin/gcloud auth configure-docker us-central1-docker.pkg.dev

# Push the image
docker push ${REGISTRY}/vllm-tpu:v4
```

### 3. Deploy to GKE
Apply the Kubernetes manifest to deploy vLLM.

```bash
kubectl apply -f vllm-deployment-v7x.yaml
```

### 4. Verification

#### 4.1 Check Pod Status
Verify that the pod is running and ready:
```bash
kubectl get pods -l app=vllm-tpu-v7x
```

#### 4.2 Check Logs
Check the logs to ensure the server has started successfully:
```bash
kubectl logs -l app=vllm-tpu-v7x
```

#### 4.3 Send Request
Port-forward the deployment:
```bash
kubectl port-forward deployment/vllm-tpu-v7x 8000:8000
```

Send a test request:
```bash
curl http://localhost:8000/v1/completions \
-H "Content-Type: application/json" \
-d '{
"model": "Qwen/Qwen2.5-Coder-7B-Instruct",
"prompt": "def hello_world():",
"max_tokens": 10
}'
```
