# Migrating Docker Data Directory to /mnt/pd

On Cloud TPU VMs, the root disk (`/`) is often small (e.g., 96GB), and building large Docker images can easily fill it up. It is recommended to move the Docker data directory to the larger persistent disk (`/mnt/pd`).

## Steps to Migrate

To actually move the Docker data directory, follow these steps (requires `sudo` permissions):

1.  **Stop the Docker service**:
    ```bash
    sudo systemctl stop docker
    ```

2.  **Modify or create the configuration file** `/etc/docker/daemon.json` to add the `"data-root"` setting:
    ```json
    {
      "data-root": "/mnt/pd/docker"
    }
    ```

3.  **Migrate existing Docker data** (optional, but recommended to keep existing images):
    ```bash
    sudo mkdir -p /mnt/pd/docker
    sudo rsync -aP /var/lib/docker/ /mnt/pd/docker/
    ```

4.  **Restart the Docker service**:
    ```bash
    sudo systemctl start docker
    ```

## Verification

After restarting, verify that Docker is using the new path:
```bash
docker info | grep "Docker Root Dir"
```
It should show `/mnt/pd/docker`.
