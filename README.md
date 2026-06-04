# LLM Skills Repository

This repository contains reusable agentic skills and reference guides for TPU VM operations, vLLM development, JAX inference, and GCS checkpoint management. These skills extend the capabilities of the Jetski/Gemini coding agents by linking them directly into your development workflow.

---

## Installation

To make the skills in this repository discoverable by Jetski/Gemini:

1. **Clone this repository** to your local Cloudtop machine:
   ```bash
   git clone git@github.com:maxwillzq/llm_skills.git
   cd llm_skills
   ```

2. **Run the installation script** to symlink the skills into the Jetski directory:
   ```bash
   python3 install.py
   ```

   This script will automatically detect all directories containing `SKILL.md` under `skills/` and symlink them to `~/.gemini/jetski/skills/`.

---

## Configuration

A configuration file (`config.json`) is used by various synchronization and helper scripts (like `tpu_dev_sync.py`) to resolve directories and connection details.

1. **Copy the example configuration file**:
   ```bash
   cp config.example.json config.json
   ```

2. **Customize `config.json`** with your specific environment details:
   ```json
   {
     "tpu_ip": "10.x.x.x",
     "local_projects_dir": "/usr/local/google/home/<your_username>/projects",
     "remote_projects_dir": "/mnt/pd/projects",
     "remote_host": "<your_username>-tpu-v7",
     "hf_checkpoint_gcs_bucket": "gs://tpu-inference-hf-llm-model-checkpoints"
   }
   ```

---

## Available Skills

| Skill | Description | Location |
| :--- | :--- | :--- |
| **`llm-tools`** | Shared utilities like code sync (`tpu_dev_sync.py`) and GCS bucket flattening (`flatten_gcs_checkpoints.py`). | [skills/llm_tools](skills/llm_tools/SKILL.md) |
| **`torch-vllm-development`** | Guide for developing, Docker container setup, and verifying PyTorch `torchtpu-vllm` on TPU VMs. | [skills/torch_vllm_development](skills/torch_vllm_development/SKILL.md) |
| **`tpu-inference-development`** | Developer guide for the high-performance JAX-based `llm_engine` framework. | [skills/tpu_inference_development](skills/tpu_inference_development/SKILL.md) |
| **`sglang-jax-inference`** | Operating, debugging, and extending the SGL-JAX runtime on TPU VMs. | [skills/sglang-jax-inference](skills/sglang-jax-inference/SKILL.md) |
| **`collaborative-problem-solving`** | Agent guidelines to analyze bugs and review plans before modifying code. | [skills/collaborative-problem-solving](skills/collaborative-problem-solving/SKILL.md) |
| **`llm-coding-discipline`** | Coding standards to keep edits minimal, simple, and surgical. | [skills/llm-coding-discipline](skills/llm-coding-discipline/SKILL.md) |
