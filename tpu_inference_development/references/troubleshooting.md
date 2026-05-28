# Debugging and VCS Tips for vLLM on TPU

This reference guide captures common troubleshooting steps and best practices
discovered during development and debugging of vLLM on TPU VMs.

## 1. TPU Environment Troubleshooting

### Stale Libtpu Lockfile
When a JAX process crashes or is interrupted on the TPU VM, it may leave a
stale lockfile behind, preventing future JAX processes from initializing the
TPU.
*   **Symptom**: `RuntimeError: Unable to initialize backend 'tpu': ABORTED:
    Internal error when accessing libtpu multi-process lockfile.`
*   **Solution**: Run the following command on the remote TPU VM to remove the
    lockfile:
    ```bash
    sudo rm /tmp/libtpu_lockfile
    ```

### Dumping XLA HLO IR for JAX Models
When using JAX models (`MODEL_IMPL_TYPE=flax_nnx`), standard vLLM flags like
`VLLM_DEBUG_DUMP_PATH` (which target PyTorch Inductor) may be ignored.
*   **Solution**: Use the standard XLA environment variable to dump HLO IR
    files for compilation debugging:
    ```bash
    export XLA_FLAGS="--xla_dump_to=/tmp/xla_dump"
    ```
    This will generate graph files in the specified directory on the TPU VM.

## 2. Dependency Discovery

### Finding Compatible vLLM Commits
If the `requirements.txt` in `tpu-inference` does not explicitly pin a `vllm`
commit, you can find the Last Known Good (LKG) commit that the team uses for
automated testing in:
*   `.buildkite/vllm_lkg.version` (inside the `tpu-inference` repository).


