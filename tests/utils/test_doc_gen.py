from pathlib import Path
from unittest.mock import patch
from hooks.gen_docs.gen_docs_env_vars import collect_fields, csv_append_env_var, write_title_to_dotenv_file, EnvVarAttrs, append_csv_to_dotenv_file, write_csv_to_md_file, fill_csv_pipeline_config
from tests.utils.resources.nested_base_settings import ParentSettings
import pytest

class TestEnvDocGen:
    def test_collect_fields(self):
        expected = [
            "not_nested_field",
            "attr",
            Ellipsis,
            Ellipsis,
        ]
        actual = [
            field.field_info.default for field in collect_fields(ParentSettings)
        ]
        assert actual == expected

    @pytest.mark.parametrize(
        ["var_name", "default_value", "description", "extra_args", "expected_outcome"],
        [
            pytest.param(
                "var_name",
                "default_value",
                "description",
                (),
                "var_name,default_value,False,description",
                id="String desc"
            ),
            pytest.param(
                "var_name",
                "default_value",
                ["description", " description"],
                (),
                "var_name,default_value,False,description description",
                id="List desc"
            ),
            pytest.param(
                "var_name",
                "default_value",
                "description",
                ("extra arg 1", "extra arg 2"), 
                "var_name,default_value,False,description,extra arg 1,extra arg 2",
                id="Extra args"
            ),
            pytest.param(
                "var_name",
                "default_value",
                None,
                (),
                "var_name,default_value,False,",
                id="No desc"
            ),
        ],
    )
    def test_csv_append_env_var(self, tmp_path, var_name, default_value, description, extra_args, expected_outcome):
        target: Path = tmp_path / "target.csv"
        csv_append_env_var(target, var_name, default_value, description, *extra_args)
        with target.open() as t:
            assert t.read() == expected_outcome + "\n"

    def test_write_title_to_dotenv_file(self, tmp_path):
        target: Path = tmp_path / "target.ENV"
        write_title_to_dotenv_file(target, "title", "description of length 72"*3)
        with target.open() as t:
            assert t.read() == (
                "# title\n"
                "#\n"
                "# " + "description of length 72description of length 72description of"+ "\n"
                "# length 72" + "\n"
                "#\n"
            )

    @pytest.mark.parametrize(
        ["name", "default", "required", "description", "setting_name", "expected"],
        [
            pytest.param(
                "NAME",
                "default",
                "True",
                "description",
                "setting_name",
                "# setting_name\n"
                "# description\n"
                "NAME=default\n",
                id="default exists, required"
            ),
            pytest.param(
                "NAME",
                "",
                "True",
                "description",
                "setting_name",
                "# setting_name\n"
                "# description\n"
                "NAME # No default value, required\n",
                id="default not exists, required"
            ),
            pytest.param(
                "NAME",
                "default",
                "False",
                "description",
                "setting_name",
                "# setting_name\n"
                "# description\n"
                "NAME=default\n",
                id="default exists, not required"
            ),
            pytest.param(
                "NAME",
                "",
                "False",
                "description",
                "setting_name",
                "# setting_name\n"
                "# description\n"
                "NAME # No default value, not required\n",
                id="default not exists, not required"
            ),
            pytest.param(
                "NAME",
                "default",
                "True",
                "description",
                "",
                "# description\n"
                "NAME=default\n",
                id="no setting name"
            ),
        ],
    )
    def test_append_csv_to_dotenv_file(self, tmp_path, name, default, required, description, setting_name, expected):
        source: Path = tmp_path / "source.csv"
        target: Path = tmp_path / "target.env"
        csv_record = [name, default, required, description]
        csv_column_names = [EnvVarAttrs.NAME, EnvVarAttrs.DEFAULT_VALUE, EnvVarAttrs.REQUIRED, EnvVarAttrs.DESCRIPTION]
        with source.open("w+", newline="") as f:
            if setting_name is not None:
                csv_record.append(setting_name)
                csv_column_names.append(EnvVarAttrs.CORRESPONDING_SETTING_NAME)
            f.write(",".join(csv_column_names)+ "\n")
            f.write(",".join(csv_record))
        append_csv_to_dotenv_file(source, target)
        with target.open("r", newline="") as f:
            assert f.read() == expected

    @pytest.mark.parametrize(
        ["title", "description", "heading", "expected"],
        [
            pytest.param(
                "title", "description", "###", "### title\n\ndescription\n\n", id="all provided, default heading",
            ),
            pytest.param(
                "title", "description", "##", "## title\n\ndescription\n\n", id="all provided, different heading",
            ),
            pytest.param(
                "title", "description", "", "title\n\ndescription\n\n", id="all provided, heading empty str",
            ),
            pytest.param(
                "title", "description", None, "title\n\ndescription\n\n", id="all provided, heading is None",
            ),
            pytest.param(
                None, "description", "###", "description\n\n", id="no title",
            ),
            pytest.param(
                "title", None, "###", "### title\n\n", id="no description",
            ),
        ]
    )
    def test_write_csv_to_md_file(self, tmp_path, title, description, heading, expected):
        source: Path = tmp_path / "source.csv"
        target: Path = tmp_path / "target.env"
        csv_record = ["NAME", "default", "True", "description", "setting_name"]
        csv_column_names = [EnvVarAttrs.NAME, EnvVarAttrs.DEFAULT_VALUE, EnvVarAttrs.REQUIRED, EnvVarAttrs.DESCRIPTION, EnvVarAttrs.CORRESPONDING_SETTING_NAME]
        with source.open("w+", newline="") as f:
            f.write(",".join(csv_column_names)+ "\n")
            f.write(",".join(csv_record))
        write_csv_to_md_file(source, target, title, description, heading)
        with target.open("r", newline="") as f:
            assert f.read() == expected + str(
                "|Name|Default Value|Required|Description|Setting name|\n"
                "|----|-------------|--------|-----------|------------|\n"
                "|NAME|default      |True    |description|setting_name|\n",
            )
