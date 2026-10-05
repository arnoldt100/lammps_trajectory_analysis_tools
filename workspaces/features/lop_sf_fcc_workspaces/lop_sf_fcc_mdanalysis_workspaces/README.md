# LOP SF FCC MDAnalysis Backend Feature Workspace

## Feature Goal

Own the physics of the FCC structure-factor local order parameter: the
`LOP_SF_FCC` MDAnalysis analysis class (an `AnalysisBase` subclass following
the MDAnalysis guidelines) and the wavevector/order-parameter helper
functions that are the single source of the calculation.

For atom $j$ with $N_j$ neighbors within `cutoff` and the six FCC wavevectors
$\mathbf{q}$:

$$S_j = \left| \frac{1}{6 N_j} \sum_{k \in N_j} \sum_{\mathbf{q}}
e^{i \mathbf{q} \cdot \mathbf{r}_{jk}} \right|^2$$

Atoms with no neighbors have $S_j = 0$.

## Structural Boundaries

Owned production code (this feature's only production scope):

```text
src/lammps_trajectory_analysis_tools/lib/lop_sf_fcc/lop_sf_fcc_mdanalysis.py
  LOP_SF_FCC                                        # AnalysisBase subclass
  create_primitive_lattice_vectors                  # FCC primitive lattice vectors
  create_reciprocal_lattice_vectors                 # reciprocal lattice vectors
  create_wavevectors                                # the six FCC wavevectors
  calculate_lop_fcc_atom_pair_exp_terms             # exp(i q·dr) sum for one pair
  calculate_sf_fcc_atom_order_parameter_no_coeffs   # per-atom exp(i q·r) sums,
                                                    # neighbor counts
  calculate_sf_fcc_atom_order_parameter_with_coeffs # per-atom normalized S_j
```

Centralized tests (per the project-wide centralized testing rule, tests never
live inside the feature workspace or `src`):

```text
tests/test_lop_sf_fcc_mdanalysis.py     # class contract + parallel matrix
tests/test_lop_sf_fcc_Ar4Version0.py    # per-atom values vs. Ar4 fixture
tests/test_lop_sf_fcc.py                # wavevector tests (shared with the
                                        # lop_sf_fcc feature)
tests/input_files/Ar4Version0.py        # shared Ar4 fixture
```

Standing plan and status (this folder):

- `top_level_plan.md` — design rules, the as-built backend contract, test
  plan, non-goals, acceptance criteria, and the completed migration log
  (including benchmark results).
- `context.md` — current implementation status snapshot; must be updated
  whenever the feature's behavior, data flow, or boundaries change.

Feature-specific logic must not leak into the global scope: the calculation
helpers are used only through `LOP_SF_FCC` and tests; nothing outside this
module performs the order-parameter math.

## External Dependencies

- **MDAnalysis** (`AnalysisBase`, `ResultsGroup`, `AtomGroup`) — the backend
  itself; MDAnalysis ≥ 2.8 semantics, project uses 2.10.0. All MDAnalysis
  imports stay in this module and the `integrations/mdanalysis` package.
- **Accumulator package** (`accumulator/`): per-frame accumulators are built
  through `array_accumulator_builder_registry`.
- **MDAnalysis integration package** (`integrations/mdanalysis/`):
  `calculate_atom_pairs` for neighbor searches.
- **Data types** (`lib/data_types.py`): `LatticeVectors`.
- **Data writer utils** (`data_writer_utils/`): the optional
  `LopSfFccTrajectoryWriterValueObjectInterface` used by `_conclude`.

## Cross-Feature Dependencies

Consumers of this feature:

- **lop_sf_fcc orchestrator** (`lop_sf_fcc_orchestrator_workspaces`): constructs
  `LOP_SF_FCC` via `_set_lop_sf_fcc_attribute` and drives it with
  `run(stop=..., **run_kwargs)`. See
  [../lop_sf_fcc_orchestrator_workspaces/README.md](../lop_sf_fcc_orchestrator_workspaces/README.md).

Dependencies of this feature — each is documented in both workspaces:

- **lop_sf_fcc orchestrator** (`lop_sf_fcc_orchestrator_workspaces`): supplies the
  atomgroup, physics parameters, writer value object, and backend selection.
- **Accumulator builder wiring** (`accumulator/`): per-frame accumulators via
  the registry (see the accumulator refactor plans under `docs/`).

## Related Documents

- Standing plan: [top_level_plan.md](top_level_plan.md)
- Status snapshot: [context.md](context.md)
- Collection rules: [../top_level_plan.md](../top_level_plan.md)
- Project-wide rules: [../../../top_level_plan.md](../../../top_level_plan.md)
- Orchestrator contract:
  [../lop_sf_fcc_orchestrator_workspaces/top_level_plan.md](../lop_sf_fcc_orchestrator_workspaces/top_level_plan.md)
