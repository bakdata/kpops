import csv
import shutil
from pathlib import Path
from typing import Any

import pytest

from hooks import ROOT
from hooks.gen_docs import gen_docs_components
from hooks.gen_docs.gen_docs_env_vars import (
    EnvVarAttrs,
    append_csv_to_dotenv_file,
    csv_append_env_var,
    fill_csv_cli,
    write_csv_to_md_file,
    write_title_to_dotenv_file,
)


class TestEnvDocGen:
    @pytest.mark.parametrize(
        ("var_name", "default_value", "description", "extra_args", "expected_outcome"),
        [
            pytest.param(
                "var_name",
                "default_value",
                "description",
                (),
                "var_name,default_value,False,description",
                id="String desc",
            ),
            pytest.param(
                "var_name",
                "default_value",
                ["description", " description"],
                (),
                "var_name,default_value,False,description description",
                id="List desc",
            ),
            pytest.param(
                "var_name",
                "default_value",
                "description",
                ("extra arg 1", "extra arg 2"),
                "var_name,default_value,False,description,extra arg 1,extra arg 2",
                id="Extra args",
            ),
            pytest.param(
                "var_name",
                "default_value",
                None,
                (),
                "var_name,default_value,False,",
                id="No desc",
            ),
        ],
    )
    def test_csv_append_env_var(
        self,
        tmp_path: Path,
        var_name: str,
        default_value: Any,
        description: str | list[str] | None,
        extra_args: tuple[str, ...],
        expected_outcome: str,
    ) -> None:
        target = tmp_path / "target.csv"
        csv_append_env_var(target, var_name, default_value, description, *extra_args)
        with target.open() as t:
            assert (
                t.read().replace("\r\n", "\n").replace("\r", "\n")
                == expected_outcome + "\n"
            )

    def test_fill_csv_cli(self, tmp_path: Path) -> None:
        target = tmp_path / "target.csv"
        fill_csv_cli(target)
        with target.open(newline="") as t:
            rows = list(csv.reader(t))
        assert [row[:3] for row in rows] == [
            ["KPOPS_CONFIG_PATH", ".", "False"],
            ["KPOPS_DOTENV_PATH", "", "False"],
            ["KPOPS_ENVIRONMENT", "", "False"],
            ["KPOPS_OPERATION_MODE", "managed", "False"],
            ["KPOPS_PIPELINE_PATHS", "", "True"],
            ["KPOPS_PIPELINE_STEPS", "", "False"],
        ]
        assert all(row[3] for row in rows)

    def test_write_title_to_dotenv_file(self, tmp_path: Path) -> None:
        target = tmp_path / "target.ENV"
        write_title_to_dotenv_file(target, "title", "description of length 72" * 3)
        with target.open() as t:
            assert t.read().replace("\r\n", "\n").replace("\r", "\n") == (
                "# title\n"
                "#\n"
                "# "
                "description of length 72description of length 72description of"
                "\n"
                "# length 72\n#\n"
            )

    @pytest.mark.parametrize(
        ("var_name", "default", "required", "description", "setting_name", "expected"),
        [
            pytest.param(
                "NAME",
                "default",
                "True",
                "description",
                "setting_name",
                "# setting_name\n# description\nNAME=default\n",
                id="default exists, required",
            ),
            pytest.param(
                "NAME",
                "",
                "True",
                "description",
                "setting_name",
                "# setting_name\n# description\nNAME # No default value, required\n",
                id="default not exists, required",
            ),
            pytest.param(
                "NAME",
                "default",
                "False",
                "description",
                "setting_name",
                "# setting_name\n# description\nNAME=default\n",
                id="default exists, not required",
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
                id="default not exists, not required",
            ),
            pytest.param(
                "NAME",
                "default",
                "True",
                "description",
                "",
                "# description\nNAME=default\n",
                id="no setting name",
            ),
        ],
    )
    def test_append_csv_to_dotenv_file(
        self,
        tmp_path: Path,
        var_name: str,
        default: Any,
        required: str,
        description: str,
        setting_name: str,
        expected: str,
    ) -> None:
        source = tmp_path / "source.csv"
        target = tmp_path / "target.env"
        csv_record = [var_name, default, required, description]
        csv_column_names = [
            EnvVarAttrs.NAME,
            EnvVarAttrs.DEFAULT_VALUE,
            EnvVarAttrs.REQUIRED,
            EnvVarAttrs.DESCRIPTION,
        ]
        with source.open("w+", newline="") as f:
            csv_record.append(setting_name)
            csv_column_names.append(EnvVarAttrs.CORRESPONDING_SETTING_NAME)
            f.write(",".join(csv_column_names) + "\n")
            f.write(",".join(csv_record))
        append_csv_to_dotenv_file(source, target)
        with target.open("r", newline="") as f:
            assert f.read().replace("\r\n", "\n").replace("\r", "\n") == expected

    @pytest.mark.parametrize(
        ("title", "description", "heading", "expected"),
        [
            pytest.param(
                "title",
                "description",
                "###",
                "### title\n\ndescription\n\n",
                id="all provided, default heading",
            ),
            pytest.param(
                "title",
                "description",
                "##",
                "## title\n\ndescription\n\n",
                id="all provided, different heading",
            ),
            pytest.param(
                "title",
                "description",
                "",
                "title\n\ndescription\n\n",
                id="all provided, heading empty str",
            ),
            pytest.param(
                "title",
                "description",
                None,
                "title\n\ndescription\n\n",
                id="all provided, heading is None",
            ),
            pytest.param(
                None,
                "description",
                "###",
                "description\n\n",
                id="no title",
            ),
            pytest.param(
                "title",
                None,
                "###",
                "### title\n\n",
                id="no description",
            ),
        ],
    )
    def test_write_csv_to_md_file(
        self,
        tmp_path: Path,
        title: str,
        description: str,
        heading: str,
        expected: str,
    ) -> None:
        source = tmp_path / "source.csv"
        target = tmp_path / "target.env"
        csv_record = ["NAME", "default", "True", "description", "setting_name"]
        csv_column_names = [
            EnvVarAttrs.NAME,
            EnvVarAttrs.DEFAULT_VALUE,
            EnvVarAttrs.REQUIRED,
            EnvVarAttrs.DESCRIPTION,
            EnvVarAttrs.CORRESPONDING_SETTING_NAME,
        ]
        with source.open("w+", newline="") as f:
            f.write(",".join(csv_column_names) + "\n")
            f.write(",".join(csv_record))
        write_csv_to_md_file(source, target, title, description, heading)
        with target.open("r", newline="") as f:
            assert f.read().replace("\r\n", "\n").replace("\r", "\n") == expected + (
                "|Name|Default Value|Required|Description|Setting name|\n"
                "|----|-------------|--------|-----------|------------|\n"
                "|NAME|default      |True    |description|setting_name|\n"
            )


class TestComponentsDocGen:
    @pytest.fixture
    def docs_resources(self, tmp_path: Path) -> Path:
        target = tmp_path / "resources"
        shutil.copytree(ROOT / "docs/docs/resources", target)
        return target

    @staticmethod
    def snapshot(path: Path) -> dict[Path, str]:
        return {file: file.read_text() for file in path.rglob("*") if file.is_file()}

    def test_missing_template(self, docs_resources: Path) -> None:
        header = docs_resources / "pipeline-components/headers/streams-app.yaml"
        header.unlink()
        with pytest.raises(SystemExit, match=r"headers/streams-app\.yaml"):
            gen_docs_components.main(docs_resources)

    def test_stateless_generation(self, docs_resources: Path) -> None:
        gen_docs_components.main(docs_resources)
        generated = self.snapshot(docs_resources)
        gen_docs_components.main(docs_resources)
        assert self.snapshot(docs_resources) == generated

        section = (
            docs_resources / "pipeline-components/sections/version-streams-app.yaml"
        )
        section.write_text("version: 1.0.0\n")
        gen_docs_components.main(docs_resources)
        dependencies = (
            docs_resources
            / "pipeline-components/dependencies/pipeline_component_dependencies.yaml"
        )
        assert "version-streams-app.yaml" in dependencies.read_text()
