#!/usr/bin/env python3
import argparse
import numpy as np

def generate_fcc_primitive_supercell(edge_length, size):
    """Generates an FCC supercell using skewed 1-atom primitive cell vectors."""
    a = edge_length
    nx, ny, nz = size
    
    a1 = 0.5 * a * np.array([0.0, 1.0, 1.0])
    a2 = 0.5 * a * np.array([1.0, 0.0, 1.0])
    a3 = 0.5 * a * np.array([1.0, 1.0, 0.0])
    
    atoms = []
    for i in range(nx):
        for j in range(ny):
            for k in range(nz):
                pos = i * a1 + j * a2 + k * a3
                atoms.append(pos)
    return np.array(atoms)

def generate_fcc_conventional_supercell(edge_length, size):
    """Generates an FCC supercell using regular 4-atom cubic conventional blocks."""
    a = edge_length
    nx, ny, nz = size
    
    basis = np.array([
        [0.0, 0.0, 0.0],  # Corner
        [0.5, 0.5, 0.0],  # XY Face
        [0.5, 0.0, 0.5],  # XZ Face
        [0.0, 0.5, 0.5]   # YZ Face
    ]) * a

    atoms = []
    for i in range(nx):
        for j in range(ny):
            for k in range(nz):
                cube_origin = np.array([i, j, k]) * a
                for basis_atom in basis:
                    atoms.append(cube_origin + basis_atom)
    return np.array(atoms)

def main():
    parser = argparse.ArgumentParser(
        description="Generate FCC primitive or conventional lattice supercells."
    )
    
    # Required Arguments
    parser.add_argument(
        "-e", "--edge-length", 
        type=float, 
        required=True, 
        help="Conventional unit cell edge length (a) in Angstroms."
    )
    
    parser.add_argument(
        "-s", "--size", 
        type=int, 
        nargs=3, 
        required=True, 
        metavar=('X', 'Y', 'Z'),
        help="Number of unit cell repetitions in X, Y, and Z directions (e.g., 3 3 3)."
    )

    # Optional Lattice Choice Flag (Defaults to conventional)
    parser.add_argument(
        "-t", "--type", 
        type=str, 
        choices=["primitive", "conventional"], 
        default="conventional",
        help="Type of lattice definition to use. Choices: primitive, conventional (default)."
    )

    args = parser.parse_args()

    # Select generation method based on user choice
    if args.type == "primitive":
        atom_positions = generate_fcc_primitive_supercell(args.edge_length, args.size)
    else:
        atom_positions = generate_fcc_conventional_supercell(args.edge_length, args.size)
    
    # Terminal output report
    print(f"=== FCC {args.type.upper()} Supercell Generated ===")
    print(f"Conventional edge length: {args.edge_length}")
    print(f"Supercell dimension size: {args.size[0]}x{args.size[1]}x{args.size[2]}")
    print(f"Total number of atoms:    {len(atom_positions)}")
    print(f"=========================================\n")
    print("Atom coordinates:")
    print(atom_positions[:])

if __name__ == "__main__":
    main()

