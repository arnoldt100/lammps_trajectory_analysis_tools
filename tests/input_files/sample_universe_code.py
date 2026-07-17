import numpy as np
import MDAnalysis as mda
from MDAnalysis.coordinates.memory import MemoryReader

# 1. Paths and inputs
psf_file = "fc_14_atoms.psf"

# Define a FCC structure with edge length 5.19 angstroms
edge_length=np.float64(5.19)

# Your NumPy positions array. Shape must be (N_atoms, 3)
# Replace with your actual array variable name
positions_array = edge_length*np.array([
                [0.00,0.00,0.00],
                [0.50,0.50,0.00],
                [0.50,0.00,0.50],
                [0.00,0.50,0.50],
                [0.00,0.00,1.00],
                [0.50,0.50,1.00],
                [0.00,1.00,0.00],
                [0.50,1.00,0.50],
                [0.00,1.00,1.00],
                [1.00,0.00,0.00],
                [1.00,0.50,0.50],
                [1.00,0.00,1.00],
                [1.00,1.00,0.00],
                [1.00,1.00,1.00]],dtype=np.float64)

# 2. Add an explicit time/frame dimension for the MemoryReader
# Converts shape from (N_atoms, 3) to a single-frame trajectory: (1, N_atoms, 3)
single_frame_trajectory = np.expand_dims(positions_array, axis=0)

# 3. Create box dimensions for this single frame
# Format: [lx, ly, lz, alpha, beta, gamma]
box_dimensions = np.array([[edge_length,edge_length,edge_length,90.0, 90.0, 90.0]],dtype=np.float64)

# 4. Build the Universe with a single-frame trajectory
u = mda.Universe(
    psf_file, 
    single_frame_trajectory, 
    format=MemoryReader, 
    dimensions=box_dimensions
)

# 5. Verify trajectory and system traits
print(f"Total number of frames: {u.trajectory.n_frames}")
print(f"Current frame index: {u.trajectory.ts.frame}")
print(f"Periodic Box: {u.dimensions}")
print(f"Atom positions:\n{u.atoms.positions}")

