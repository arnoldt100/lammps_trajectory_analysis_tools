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

#--
#--
#--
#--
import numpy as np
import MDAnalysis as mda

# 1. Define your inputs (Replace with your actual variables)
psf_file_path = "path/to/your/topology.psf"
dt = 2.0  # Your time step value
time_unit = "ps"  # e.g., 'ps' or 'ns'

# Example dummy data: Replace with your actual numpy arrays
# Let's assume you have 10 frames and 100 atoms
n_frames = 10
n_atoms = 100  # Must match the number of atoms in your PSF file

# Coordinates shape must be (n_frames, n_atoms, 3)
coordinates_array = np.random.rand(n_frames, n_atoms, 3) * 10

# Box dimensions shape must be (n_frames, 6) -> [a, b, c, alpha, beta, gamma]
# Example: 50x50x50 Angstrom cubic box for all frames
box_array = np.array([[50.0, 50.0, 50.0, 90.0, 90.0, 90.0] for _ in range(n_frames)])

# 2. Initialize the Universe using your PSF topology
u = mda.Universe(psf_file_path)

# 3. Load the coordinates and box dimensions into memory
u.load_new(
    coordinates_array,
    format="MemoryReader",
    dt=dt,
    dimensions=box_array
)

# 4. Explicitly assign the units (MDAnalysis defaults to 'ps' and 'Angstrom')
u.trajectory.units = {'time': time_unit, 'length': 'Angstrom'}

# 5. Verify the setup
print(f"Total Frames: {u.trajectory.n_frames}")
print(f"Current Time (Frame 0): {u.trajectory.time} {u.trajectory.units['time']}")
u.trajectory[1]  # Move to second frame
print(f"Current Time (Frame 1): {u.trajectory.time} {u.trajectory.units['time']}")

