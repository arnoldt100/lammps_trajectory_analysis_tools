# Top Level Plan - Density Plot Profile VTKHDF Writer.

This is the canonical standing plan for the 3D desity plot profile animation
writer. It inherits the project-wide rules from
[../../top_level_plan.md](../../top_level_plan.md).

## Objective

This feature responsibility is to write VTKHDF aninmated mass 3D density plots of
the persisted LAMMPS DCD trajectory files. This feature iw prohibited from altering the LAMMPS
DCD trajectory files.

The feature will leverage the MDAnalysis class "MDAnalysis.analysis.density.DensityAnalysis" to
calculate the 3D volumetric plot.

## Command Line Usage
The command line invocation will be as follows:

```
    uv run lammps_analysis_tool.py 3d_volumetric_density_plot \
         --trajectory <trajectory_filename_text> \
         --psf <psf_filename_text> \
         --timeunits <imeunits_text> \
         --dt <dt_text> \
         --parallel-threads=${nm_threads}
         --output-density-plot <output_filename_text> \
         --atomgroup <atom_group_text> \
         --delta <delta_text> \
         --xdim <xdim_text> --ydim <ydim_text> --zdim <zdim_text> \
        --gridcenter < x_grid_center y_grid_center z_grid_center> 
```

where lammps_analysis_tool.py is the main Python script,
the option `3d_volumetric_density_plot` creates a subparser whose 
subcommand calculates the 3d density volumetric plot.


| Option | Description | Optional Option | Default Value |
| ---    |    ---      |    ---          |    ---                           |
| --trajectory |   The name of the DCD file (str) | Mandatory |  --         | 
| --output-density-plot |   The name of the output file (str)  | Mandatory |  --  | 
| --psf |   The name of the PSF file (str)  | Mandatory |  --                     | 
| --timeunits |   The units for each time step (str)   | Mandatory |  -- | 
| --dt |   The magnitude for each time step (float)   | Mandatory |  --            | 
| --parallel-threads |   The number of parallel workers (int)   | Optional |  1   | 
| --atomgroup |   The  group of atoms (str)   | Optional |  all   | 
| --delta | The bin size for the density grid in angstroms, (float)  | Optional |  No default value  | 
| --gridcenter | User defined center of grid (3 floats)   | Optional |  No default value  | 
| --xdim | User defined x dimension edge, (float)  | Optional |  No default value  | 
| --ydim | User defined y dimension edge, (float)  | Optional |  No default value  | 
| --zdim | User defined z dimension edge, (float)  | Optional |  No default value  | 

The options `--xdim`, `--ydim` and `--zdim` are mutually exclusive to option `--gridcenter`. Use 
either `--gridcenter` or `--xdim`, `--ydim` and `--zdim`. 

## Paralleliztion Desing Rules.

Deferred for now.

## Shared Design Rules

## Testing Rules

- Tests are centralized under `tests/`, mirroring the feature structure; no
  tests live inside a feature workspace or `src`.
- Every child feature lists its owned test files in its README.
- End-to-end and backend-matrix tests cross child boundaries deliberately;
  unit tests should stay within one child's contract.

# Documentation Rules

- Each child feature keeps its own `README.md` (goal, boundaries,
  dependencies), `context.md` (status snapshot), and `top_level_plan.md`
  (standing rules and contract), and must link back to this plan.
- Cross-feature consumers and dependencies are recorded in both features'
  READMEs.
- Completed migrations are recorded in the child plan's migration log, not
  left as open work items.

## Feature Index

See [context.md](context.md) for the current list of child features and
their status.

