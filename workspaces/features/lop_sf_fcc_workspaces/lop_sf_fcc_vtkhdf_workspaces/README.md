# LOP SF FCC VTKHDF Writer Feature Workspace

## Feature Goal
Owns the responsibility of writing an VTKHDF file for viewing the trajectory
data the concrete trajectory writer HDF5LopSfFccTrajectoryDataWriter produces.

The concrete writer VTKHDFLopSfFccTrajectoryDataWriter creates a 
VTKHDF animation file. 

## Structural Boundaries.

### Owned production code 

```text
/src/lammps_trajectory_analysis_tools/lib/lop_sf_fcc/vtkhdf_writer
 ├── __init__.py  # lop_sf_fcc_vtkhdf_animation_writer_factory
 │                # single registration site + exports
 ├── lop_sf_fcc_vtkhdf_animation_writer.py # The concrete VTKHDF writer for HDF5 LOP FCC trajectories.
 │                                         # LopSfFccVtkhdAnimationWriter
 ├── lop_sf_fcc_vtkhdf_animation_writer_value_object.py # LopSfFccVtkhdAnimationWriterValueObject
 ├── lop_sf_fcc_vtkhdf_animation_writer_value_object_interface.py # LopSfFccVtkhdAnimationWriterValueObjectInterface
 ├── lop_sf_fcc_vtkhdf_animation_writer_value_object_behavior.py # LopSfFccVtkhdAnimationWriterValueObjectBehavior
 ├── lop_sf_fcc_vtkhdf_animation_writer_builder.py # The concrete builders
 └── lop_sf_fcc_vtkhdf_animation_writer_builder_keys.py # The concrete builder keys.
```


```
### Centralized tests 
Per the project-wide centralized testing rule, tests never
live inside the feature workspace or `src`):

### Standing plan and status (this folder):

- `top_level_plan.md` — 

- `context.md` — current implementation status snapshot; must be updated
  whenever the feature's behavior, data flow, or boundaries change.


## External Dependencies

## Cross-Feature Dependencies

Consumers of this feature:

## Related Documents

- Standing plan: [top_level_plan.md](top_level_plan.md)
- Status snapshot: [context.md](context.md)
- Collection rules: [../top_level_plan.md](../top_level_plan.md)
- Project-wide rules: [../../../top_level_plan.md](../../../top_level_plan.md)
- Command-line contract: [../../command_line_workspaces/top_level_plan.md](../../command_line_workspaces/top_level_plan.md)
