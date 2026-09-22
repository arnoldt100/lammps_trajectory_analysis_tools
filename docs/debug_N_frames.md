# Debug N Frames Plan

## Goal
Read env var `LTAT_DEBUG_PLOT_FRAMES` (integer). If positive N, only compute
the first N trajectory frames (via slicing the MDAnalysis trajectory reader,
so the Universe truly only iterates N frames). If non-positive, or unset,
compute all frames. If set but not a valid integer, raise a Python exception
and stop the program. If N > total frames available, raise an exception
(invalid input) rather than silently clipping.

## Target file
`src/lammps_trajectory_analysis_tools/lib/lop_sf_fcc/lop_sf_fcc.py`

## Decisions (confirmed with user)
- Slice `universe.trajectory` (e.g. `universe.trajectory[:n]`), not a manual
  loop-counter break. Remove the existing hardcoded
  `max_trajectories_to_compute = 10` and the `if counter == max_trajectories_to_compute: break`
  in `LopSfFcc.__call__`.
- Env var unset -> behave like non-positive (compute all frames).
- Env var set but non-integer string -> raise a plain Python exception
  (e.g. `ValueError`) with a descriptive message; let it propagate/crash
  the program (no manual sys.exit/try-except swallowing).
- Env var positive N > total available frames in the trajectory -> raise an
  exception (treat as invalid input), do not silently clip.
- Keep the env-var-reading helper local to `lop_sf_fcc.py` (do not add to
  `lop_sf_fcc_cli_parser.py`, which is unrelated/currently a stub for this
  purpose).

## Steps

1. Add a private helper `_read_debug_plot_frames_env_var() -> Optional[int]`
   in `lop_sf_fcc.py`:
   - Reads `os.environ.get("LTAT_DEBUG_PLOT_FRAMES")`.
   - If unset/None, return `None` (meaning "all frames").
   - Try `int(value)`; on `ValueError`, raise `ValueError` with message
     naming the env var and the invalid value.
   - If parsed value <= 0, return `None` (meaning "all frames").
   - Otherwise return the positive int N.

2. Add a private helper `_resolve_nm_frames_to_compute(total_frames: int, debug_plot_frames: Optional[int]) -> int`:
   - If `debug_plot_frames is None`, return `total_frames`.
   - If `debug_plot_frames > total_frames`, raise `ValueError` (N exceeds
     available frames) with a descriptive message including both values.
   - Else return `debug_plot_frames`.

3. Modify `_set_universe_attributes(command_line_arguments)`:
   - After building `my_universe` and computing `nm_frames = my_universe.trajectory.n_frames` (total frames), call the two new helpers to compute the
     resolved `nm_frames` to actually compute (this becomes the value stored
     on `self._nm_frames` used elsewhere for reporting/timer).
   - Return the resolved `nm_frames` (rename total vs resolved clearly, e.g.
     `total_nm_frames` vs `nm_frames`).

4. Modify `LopSfFcc.__call__`:
   - Remove `max_trajectories_to_compute = 10` hardcoded value; use
     `self._nm_frames` (now correctly reflecting the debug-limited or full
     frame count) as the timer's max-iteration parameter passed to
     `timer_object_factory.build(...)`.
   - Replace `for ts in self._universe.trajectory:` with iteration over a
     slice: `for ts in self._universe.trajectory[:self._nm_frames]:`.
   - Remove the `if counter == max_trajectories_to_compute: break` block
     entirely — the slice bounds the loop naturally.

5. No changes needed to `data_writer` — it resizes/grows dynamically per
   `append_trajectory_frames` calls (verified: no dependency on total frame
   count upfront), so writing fewer frames than originally configured is
   safe.

## Verification
1. Run existing test suite for `lop_sf_fcc` module:
   `pytest tests/test_lop_sf_fcc.py tests/test_lop_sf_fcc_Ar4Version0.py tests/test_lop_sf_fcc_cli_parser.py -q`
2. Add/update unit tests (if a tests file for this module's private helpers
   exists or is warranted) covering:
   - `LTAT_DEBUG_PLOT_FRAMES` unset -> all frames computed.
   - Set to a positive N < total frames -> only N frames computed/written.
   - Set to 0 or negative -> all frames computed.
   - Set to a non-integer string (e.g. "abc") -> raises `ValueError`.
   - Set to positive N > total available frames -> raises `ValueError`.
3. Manually confirm via existing example
   (`examples/example-lop_sf_fcc-ar_box_small/run_lop_sf_fcc.sh`) with
   `LTAT_DEBUG_PLOT_FRAMES=2` that output HDF5 file contains exactly 2
   frames.

## Scope boundaries
- Only touches `lop_sf_fcc.py`; no changes to `lop_sf_fcc_cli_parser.py`,
  `universe.py`, or data writer classes.
- Does not add a new CLI flag — env var is read directly, consistent with
  how `LTAT_DEBUG_PLOT_FRAMES` is already exported in
  `NimzoIndian.env.sh`/`RuyLopez.env.sh`.


