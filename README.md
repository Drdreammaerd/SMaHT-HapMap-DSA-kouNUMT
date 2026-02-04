# SMaHT-HapMap-DSA-kouNUMT

This repository stores the essential files for running the Koumokuyou-NUMT on SMaHT HapMap Mixture DSA.

For more information about the HapMap mixture, please visit: [SMaHT HapMap Benchmarking Data](https://data.smaht.org/data/benchmarking/HapMap)

## Pipeline Documentation
The full pipeline is documented here: [Koumokuyou-NUMT](https://github.com/Drdreammaerd/Koumokuyou-NUMT.git)

## Environment
We use the docker image `dreammaerd/last-train:v4` on the WUSTL RIS system.

## Usage
To run the pipeline on the HPRC DSA, use the submission script:
```bash
bin/submit_all_HPRC_DSA.sh
```

## Benchmarking Results
Before running on HPRC DSA, the pipeline was tested on the hg38 reference genome.

**Truth Set**: The UCSC tracker served as the truth set for comparison: [UCSC nuMtSeq Track](https://genome.ucsc.edu/cgi-bin/hgTables?db=hg38&hgta_group=rep&hgta_track=nuMtSeq)

**Evaluation**: Results were compared using the script `bin/evaluate_numt.py`.

### NUMT Evaluation Report
```text
=============================================
        NUMT EVALUATION REPORT
=============================================
Date:         2026-02-02 15:54:19
Truth:        NuMtseq_hg38.bed
Method:       Human_Hg38_Numts_filtered.bed
Overlap Min:  1e-09
Logic Mode:   reciprocal
---------------------------------------------
TOTAL Truth NUMTs:       1071
TOTAL Method Predictions: 1079
---------------------------------------------
True Positives (TP):     1025
False Positives (FP):    54
False Negatives (FN):    24
---------------------------------------------
Precision:               0.9500
Recall (Sensitivity):    0.9776
F1-Score:                0.9636
=============================================
```

### Experimental Validation
An alternative validation script `bin/validate_numt_calls.py` is provided for biological validation using BLAT. 

> [!WARNING]
> This method is currently experimental and has shown low sensitivity (e.g., validating only ~148 calls). The primary evaluation should rely on `bin/evaluate_numt.py`.

Usage:
```bash
python bin/validate_numt_calls.py --input_bed <your_bed_file>
```
Output will be saved as `<input_basename>_validated.bed`.
