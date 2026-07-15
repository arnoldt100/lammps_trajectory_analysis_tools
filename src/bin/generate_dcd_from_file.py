#! /usr/bin/env python3
import argparse
import os
import sys
import numpy as np
import MDAnalysis as mda
from MDAnalysis.coordinates.memory import MemoryReader

def load_and_convert_to_dcd(input_file, output_dcd_file="output.dcd", timestep_ps=1.0):
    """
    Loads an (Nx3) numpy array from disk and converts it to a single-step DCD.
    """
    # 1. Verify file existence
    if not os.path.exists(input_file):
        print(f"Error: The file '{input_file}' does not exist.")
        sys.exit(1)

    # 2. Load the array from disk based on file extension
    try:
        if input_file.endswith('.npy'):
            coords_Nx3 = np.load(input_file)
        elif input_file.endswith('.txt') or input_file.endswith('.csv'):
            # Handles commas, spaces, or tabs automatically
            delimiter = ',' if input_file.endswith('.csv') else None
            coords_Nx3 = np.loadtxt(input_file, delimiter=delimiter) 
        else:
            print("Error: Unsupported file format. Please use .npy, .txt, or .csv")
            sys.exit(1)
    except Exception as e:
        print(f"Error loading file: {e}")
        sys.exit(1)

    # 3. Ensure proper data shape (N, 3)
    if coords_Nx3.ndim != 2 or coords_Nx3.shape[1] != 3:
        print(f"Error: Expected array shape (N, 3), but got {coords_Nx3.shape}")
        sys.exit(1)

    # 4. Format for MDAnalysis memory reader
    coords = np.asarray(coords_Nx3, dtype=np.float32)
    N = coords.shape[0]
    frame_coords = coords.reshape(1, N, 3)
 
    # 5. Create trajectory in memory and write to disk
    u = mda.Universe.empty(N, trajectory=True)
    u.load_new(frame_coords, format=MemoryReader)
    
    with mda.Writer(output_dcd_file, n_atoms=N) as W:
        ts = u.trajectory
        ts.dt = timestep_ps  
        W.write(ts)
    
    print(f"Success: Converted {input_file} ({N} atoms) to {output_dcd_file}")

if __name__ == "__main__":
    # Setup command line argument parser
    parser = argparse.ArgumentParser(description="Convert an Nx3 coordinate array file to a single-step DCD trajectory.")
    
    # Positional argument (required)
    parser.add_argument("input_file", type=str, help="Path to the input file (.npy, .csv, or .txt)")
    
    # Optional arguments
    parser.add_argument("-o", "--output", type=str, default="output.dcd", help="Path to the output DCD file (default: output.dcd)")
    parser.add_argument("-t", "--timestep", type=float, default=1.0, help="Timestep value in picoseconds (default: 1.0)")
    
    args = parser.parse_args()
    
    # Run conversion
    load_and_convert_to_dcd(args.input_file, args.output, args.timestep)

