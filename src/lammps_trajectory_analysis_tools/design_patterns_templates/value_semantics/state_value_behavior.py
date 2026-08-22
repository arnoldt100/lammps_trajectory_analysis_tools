"""Common behavior for state-value templates."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from .value_object_helpers import _hashable_state


class StateValueBehavior:
    """Provide the package-wide behavior used by state-value templates.

    ``dummy_method`` is an illustrative placeholder that users can replace
    when adapting the template to their own domain behavior.

    No production module currently constructs this class; it is exercised only
    by tests/design_patterns_templates/value_semantics/test_value_object.py,
    which instantiates, subclasses, and monkeypatches it as the default
    behavior template.
    """

    def copy_state(self, state: Any) -> Any:
        """Return an independent copy of state."""
        return deepcopy(state)

    def validate_state(self, state: Any) -> None:
        """Delegate validation to an owned object when it provides it."""
        validator = getattr(state, "validate_state", None)
        if validator is not None:
            validator()
            return
        if isinstance(state, Mapping) and any(
            not isinstance(name, str) or not name for name in state
        ):
            raise ValueError("state field names must be non-empty strings")

    def replace_state(self, state: Any, changes: Any) -> Any:
        """Delegate replacement to an owned object or update a mapping."""
        replacer = getattr(state, "replace", None)
        if replacer is not None:
            return replacer(changes)
        if not isinstance(state, Mapping) or not isinstance(changes, Mapping):
            raise TypeError("default behavior requires mapping state and changes")
        updated_state = dict(state)
        updated_state.update(changes)
        return updated_state

    def update_state(self, state: Any, changes: Any) -> Any:
        """Delegate in-place update to an owned object or update a mapping."""
        updater = getattr(state, "update", None)
        if updater is not None and not isinstance(state, Mapping):
            updated_state = self.copy_state(state)
            updated_state.update(changes)
            return updated_state
        return self.replace_state(state, changes)

    def states_equal(self, left: Any, right: Any) -> bool:
        """Compare state values using ordinary equality."""
        return left == right

    def state_repr(self, state: Any) -> str:
        """Return the ordinary debugging representation of state."""
        return repr(state)

    def hash_state(self, state: Any) -> int:
        """Return a hash for mapping or otherwise hashable state."""
        if isinstance(state, dict):
            return hash(_hashable_state(state))
        return hash(state)

    def dummy_method(
        self,
        owned_object: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Demonstrate behavior delegated for an owned object."""
        return owned_object.dummy_method(*args, **kwargs)
