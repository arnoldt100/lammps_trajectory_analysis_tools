# LAMMPS Trajectory Analysis Tools — Architecture

## Project Overview
Collection of Python tools for analyzing LAMMPS molecular dynamics simulation trajectories. Focused on trajectory parsing, statistical analysis, and visualization.

---

## Module Map

### `src/trajectory.py`
**Purpose**: Core trajectory I/O and data structures  
**Exports**:
- `TrajectoryReader`: Parse LAMMPS dump/trajectory files
- `Frame`: Single timestep container (atoms, box, metadata)
- `Trajectory`: In-memory trajectory collection
- `format_detector()`: Identify file format
- `read_dump()`: Unified entry point

**Dependencies**: numpy, internal utils  
**Typical usage**: `traj = read_dump("dump.lammpstrj")`

---

### `src/analysis.py`
**Purpose**: Structural and statistical metrics  
**Exports**:
- `RadialDistributionFunction`: RDF calculator
- `MeanSquareDisplacement`: MSD tracker
- `StructureFactor`: S(q) calculator
- `Cluster`: Clustering utilities
- Helper functions: `compute_distances()`, `bin_data()`

**Dependencies**: numpy, scipy, trajectory.py  
**Typical usage**: `rdf = RadialDistributionFunction(trajectory, cutoff=10.0)`

---

### `src/plotting.py`
**Purpose**: Visualization helpers  
**Exports**:
- `plot_trajectory()`: Animation or frame sequence
- `plot_rdf()`: RDF visualization
- `plot_msd()`: MSD vs time
- `plot_structure_factor()`: S(q) plot

**Dependencies**: matplotlib, numpy, analysis.py  
**Typical usage**: `plot_rdf(rdf_data, filename="rdf.png")`

---

### `src/utils.py`
**Purpose**: Shared utilities (no LAMMPS-specific logic)  
**Exports**:
- `load_config()`: Parse config files
- `validate_input()`: Input validation
- `write_results()`: Export data (CSV, JSON, HDF5)
- `Timer`: Performance profiler context manager
- Logging setup

**Dependencies**: standard library + optional h5py  
**Typical usage**: `config = load_config("params.yaml")`

---

### `src/__init__.py`
**Purpose**: Public API  
**Exports**: High-level imports for end users  
```python
from .trajectory import read_dump, Trajectory
from .analysis import RadialDistributionFunction, MeanSquareDisplacement
from .plotting import plot_rdf, plot_trajectory
```

---

## Dependency Graph
```
trajectory.py ──┐
                ├─→ analysis.py ──┐
utils.py ───────┤                 ├─→ plotting.py
                └──────────────────┘
```

---

## File Size Guidelines
- Each module: ≤500 lines (split if needed)
- Classes: ≤200 lines each
- Functions: ≤50 lines if possible

---

## Key Design Principles
1. **Single Responsibility**: Each module does one thing well
2. **No circular dependencies**: Unidirectional imports only
3. **Type hints**: All public APIs fully annotated
4. **Minimal external deps**: numpy, scipy only (matplotlib optional)
5. **Testable**: Functions accept/return simple types

---

## Adding New Modules
When adding functionality:
1. Update this document first (top-down design)
2. Choose existing module or create new one (if scope is distinct)
3. Update `src/__init__.py` exports
4. Add type hints + docstrings
5. Create unit tests in `tests/`

---

## Common Entry Points
- **Script usage**: `python -m src.trajectory /path/to/dump.lammpstrj`
- **API usage**: `from src import read_dump; traj = read_dump(...)`
- **Examples**: See `examples/` folder for typical workflows
