import sys
import importlib
from MDAnalysis.analysis.rms import RMSD

def check_parallel_backends(analysis_class):
    """
    Checks and prints the supported parallel backends for a given 
    MDAnalysis tool class, verifying if their third-party dependencies are met.
    """
    print(f"--- Checking Backends for {analysis_class.__name__} ---")
    
    # 1. Fetch the theoretically supported backends by the tool
    try:
        supported_backends = analysis_class.get_supported_backends()
        print(f"Theoretically supported by this tool: {list(supported_backends)}")
    except AttributeError:
        print("[-] This version of MDAnalysis does not support the split-apply-combine parallel framework.")
        print("    Please upgrade to MDAnalysis >= 2.8.0.")
        return

    # 2. Check the system readiness for each backend
    print("\nSystem Availability Status:")
    for backend in supported_backends:
        if backend == 'serial':
            print("  [✓] serial          : Available (Default execution style)")
            
        elif backend == 'multiprocessing':
            print("  [✓] multiprocessing : Available (Uses standard library)")
            
        elif backend == 'dask':
            # Verify if dask package is installed in the environment
            dask_available = importlib.util.find_spec("dask") is not None
            if dask_available:
                print("  [✓] dask            : Available (Package 'dask' is installed)")
            else:
                print("  [X] dask            : UNAVAILABLE (Missing 'dask' package. Run: pip install dask)")
                
        else:
            print(f"  [?] {backend}          : Unknown/Custom backend detected.")

if __name__ == "__main__":
    # We use RMSD as an example, as it is natively parallelizable in MDAnalysis
    check_parallel_backends(RMSD)

