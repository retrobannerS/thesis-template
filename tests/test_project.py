import subprocess
import os
import re
import sys
import shutil

# Configuration
DOCUMENTS = ["1-task", "2-rspz", "3-pz"]
OUT_DIR = "out"
AUX_DIR = os.path.join(OUT_DIR, ".latex_tmp_files")

def clean_build_artifacts():
    """Cleans the output directory before starting tests."""
    print(f"🧹 Cleaning output directory: {OUT_DIR}...")
    if os.path.exists(OUT_DIR):
        try:
            shutil.rmtree(OUT_DIR)
            print("   Cleaned successfully.")
        except Exception as e:
            print(f"   Warning: Could not clean {OUT_DIR}: {e}")
    else:
        print("   Directory already clean.")

def run_latexmk(doc_name):
    """Runs latexmk for a specific document."""
    print(f"🔄 Compiling {doc_name}.tex...")
    cmd = [
        "latexmk",
        "-xelatex",
        "-interaction=nonstopmode",
        f"-outdir={OUT_DIR}",
        f"-auxdir={AUX_DIR}",
        "-file-line-error",
        f"{doc_name}.tex"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result

def analyze_log(doc_name):
    """Analyzes the .log file for common LaTeX issues."""
    # Note: Log files are usually in the auxdir if specified, 
    # but latexmk often mirrors the main log to outdir or keeps it in auxdir depending on config.
    # With -auxdir, the .log file usually ends up in the AUX_DIR.
    log_path = os.path.join(AUX_DIR, f"{doc_name}.log")
    
    # Fallback to check OUT_DIR if not found in AUX_DIR (some versions behave differently)
    if not os.path.exists(log_path):
        log_path_alt = os.path.join(OUT_DIR, f"{doc_name}.log")
        if os.path.exists(log_path_alt):
            log_path = log_path_alt

    issues = {
        "errors": [],
        "undefined_refs": [],
        "undefined_cites": [],
        "overfull_hboxes": 0
    }
    
    if not os.path.exists(log_path):
        print(f"   ⚠️ Warning: Log file not found at {log_path}")
        return issues
        
    with open(log_path, 'r', encoding='latin-1', errors='replace') as f:
        content = f.read()
        
        # Check for LaTeX Errors
        # Simple regex for lines starting with ! or containing "Error:"
        error_matches = re.findall(r"^!.*$|^.*Error:.*$", content, re.MULTILINE)
        issues["errors"] = error_matches
        
        # Check for undefined references
        ref_matches = re.findall(r"Reference `(.*?)' on page .* undefined", content)
        issues["undefined_refs"] = ref_matches
        
        # Check for undefined citations
        cite_matches = re.findall(r"Citation `(.*?)' on page .* undefined", content)
        issues["undefined_cites"] = cite_matches
        
        # Count overfull hboxes
        issues["overfull_hboxes"] = len(re.findall(r"Overfull \\hbox", content))
        
    return issues

def main():
    print("🚀 Starting automated LaTeX testing...\n")
    
    # Clean previous builds
    clean_build_artifacts()
    print("")
    
    overall_success = True
    
    for doc in DOCUMENTS:
        # Compile
        result = run_latexmk(doc)
        
        # Analyze
        issues = analyze_log(doc)
        
        # Report
        print(f"--- Report for {doc} ---")
        
        if result.returncode != 0:
            print("❌ Compilation FAILED")
            overall_success = False
            # Print last few lines of stderr/stdout for context
            print("Last 10 lines of output:")
            print("\n".join(result.stdout.splitlines()[-10:]))
        else:
            print("✅ Compilation SUCCESS")
            
        if issues["errors"]:
            print(f"❌ Found {len(issues['errors'])} critical errors in log (even if compiled):")
            for err in issues["errors"][:5]:
                print(f"  - {err.strip()}")
            overall_success = False
            
        if issues["undefined_refs"]:
            print(f"⚠️  Undefined References ({len(issues['undefined_refs'])}):")
            for ref in issues['undefined_refs'][:5]:
                print(f"  - {ref}")
            if len(issues['undefined_refs']) > 5: print("  ... and more")
            
        if issues["undefined_cites"]:
            print(f"⚠️  Undefined Citations ({len(issues['undefined_cites'])}):")
            for cite in issues['undefined_cites'][:5]:
                print(f"  - {cite}")
                
        if issues["overfull_hboxes"] > 0:
            print(f"ℹ️  Overfull HBoxes: {issues['overfull_hboxes']} (check formatting)")
            
        print("")

    if overall_success:
        print("✨ All documents passed smoke tests!")
        sys.exit(0)
    else:
        print("🛑 Some tests failed. Please review the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
