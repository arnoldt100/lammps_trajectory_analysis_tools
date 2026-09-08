# MD Parameters Option Contract Plan

## Task

### Specifying the Molecular Dynamics Simulation Parameters

Add a command line option that specifies the name of the JSON file that
contains the molecular dynamics simulation parameters. 

The option must:

- The option is mandatory.
- Adhere to a JSON schema that has file name `md_params.schema.json`, or raise an error.
- Make the JSON file path/name available to the data writers. The data writers will write the
MD parameters to the appropriate output file.

## MD Parameter Option

Add the following to the FCC subparser in `lop_sf_fcc_cli_parser.py`:

```text
--md-params-json
```

Recommended destination and property name:

```text
md_params_json
```

Example:

```
lammps_analysis_tool ... --md-params-json md.params.json ...
```


## Propagation To `LopSfFcc`


The current calculation entry point is `LopSfFcc.__call__`, which receives a
`CLILopSfFcc` instance. Read the configured value from the CLI object at the
calculation boundary:

```python
md_params_json = command_line_arguments.md_params_json
```

## Testing Plan

Add tests to CLI contract

1. Omitting the option produces raises an error.
4. A file name of empty string or blanks must raise an error.
2. If the JSON file doesn't exist an error is raised.
2. If the JSON file isn't readable an error is raised.
3. The JSON file adheres to `md_params.schema.json` or an error is raised.

## Documentation Updates on Implementation of Plan


### In progress of adding `--md-params-json` to `CLILopSfFcc`.
