#!/bin/bash

## Date
DATE=$( date +%F | sed "s/-//g")

### Bash Strict Mode
set -euo pipefail
IFS=$'\n\t'

# --- Configuration --- Edit as needed
INPUT_ROOT="/storage2/fs1/epigenome/Active/shared_smaht/data/HPRC_Assemblies/RagTag_Scaffolded_Assemblies"
SCRIPT_PATH="/storage1/fs1/jin810/Active/testing/yung-chun/AI-develop/NUMT-HapMap-TrueSet/run_kuo_numts_CMD.sh"
BASE_OUT_DIR="/storage1/fs1/jin810/Active/testing/yung-chun/AI-develop/NUMT-HapMap-TrueSet/Kou_LAST_Method/HPRC_Results"
LOG_BASE="/storage1/fs1/jin810/Active/testing/yung-chun/JOBS/${DATE}_HPRC_KouNumt_Logs"

# --- Option Parsing for Dry Run ---
dry_run="false"

while getopts "dh" opt; do
  case $opt in
    d) dry_run="true" ;;
    h) echo "Usage: $0 [-d] (d = dry run)"; exit 0 ;;
    *) echo "Invalid option"; exit 1 ;;
  esac
done

# Create directories only if NOT dry run (or just do it, harmless)
if [[ "$dry_run" == "false" ]]; then
    mkdir -p "$BASE_OUT_DIR"
    mkdir -p "$LOG_BASE"
fi

# --- Loop through directories ---
count=0
for folder in $INPUT_ROOT/*_mat $INPUT_ROOT/*_pat; do
    
    sample_name=$(basename "$folder")
    
    # --- Find Fasta ---
    if [ -f "$folder/$sample_name.fasta" ]; then
        input_fasta="$folder/$sample_name.fasta"
    elif [ -f "$folder/$sample_name.fasta.gz" ]; then
        input_fasta="$folder/$sample_name.fasta.gz"
    else
        # Skip silently or warn, but don't crash
        # echo "Warning: No fasta for $sample_name"
        continue
    fi

    # --- Job Parameters ---
    sample_out_dir="$BASE_OUT_DIR/$sample_name"
    sample_log_dir="$LOG_BASE"
    
    job_name="KuoNumt_${sample_name}"
    log_file="$sample_log_dir/${job_name}.log"
    err_file="$sample_log_dir/${job_name}.err"

    # --- Submit or Dry Run ---
    if [[ "$dry_run" == "true" ]]; then
        count=$((count + 1))
        echo "[$count] [DRY-RUN] Would submit: $job_name"
        echo "    Input:  $input_fasta"
        echo "    Output: $sample_out_dir"
        echo "    Log:    $err_file"
        echo "    CMD:    bsub ... bash $SCRIPT_PATH -i ... -o ... -n $sample_name"
        echo "---------------------------------------------------"
    else
        # Make the log dir specific to this sample
        mkdir -p "$sample_log_dir"

        #-G compute-jin810 -q general \
        bsub -J "$job_name" \
             -o "$log_file" \
             -e "$err_file" \
             -G compute-jin810-t3 \
             -q subscription \
             -sla jin810_t3 \
             -n 4 \
             -R 'rusage[mem=64GB]' \
             -a 'docker(dreammaerd/last-train:v4)' \
             bash "$SCRIPT_PATH" -i "$input_fasta" -o "$sample_out_dir" -n "$sample_name"
        
        echo "Submitted: $job_name"
    fi

done

if [[ "$dry_run" == "true" ]]; then
    echo "Dry run complete. Found $count samples ready to process."
fi