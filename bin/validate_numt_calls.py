## Python 3 script to biologically validate NUMT BED regions using BLAT. 
## Docker: dreammaerd/python-mpra:v2
import subprocess
import argparse
import os
import pysam
import pandas as pd
from datetime import datetime

# --- PRESET GLOBAL VARIABLES ---
BLAT_BIN = "/storage1/fs1/jin810/Active/testing/yung-chun/genomicstools/blat/blat"
CHR_M = "/storage1/fs1/jin810/Active/testing/yung-chun/AI-develop/NUMT-Blat/Reference/chrM.fa"
DEFAULT_REF = "/storage1/fs1/jin810/Active/References/GATK-SV/resources_hg38_json/reference_fasta/Homo_sapiens_assembly38.fasta"

def main():
    parser = argparse.ArgumentParser(description='Biological Validation of NUMT BED regions using BLAT.')
    parser.add_argument('--input_bed', required=True, help='BED file to validate')
    parser.add_argument('--genome', default=DEFAULT_REF, help='Reference genome (hg38 or DSA)')
    parser.add_argument('--out_dir', default='Validation_Reports_BLAT')
    
    args = parser.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    
    base_name = os.path.basename(args.input_bed).split('.')[0]
    temp_fa = os.path.join(args.out_dir, f"{base_name}_extracted.fasta")
    out_psl = os.path.join(args.out_dir, f"{base_name}_vs_chrM.psl")
    final_report = os.path.join(args.out_dir, f"{base_name}_validation_detail.txt")
    validated_bed = os.path.join(args.out_dir, f"{base_name}_validated.bed")

    # 1. Get the fa seq from ref
    print(f"[*] Extracting sequences from {os.path.basename(args.genome)}...")
    with pysam.FastaFile(args.genome) as fasta_ref, open(temp_fa, "w") as out_fa:
        with open(args.input_bed, "r") as bed:
            for line in bed:
                if line.startswith(("#", "track", "browser")) or not line.strip():
                    continue
                cols = line.strip().split("\t")
                chrom, start, end = cols[0], int(cols[1]), int(cols[2])
                region_id = f"{chrom}:{start}-{end}"
                
                try:
                    seq = fasta_ref.fetch(chrom, start, end)
                    out_fa.write(f">{region_id}\n{seq}\n")
                except KeyError:
                    print(f"[!] Warning: {chrom} not found in genome index.")

    # 2. Validatoin via BLAT
    print(f"[*] Running BLAT validation against {os.path.basename(CHR_M)}...")
    blat_cmd = [
        BLAT_BIN, CHR_M, temp_fa, out_psl,
        "-t=dna", "-q=dna", "-out=psl", "-noHead",
        "-repMatch=2253", "-minIdentity=90", "-stepSize=5", "-tileSize=11", "-minScore=20"
    ]
    subprocess.run(blat_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    # 3. Parse BLAT results
    valid_hits = set()
    if os.path.exists(out_psl) and os.path.getsize(out_psl) > 0:
        # index 9: Query Name (our Region_ID)
        try:
            results = pd.read_csv(out_psl, sep='\t', header=None)
            valid_hits = set(results[9].unique())
        except Exception as e:
            print(f"[-] Error parsing PSL: {e}")

    # 4. generate final report
    print(f"[*] Generating report: {final_report}")
    with open(args.input_bed, "r") as infile, \
         open(final_report, "w") as report, \
         open(validated_bed, "w") as v_bed:
        
        report.write("Region_ID\tStatus\n")
        total, passed = 0, 0
        
        for line in infile:
            if line.startswith(("#", "track", "browser")) or not line.strip():
                continue
            cols = line.strip().split("\t")
            region_id = f"{cols[0]}:{cols[1]}-{cols[2]}"
            total += 1
            
            if region_id in valid_hits:
                report.write(f"{region_id}\tVALIDATED\n")
                v_bed.write(line)
                passed += 1
            else:
                report.write(f"{region_id}\tFAILED_BLAT_MAPPING\n")

    # 5. Summary Output
    print("\n" + "="*45)
    print(f"{'BLAT VALIDATION SUMMARY':^45}")
    print("="*45)
    print(f"Method Tested:    {base_name}")
    print(f"Total Regions:    {total}")
    print(f"Validated (TP):   {passed}")
    print(f"Failed (FP):      {total - passed}")
    print(f"Confidence Rate:  {(passed/total)*100:.2f}%" if total > 0 else "0.00%")
    print("="*45 + "\n")

if __name__ == "__main__":
    main()