import pytest

from lammps_trajectory_analysis_tools.design_patterns_templates.builder import (
    BuilderKeyError,
    BuilderRegistrationError,
    BuilderRegistry,
)


class Product:
    def __init__(self, *args, **kwargs) -> None:
        self.args = args
        self.kwargs = kwargs


def make_product(*args, **kwargs) -> Product:
    return Product(*args, **kwargs)


def test_build_returns_product_with_forwarded_arguments():
    registry = BuilderRegistry()
    registry.register_builder("product", make_product)

    result = registry.build("product", 1, 2, name="sample")

    assert isinstance(result, Product)
    assert result.args == (1, 2)
    assert result.kwargs == {"name": "sample"}


def test_build_with_unregistered_key_raises_builder_key_error():
    registry = BuilderRegistry()

    with pytest.raises(BuilderKeyError):
        registry.build("missing")


def test_register_builder_twice_raises_and_preserves_original():
    registry = BuilderRegistry()
    registry.register_builder("product", make_product)

    def other_builder(*args, **kwargs) -> Product:
        return Product("other", *args, **kwargs)

    with pytest.raises(BuilderRegistrationError):
        registry.register_builder("product", other_builder)

    result = registry.build("product")
    assert result.args == ()


def test_has_builder_and_keys_reflect_registration_state():
    registry = BuilderRegistry()

    assert not registry.has_builder("product")
    assert registry.keys() == frozenset()

    registry.register_builder("product", make_product)

    assert registry.has_builder("product")
    assert registry.keys() == frozenset({"product"})


def test_registries_do_not_share_state():
    first = BuilderRegistry()
    second = BuilderRegistry()

    first.register_builder("product", make_product)

    assert first.has_builder("product")
    assert not second.has_builder("product")
