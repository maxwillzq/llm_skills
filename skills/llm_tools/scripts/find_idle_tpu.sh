#!/bin/bash
#
# Find idle TPUs in a project.
#

source gbash.sh || exit

DEFINE_string projects "tpu-prod-env-one-vm,cloud-tpu-inference-test" "Comma-separated list of GCP Projects"
# shared=false is for this script debugging only. Please never use it.
DEFINE_string shared "false" "Filter by shared label (true/false)"
DEFINE_string user "$(whoami)_google_com" "SSH username"
DEFINE_bool list_all true "List all idle TPUs instead of stopping at the first one"
DEFINE_string accelerator_type "tpu7x-8" "Filter by accelerator type"

function main() {
  local shared="${FLAGS_shared}"
  local user="${FLAGS_user}"
  local list_all="${FLAGS_list_all}"
  local accelerator_type="${FLAGS_accelerator_type}"
  
  # Convert comma-separated string to array
  IFS=',' read -r -a projects_array <<< "${FLAGS_projects}"

  local found_idle=false

  # Output CSV header
  echo "Project,Name,IP,Status,LastLogin,AcceleratorType"

  for project in "${projects_array[@]}"; do
    local filter=""
    local filters=()
    if [[ "${shared}" == "true" ]]; then
        filters+=("labels.shared=true")
    fi
    if [[ -n "${accelerator_type}" ]]; then
        filters+=("acceleratorType:${accelerator_type}")
    fi

    if [[ ${#filters[@]} -gt 0 ]]; then
        filter="--filter="
        for i in "${!filters[@]}"; do
            if [[ $i -gt 0 ]]; then
                filter+=" AND "
            fi
            filter+="${filters[$i]}"
        done
    fi

    local tpus_output
    tpus_output=$(/usr/bin/gcloud compute tpus tpu-vm list --zone=- --project="${project}" ${filter} --format="value(name,networkEndpoints[0].accessConfig.externalIp,acceleratorType)" 2>/dev/null | shuf)

    if [[ -z "${tpus_output}" ]]; then
        continue
    fi

    while read -r name ip type; do
        if [[ -z "${name}" ]]; then
            continue
        fi
        # Ensure we only get the name, not the full path
        name=$(basename "${name}")

        # 1. Check if Idle
        libtpu_check=$(ssh -n -o ConnectTimeout=5 -o PasswordAuthentication=no -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR "${user}@${ip}" "grep -l 'libtpu.so' /proc/*/maps 2>/dev/null" 2>&1)
        local status=$?

        # 2. Handle connection failure
        if [[ $status -eq 255 ]]; then
            if [[ "${libtpu_check}" == *"timed out"* ]]; then
                echo "${project},${name},${ip},Timeout,N/A,${type}"
            else
                echo "${project},${name},${ip},SSH Failed,N/A,${type}"
            fi
            continue
        fi

        # 3. Handle idle or busy
        if [[ -z "${libtpu_check}" ]]; then
            # Get last login time
            last_login=$(ssh -n -o ConnectTimeout=5 -o PasswordAuthentication=no -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR "${user}@${ip}" "last -n 1 | head -n 1" 2>/dev/null)
            # Clean commas in last_login to avoid breaking CSV format
            last_login=$(echo "${last_login}" | tr ',' ';')
            echo "${project},${name},${ip},Idle,${last_login},${type}"
            found_idle=true
        else
            echo "${project},${name},${ip},Busy,N/A,${type}"
        fi
    done <<< "${tpus_output}"
  done

  if [[ "${found_idle}" == "true" ]]; then
      return 0
  else
      return 1
  fi
}

gbash::main "$@"
