"""Templates for implementing value-oriented domain objects."""

from .concrete_state_implementation import ConcreteStateImplementation
from .numeric_state_implementation import NumericStateImplementation
from .protocols import StateValueBehaviorProtocol, ValueSemantics
from .state_value_object_immutable import StateValueObjectImmutable
from .state_value_object_mutable import StateValueObjectMutable
from .validation import ValueValidationError
from .value_object_behaviors import hash_state, invoke_dummy_method
from .value_object_interface import ValueObjectInterface

__all__ = [
    "ConcreteStateImplementation",
    "NumericStateImplementation",
    "StateValueObjectImmutable",
    "StateValueObjectMutable",
    "StateValueBehaviorProtocol",
    "ValueObjectInterface",
    "ValueSemantics",
    "ValueValidationError",
    "hash_state",
    "invoke_dummy_method",
]
