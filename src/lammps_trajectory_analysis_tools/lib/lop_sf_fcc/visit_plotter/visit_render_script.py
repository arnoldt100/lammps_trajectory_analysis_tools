#! /usr/bin/env python3
"""VisIt-side render script source for the LOP SF FCC time series.

This module provides the following public members:
    RENDER_SCRIPT: The Python source executed by ``visit -cli -nowin -s``.
    render_script_text: Return the render script source (for tests/writing).

The script runs inside VisIt's bundled Python (numpy only, no h5py) and is
deliberately self-contained: it takes the master ``.xdmf`` path, an output
directory, and a fixed ``[min, max]`` pseudocolor range, then writes one PNG
per timestep.
"""

# ----------
# Public members
# ----------

"""The VisIt-side render script.

Positional arguments (``sys.argv``):
    1. master ``.xdmf`` path
    2. output directory for the per-frame PNGs
    3. global pseudocolor minimum
    4. global pseudocolor maximum

The pseudocolor range is fixed across all frames so that colors are
comparable frame to frame. ``SaveWindowAttributes.format`` takes an enum
index (``s.PNG``), not a string; the point glyph enum lives on the
attributes instance (``p.Point``), not on the class.
"""
RENDER_SCRIPT = '''\
import os
import sys

import visit


def _main() -> int:
    xdmf_path = sys.argv[1]
    out_dir = os.path.abspath(sys.argv[2])
    color_min = float(sys.argv[3])
    color_max = float(sys.argv[4])

    os.makedirs(out_dir, exist_ok=True)

    visit.OpenDatabase(xdmf_path)
    visit.AddPlot("Pseudocolor", "lop_sf_fcc")
    plot = visit.PseudocolorAttributes()
    plot.pointType = plot.Point
    plot.pointSize = 0.2
    plot.minFlag = True
    plot.maxFlag = True
    plot.min = color_min
    plot.max = color_max
    visit.SetPlotOptions(plot)
    visit.DrawPlots()

    save = visit.SaveWindowAttributes()
    save.outputToCurrentDirectory = 0
    save.outputDirectory = out_dir
    save.family = 0
    save.format = save.PNG

    n_states = visit.TimeSliderGetNStates()
    print("NUM_STATES", n_states)
    for state in range(n_states):
        visit.SetTimeSliderState(state)
        save.fileName = "frame_%04d" % state
        visit.SetSaveWindowAttributes(save)
        visit.SaveWindow()
    print("RENDER_OK")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
'''


def render_script_text() -> str:
    """Return the VisIt-side render script source.

    Returns:
        The render script as a Python source string.
    """
    return RENDER_SCRIPT


# ----------
# Private members
# ----------


def _main() -> None:
    return


if __name__ == "__main__":
    _main()
