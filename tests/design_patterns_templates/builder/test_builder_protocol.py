from lammps_trajectory_analysis_tools.design_patterns_templates.builder import SupportsBuild


class Product:
    pass


class CallableBuilder:
    def __call__(self, *args, **kwargs) -> Product:
        return Product()


def test_callable_satisfies_supports_build_protocol():
    builder = CallableBuilder()

    assert isinstance(builder, SupportsBuild)


def test_plain_function_satisfies_supports_build_protocol():
    def build_product(*args, **kwargs) -> Product:
        return Product()

    assert isinstance(build_product, SupportsBuild)


def test_non_callable_does_not_satisfy_supports_build_protocol():
    assert not isinstance(object(), SupportsBuild)
