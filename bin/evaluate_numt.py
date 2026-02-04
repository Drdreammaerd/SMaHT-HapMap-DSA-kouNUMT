## Python 2.7 compatible script to evaluate NUMT detection performance using bedtools.
## Docker: biocontainers/bedtools:v2.28.0_cv2
## Calculates TP, FP, FN, Precision, Recall, and F1-Score based on overlap criteria.
import subprocess
import argparse
import os
from datetime import datetime

def get_count(command):
    """Executes a shell command and returns the integer count from wc -l (Python 2.7 compatible)."""
    try:
        # In Python 2.7, we use check_output to get the result from the shell
        output = subprocess.check_output(command, shell=True)
        return int(output.strip())
    except Exception:
        return 0

def run_command(command):
    """Executes a shell command without returning a value (for file saving)."""
    subprocess.check_call(command, shell=True)

def main():
    parser = argparse.ArgumentParser(description='Evaluate NUMT performance and save reports.')
    
    # Required Paths
    parser.add_argument('--truth', type=str, 
                        default='/storage1/fs1/jin810/Active/testing/yung-chun/AI-develop/NUMT-HapMap-TrueSet/UCSC_NUMT_hg38/NuMtseq_hg38.bed',
                        help='Path to the Truth BED file')
    parser.add_argument('--method', type=str, required=True,
                        help='Path to the Method results BED file')
    
    # Overlap Logic Options
    parser.add_argument('--overlap', type=float, default=1e-9,
                        help='Minimum overlap fraction (e.g., 0.50). Default is 1bp.')
    parser.add_argument('--reciprocal', action='store_true',
                        help='Require reciprocal overlap.')
    
    # Output Options
    parser.add_argument('--output_dir', type=str, default='Evaluation_Reports',
                        help='Folder to save reports (default: Evaluation_Reports)')
    parser.add_argument('--save', action='store_true',
                        help='Save the output to a text file.')
    
    args = parser.parse_args()

    # Build the bedtools flag string using .format()
    overlap_flags = "-f {0}".format(args.overlap)

    if args.reciprocal:
        overlap_flags += " -r"

    # Get Total Counts (New Feature)
    count_truth_cmd = "cat {0} | wc -l".format(args.truth)
    count_method_cmd = "cat {0}| wc -l".format(args.method)
    
    TOTAL_TRUTH = get_count(count_truth_cmd)
    TOTAL_METHOD = get_count(count_method_cmd)

    # 1. Precision Checks (Method Perspective)
    # TP_Method: Method calls that are correct
    tp_method_cmd = "bedtools intersect -a {0} -b {1} -u {2} | wc -l".format(args.method, args.truth, overlap_flags)
    # FP: Method calls that are wrong
    fp_cmd = "bedtools intersect -a {0} -b {1} -v {2} | wc -l".format(args.method, args.truth, overlap_flags)

    # 2. Recall Checks (Truth Perspective - THIS FIXES THE MATH)
    # TP_Truth: Truths that were found (regardless of how many method calls did it)
    tp_truth_cmd = "bedtools intersect -a {0} -b {1} -u {2} | wc -l".format(args.truth, args.method, overlap_flags)
    # FN: Truths that were missed
    fn_cmd = "bedtools intersect -a {0} -b {1} -v {2} | wc -l".format(args.truth, args.method, overlap_flags)

    TP_METHOD = get_count(tp_method_cmd) # For Precision
    FP = get_count(fp_cmd)
    
    TP_TRUTH = get_count(tp_truth_cmd)   # For Recall
    FN = get_count(fn_cmd)

    # Math Check
    # Precision = Correct Calls / Total Calls
    precision = float(TP_METHOD) / (TP_METHOD + FP) if (TP_METHOD + FP) > 0 else 0.0
    
    # Recall = Found Truths / Total Truths
    recall = float(TP_TRUTH) / (TP_TRUTH + FN) if (TP_TRUTH + FN) > 0 else 0.0
    
    f1 = 2.0 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    # Format Report Content
    method_name = os.path.basename(args.method).replace(".bed", "")
    truth_name = os.path.basename(args.truth).replace(".bed", "")
    mode = "reciprocal" if args.reciprocal else "oneway"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    report_content = """
=============================================
        NUMT EVALUATION REPORT
=============================================
Date:         {0}
Truth:        {1}
Method:       {2}
Overlap Min:  {3}
Logic Mode:   {4}
---------------------------------------------
TOTAL Truth NUMTs:       {5}
TOTAL Method Predictions: {6}
---------------------------------------------
True Positives (TP):     {7}
False Positives (FP):    {8}
False Negatives (FN):    {9}
---------------------------------------------
Precision:               {10:.4f}
Recall (Sensitivity):    {11:.4f}
F1-Score:                {12:.4f}
=============================================
""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
           os.path.basename(args.truth),
           os.path.basename(args.method),
           args.overlap, mode, 
           TOTAL_TRUTH, TOTAL_METHOD, 
           TP_METHOD, FP, FN, 
           precision, recall, f1)

    # Print to Console
    print(report_content)

    # Save to File
    if args.save:
        if not os.path.exists(args.output_dir):
            os.makedirs(args.output_dir)
        
        filename = "Report_{0}_vs_{1}_ov{2}_{3}_{4}.txt".format(method_name, truth_name, args.overlap, mode, timestamp)
        file_path = os.path.join(args.output_dir, filename)
        
        with open(file_path, "w") as f:
            f.write(report_content)
        print("Report saved to: {0}".format(file_path))

        # 2. Save True Positive BED (The "Missed" Truths)
        tp_filename = "TruePositives_{0}_vs_{1}_ov{2}_{3}_{4}.bed".format(truth_name, method_name, args.overlap, mode, timestamp)
        tp_path = os.path.join(args.output_dir, tp_filename)

        save_tp_cmd = "bedtools intersect -a {0} -b {1} -u {2}  > {3}".format(args.truth, args.method, overlap_flags, tp_path)

        run_command(save_tp_cmd)
        print("True Positive BED saved to: {0}".format(tp_path))

        # 2. Save False Negatives BED (The "Missed" Truths)
        fn_filename = "FalseNegatives_{0}_vs_{1}_ov{2}_{3}_{4}.bed".format(truth_name, method_name, args.overlap, mode, timestamp)
        fn_path = os.path.join(args.output_dir, fn_filename)

        save_fn_cmd = "bedtools intersect -a {0} -b {1} -v {2} > {3}".format(args.truth, args.method, overlap_flags, fn_path)
        
        run_command(save_fn_cmd)
        print("False Negatives BED saved to: {0}".format(fn_path))

if __name__ == "__main__":
    main()