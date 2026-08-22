# Value semantics package usage guide

This package is intentionally written as a reusable template. In many projects, the simplest path is to copy the package, rename it to match your domain, and then adapt its behavior and owned state types to your real model.

The purpose of the package is not to be the final domain model itself. It is a small pattern library for:

- a value-object wrapper that owns state
- a protocol for how state is copied, validated, compared, and hashed
- a concrete owned object that represents the data being wrapped
- a placeholder `dummy_method` extension point for adding real domain behavior

The template in this repo lives at:

- `src/lammps_trajectory_analysis_tools/design_patterns_templates/value_semantics/`

A user project should generally copy that directory into a domain-specific package, for example:

- `src/my_project/domain/value_semantics/`
- or `src/my_project/values/`

and then rename the classes and package names to fit the target domain.

---

## 1. Copy and rename the package

Use this checklist when adapting the template:

1. Copy the entire `value_semantics` package directory.
2. Rename the package folder to a domain-appropriate name.
3. Rename the public classes in the copied files.
4. Update imports in any code that refers to the old package path.
5. Replace generic docstrings and examples with domain-specific language.
6. Replace the placeholder `dummy_method` behavior with actual domain operations.

A typical rename would look like this:

- `StateValueObjectImmutable` -> `PriceImmutable` or `OrderValue`
- `StateValueObjectMutable` -> `PriceMutable` or `OrderStateValue`
- `ValueObjectInterface` -> `DomainValueObjectInterface`
- `StateValueBehaviorProtocol` -> `PriceBehaviorProtocol`

The key idea is to preserve the pattern while making the names represent the actual business concept being modeled.

---

## 2. Files to modify when creating a custom copy

The template consists of a few files that usually need revision:

### Package exports

File: `__init__.py`

This file defines what the package exposes to callers. Update it to export the renamed classes and helper functions.

Typical edits:

- rename exported classes
- keep or remove helper functions as needed
- update `__all__`
- fix any import paths after moving the package

Example:

```python
from .state_value_object_immutable import PriceImmutable
from .state_value_object_mutable import PriceMutable
from .protocols import PriceBehaviorProtocol
from .value_object_interface import DomainValueObjectInterface

__all__ = [
    "PriceImmutable",
    "PriceMutable",
    "PriceBehaviorProtocol",
    "DomainValueObjectInterface",
]
```

### Behavior contract

File: `protocols.py`

This file defines the protocol used by the wrapper objects. Update the names and docstrings to match your domain concept.

The protocol is the contract that every custom behavior object must satisfy. The user-defined behavior object must implement methods such as:

- `copy_state(state)`
- `validate_state(state)`
- `replace_state(state, changes)`
- `update_state(state, changes)`
- `states_equal(left, right)`
- `state_repr(state)`
- `hash_state(state)`
- `dummy_method(owned_object, *args, **kwargs)`

The placeholder `dummy_method` is explicitly meant to be replaced or reinterpreted by the user during adaptation.

### Value object interface

File: `value_object_interface.py`

This file defines the abstract API that all concrete value objects must follow. Usually this file requires minimal changes unless the project wants a different public contract.

Typical adjustments:

- rename the abstract base class
- change method names if the project wants semantics beyond `replace`
- keep `state` as the value-bearing surface unless the domain wants a different representation

### Immutable and mutable wrappers

Files:

- `state_value_object_immutable.py`
- `state_value_object_mutable.py`

These are the concrete templates users will most often customize.

Update them to:

- rename the class names
- update docstrings to the domain concept
- ensure any behavior-specific method names still match the protocol
- keep the `replace` behavior for immutable objects
- keep the `update` behavior for mutable objects
- decide whether `__hash__` should be supported or disabled depending on the domain

The wrappers should remain thin adapters around the behavior object and the concrete owned state implementation.

### Shared helper functions

File: `value_object_behaviors.py`

This is where package-level helpers live. It is a useful place to add domain-wide operations that should work on the value-object wrappers without repeating logic in each class.

Common additions:

- `hash_state(value_object)`
- domain-specific serializers
- comparison helpers
- validation helpers
- shared operation wrappers that call the value object or the underlying state

### Validation definitions

File: `validation.py`

This file contains the validation exception used by the package. In a project-specific copy, it is usually enough to keep the same exception pattern, but rename it if the domain uses a different validation vocabulary.

Example:

```python
class PriceValidationError(ValueError):
    """Raised when a value object cannot satisfy its invariants."""
```

---

## 3. How to add a custom behavior

The behavior object is the central customization point. It is the object that knows how to copy, validate, compare, and represent the domain state.

Create a class that satisfies `StateValueBehaviorProtocol` and keep it close to the copied package. For example:

```python
from copy import deepcopy
from typing import Any


class PriceBehavior:
    def copy_state(self, state: Any) -> Any:
        return deepcopy(state)

    def validate_state(self, state: Any) -> None:
        if state.quantity <= 0:
            raise ValueError("quantity must be positive")

    def replace_state(self, state: Any, changes: Any) -> Any:
        updated = dict(state)
        updated.update(changes)
        return updated

    def update_state(self, state: Any, changes: Any) -> Any:
        return self.replace_state(state, changes)

    def states_equal(self, left: Any, right: Any) -> bool:
        return left == right

    def state_repr(self, state: Any) -> str:
        return repr(state)

    def hash_state(self, state: Any) -> int:
        return hash(tuple(sorted(state.items())))

    def dummy_method(self, owned_object: Any, *args: Any, **kwargs: Any) -> Any:
        return owned_object.calculate_total(*args, **kwargs)
```

This behavior object is then passed into the concrete wrappers as the implementation strategy.

### Design intent

The behavior object separates:

- the owned object (the concrete state-holder)
- the value wrapper (the immutable/mutable shell)
- the domain rules (validation, equality, replacement logic)

This is useful when a project wants multiple types of value wrappers with a shared domain representation but different validation semantics.

---

## 4. What changes are needed in concrete state implementations

The concrete state object is the class that actually owns the data. In the template, these are examples such as:

- `ConcreteStateImplementation`
- `NumericStateImplementation`

These should be replaced by real domain-owned objects.

Each concrete state implementation should provide the following minimum surface:

```python
class OrderState:
    def validate_state(self) -> None:
        ...

    def replace(self, changes):
        ...

    def update(self, changes):
        ...

    def dummy_method(self, *args, **kwargs):
        ...
```

### Important rules

1. The state object should own its own private data.
2. It should validate its invariants before being accepted.
3. `replace` should return a new object, not mutate the current one.
4. `update` should mutate in place for mutable objects.
5. `dummy_method` should be renamed or replaced with real domain actions.

A state implementation is not the value wrapper itself; it is the underlying representation being wrapped.

For example, if the project models a price, the owned object may be something like:

```python
class PriceState:
    def __init__(self, amount: float, currency: str):
        self.amount = amount
        self.currency = currency

    def validate_state(self) -> None:
        if self.amount < 0:
            raise ValueError("amount must be non-negative")

    def replace(self, changes):
        return type(self)(**changes)

    def update(self, changes):
        for key, value in changes.items():
            setattr(self, key, value)

    def dummy_method(self):
        print(f"{self.amount} {self.currency}")
```

---

## 5. What changes are needed in the concrete value objects

The value wrappers are the public objects users interact with most often. They should be renamed to match the domain and still obey the value-object pattern.

### Immutable value object pattern

The immutable wrapper should:

- copy incoming state
- validate it during construction
- provide `state` and `state_implementations` accessors
- return a new object from `replace`
- make equality depend on the wrapped state
- support hashing when the underlying state is hashable

Example shape:

```python
class PriceImmutable(ValueObjectInterface):
    def __init__(self, state, behavior):
        self._behavior = behavior
        copied = behavior.copy_state(state)
        behavior.validate_state(copied)
        self._state_implementations = copied

    @property
    def state(self):
        return self._behavior.copy_state(self._state_implementations)

    def replace(self, changes):
        updated = self._behavior.replace_state(self._state_implementations, changes)
        return type(self)(updated, self._behavior)
```

### Mutable value object pattern

The mutable wrapper should:

- accept the same behavior contract
- validate state before storing
- support `update(changes)` with atomic validation semantics
- reject hashing because mutability breaks hash stability

Example:

```python
class PriceMutable(ValueObjectInterface):
    def __init__(self, state, behavior):
        self._behavior = behavior
        copied = behavior.copy_state(state)
        behavior.validate_state(copied)
        self._state_implementations = copied

    def update(self, changes):
        updated = self._behavior.update_state(self._state_implementations, changes)
        self._behavior.validate_state(updated)
        self._state_implementations = updated
```

This keeps the public object semantics stable while the owned object remains the real data-holder.

---

## 6. How to use the placeholder `dummy_method`

`dummy_method` is intentionally generic. It is a placeholder that reminds users to add domain-specific behavior at the contract boundary.

This is not a required behavior in the abstract sense; it is a template hook. In a real project, the user should replace it with the actual operations that matter for the domain.

Common replacements:

- `calculate_total()`
- `serialize()`
- `normalize()`
- `validate_business_rules()`
- `render()`
- `merge()`
- `apply_discount()`

The important rule is that the custom implementation should be expressed in terms of the owned state and should not mutate the wrapper state except through the approved replacement or update path.

---

## 7. Recommended adaptation workflow

1. Copy the `value_semantics` package to a project-specific directory.
2. Rename the package and exported classes.
3. Replace the example owned objects with real domain data objects.
4. Write a new behavior class for the domain state rules.
5. Replace `dummy_method` with real operations.
6. Update callers to import the renamed package.
7. Add tests for validation, replacement, equality, and immutability rules.

---

## 8. Summary

This package is designed to be copied and customized rather than used verbatim in a production domain model. The core pattern is:

- wrapped state lives in a concrete owned object
- the wrapper enforces value-object semantics
- the behavior object defines copy/validation/comparison logic
- the `dummy_method` hook shows where project-specific behavior belongs

If the project is modeling a real domain concept, the best next step is to rename the package and classes, swap in real state objects, and replace the placeholder behavior with domain logic that matches the actual business rules.
