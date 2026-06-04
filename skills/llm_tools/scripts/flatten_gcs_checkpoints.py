import sys
import subprocess

def run_cmd(cmd):
    print(f"[run] {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout

def flatten_bucket(bucket_name):
    bucket_uri = f"gs://{bucket_name}"
    
    # List all top-level items in the bucket
    stdout = run_cmd(["gcloud", "storage", "ls", f"{bucket_uri}/"])
    lines = stdout.splitlines()
    
    model_folders = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = line.split('/')
        if len(parts) >= 4:
            folder_name = parts[3]
            if folder_name.startswith("models--"):
                model_folders.append(folder_name)
                
    print(f"Found model folders: {model_folders}")
    
    for model_folder in model_folders:
        model_uri = f"{bucket_uri}/{model_folder}"
        print(f"Checking {model_folder}...")
        
        # Look for snapshots directory under the model folder
        try:
            snapshots_stdout = run_cmd(["gcloud", "storage", "ls", f"{model_uri}/snapshots/"])
        except subprocess.CalledProcessError:
            print(f"No snapshots folder found in {model_folder}, skipping.")
            continue
            
        snapshot_uri = None
        for line in snapshots_stdout.splitlines():
            line = line.strip()
            if line.endswith('/') and not line.endswith('snapshots/'):
                snapshot_uri = line
                break

        if not snapshot_uri:
            print(f"No valid snapshot subdirectory found in {model_folder}, skipping.")
            continue
            
        print(f"Flattening {model_folder} using snapshot {snapshot_uri}...")
        
        # 1. Copy all files from the snapshot directory to the model root, resolving symlinks if necessary
        ls_out = run_cmd(["gcloud", "storage", "ls", "-l", f"{snapshot_uri}**"])
        for line in ls_out.splitlines():
            line = line.strip()
            if not line or "TOTAL:" in line or line.endswith(':'):
                continue
            parts = line.split(maxsplit=2)
            if len(parts) < 3:
                continue
            try:
                size = int(parts[0])
            except ValueError:
                continue
            file_uri = parts[2]
            if file_uri.endswith('/'):
                continue
            filename = file_uri[len(snapshot_uri):]
            dest_uri = f"{model_uri}/{filename}"
            
            is_symlink = False
            if size <= 200:
                content = run_cmd(["gcloud", "storage", "cat", file_uri]).strip()
                if content.startswith("../"):
                    is_symlink = True
                    rel_path = content.replace("../", "")
                    src_uri = f"{model_uri}/{rel_path}"
                    print(f"  Resolving symlink {filename} -> {rel_path}...")
                    run_cmd(["gcloud", "storage", "cp", src_uri, dest_uri])
            
            if not is_symlink:
                print(f"  Copying {filename} directly...")
                run_cmd(["gcloud", "storage", "cp", file_uri, dest_uri])
        
        # 2. Clean up subdirectories
        for subdir in ["blobs", "snapshots", "refs", ".no_exist"]:
            subdir_uri = f"{model_uri}/{subdir}/"
            try:
                # Check if subdir exists by listing it
                run_cmd(["gcloud", "storage", "ls", subdir_uri])
                print(f"  Deleting {subdir_uri}...")
                run_cmd(["gcloud", "storage", "rm", "-r", subdir_uri])
            except subprocess.CalledProcessError:
                # Subdirectory does not exist, ignore
                pass
                
    print("Flattening completed successfully.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 flatten_gcs_checkpoints.py <bucket_name>")
        sys.exit(1)
    flatten_bucket(sys.argv[1])
