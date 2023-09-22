from hooks.gen_docs.gen_docs_env_vars import collect_fields
from tests.utils.resources.nested_base_settings import ParentSettings


class TestEnvDocGen:
    def test_collect_fields(self):
        collected_field_defaults = [
            "not_nested_field",
            "attr",
            Ellipsis,
        ]
        collected_defaults = [
            field.field_info.default for field in collect_fields(ParentSettings)
        ]
        assert collected_defaults == collected_field_defaults
