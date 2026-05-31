# LAMMPS Trajectory Analysis Tools

Analysis and visualization toolkit for LAMMPS molecular dynamics simulations.

## Quick Start

```bash
pip install -r requirements.txt
```

```python
from src import read_dump, RadialDistributionFunction, plot_rdf

# Load trajectory
traj = read_dump("trajectory.dump")

# Compute RDF
rdf = RadialDistributionFunction(traj, cutoff=10.0)
r, g_r = rdf.compute()

# Visualize
plot_rdf((r, g_r), filename="rdf.png")
```

## Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** — Module structure and design
- **[docs/](docs/)** — Detailed documentation (coming soon)
- **[examples/](examples/)** — Example scripts

## Features

- 📊 Radial distribution function (RDF)
- 📈 Mean square displacement (MSD)
- 🌊 Structure factor S(q)
- 🎨 Trajectory visualization
- 💾 Multiple export formats (CSV, JSON, HDF5)
- Jupyter notebooks: Run the command "uv run --with jupyter jupyter lab"

## Requirements

- Python 3.8+
- numpy
- scipy
- matplotlib (optional, for plotting)

## License

See [LICENSE](LICENSE)
