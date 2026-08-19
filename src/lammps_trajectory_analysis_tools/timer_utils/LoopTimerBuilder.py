#! /usr/bin/env python3
#
# AI assistance: OpenAI ChatGPT via API, model family GPT-5, accessed 2026-08-13.
# Contribution: generated initial code comments/docstrings.
# Status: output was reviewed, modified, and validated by the author.

"""The builder for the LoopTimer class.

This module provides a small callable builder wrapper around ``LoopTimer``.
It is useful when a registry, factory table, or plugin system needs a
callable object associated with a known key.

This module provides the following public members:
    LoopTimerBuilderKey
    LoopTimerBuilder
"""

# ----------
# Python standard library imports
# ----------
from typing import Any

# ----------
# Local library imports
# ----------
# Import the concrete class that this builder creates.
from .LoopTimer import LoopTimer

# ----------
# Public members
# ----------

class LoopTimerBuilder:
    """The builder of LoopTimer objects.

    A callable class; when called, it builds a LoopTimer object. See
    the LoopTimer class for the permitted arguments.
    """

    def __call__(self, *args: Any, **kwargs: Any) -> LoopTimer:
        """Build and return a LoopTimer from forwarded constructor arguments."""
        return LoopTimer(*args, **kwargs)

# Public identifier that can be used as a registry or lookup key for this
# builder. For example, a factory dictionary might map this string to the
# LoopTimerBuilder class or to an instance of it.
#
# Keeping the key in a named constant avoids repeating string literals and
# reduces the chance of typographical errors elsewhere in the codebase.
LoopTimerBuilderKey = "LoopTimer"

def _main() -> None:
    # Module entry point used only when this file is executed as a script.
    #
    # The module is primarily intended to be imported, not run directly.
    # The empty implementation is kept as a placeholder for possible future
    # manual testing or debugging support.
    pass

# ----------
# Private members
# ----------

# Standard Python script guard.
#
# This ensures _main() is called only when the module is run directly:
#
#     python LoopTimerBuilder.py
#
# and not when the module is imported by another module.
if __name__ == "__main__":
    _main()

