from pathlib import Path

import pytest
from pytest_mock import MockerFixture
from structlog.testing import capture_logs
from typer.testing import CliRunner

from kpops.api.options import FilterType
from kpops.cli.main import app, cli
from kpops.core.exception import KpopsException
from kpops.core.operation import OperationMode

runner = CliRunner()


@pytest.fixture
def pipeline_file(tmp_path: Path) -> Path:
    file = tmp_path / "pipeline.yaml"
    file.touch()
    return file


@pytest.fixture
def dotenv_file(tmp_path: Path) -> Path:
    file = tmp_path / ".env"
    file.touch()
    return file


@pytest.fixture
def config_dir(tmp_path: Path) -> Path:
    dir_path = tmp_path / "config"
    dir_path.mkdir()
    return dir_path


def test_cli_exits_with_code_1_on_kpops_exception(mocker: MockerFixture) -> None:
    mocker.patch("kpops.cli.main.app", side_effect=KpopsException("boom"))

    with pytest.raises(SystemExit) as exc_info:
        cli()

    assert exc_info.value.code == 1


def test_cli_does_not_double_log_already_logged_exception(
    mocker: MockerFixture,
) -> None:
    error = KpopsException("boom")
    error.logged = True
    mocker.patch("kpops.cli.main.app", side_effect=error)

    with capture_logs() as cap_logs, pytest.raises(SystemExit):
        cli()

    assert not any(e["log_level"] == "error" for e in cap_logs)


def test_cli_logs_unlogged_exception(mocker: MockerFixture) -> None:
    error = KpopsException("boom")
    mocker.patch("kpops.cli.main.app", side_effect=error)

    with capture_logs() as cap_logs, pytest.raises(SystemExit):
        cli()

    assert any(e["log_level"] == "error" and e["event"] == "boom" for e in cap_logs)


@pytest.mark.parametrize("command", ["deploy", "destroy", "reset", "clean"])
def test_operation_managed_default_options(
    command: str, pipeline_file: Path, mocker: MockerFixture
) -> None:
    mock_api = mocker.patch(f"kpops.api.{command}")
    result = runner.invoke(app, [command, str(pipeline_file)], catch_exceptions=False)
    assert result.exit_code == 0
    mock_api.assert_called_once_with(
        pipeline_path=pipeline_file,
        dotenv=None,
        config=Path(),
        steps=None,
        filter_type=FilterType.INCLUDE,
        environment=None,
        dry_run=True,
        verbose=False,
        parallel=False,
    )


@pytest.mark.parametrize("command", ["deploy", "destroy", "reset", "clean"])
def test_operation_managed_custom_options(
    command: str,
    pipeline_file: Path,
    dotenv_file: Path,
    config_dir: Path,
    mocker: MockerFixture,
) -> None:
    mock_api = mocker.patch(f"kpops.api.{command}")
    result = runner.invoke(
        app,
        [
            command,
            str(pipeline_file),
            "--dotenv",
            str(dotenv_file),
            "--config",
            str(config_dir),
            "--steps",
            "step_a,step_b",
            "--filter-type",
            "exclude",
            "--environment",
            "development",
            "--execute",
            "--verbose",
            "--parallel",
            "--operation-mode",
            "managed",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    mock_api.assert_called_once_with(
        pipeline_path=pipeline_file,
        dotenv=[dotenv_file],
        config=config_dir,
        steps={"step_a", "step_b"},
        filter_type=FilterType.EXCLUDE,
        environment="development",
        dry_run=False,
        verbose=True,
        parallel=True,
    )


def test_generate_default_options(pipeline_file: Path, mocker: MockerFixture) -> None:
    mock_pipeline = mocker.MagicMock()
    mock_pipeline.to_yaml.return_value = ""
    mock_generate = mocker.patch("kpops.api.generate", return_value=mock_pipeline)

    result = runner.invoke(
        app, ["generate", str(pipeline_file)], catch_exceptions=False
    )
    assert result.exit_code == 0
    mock_generate.assert_called_once_with(
        pipeline_path=pipeline_file,
        dotenv=None,
        config=Path(),
        steps=None,
        filter_type=FilterType.INCLUDE,
        environment=None,
        verbose=False,
    )


def test_generate_custom_options(
    pipeline_file: Path,
    dotenv_file: Path,
    config_dir: Path,
    mocker: MockerFixture,
) -> None:
    mock_pipeline = mocker.MagicMock()
    mock_pipeline.to_yaml.return_value = ""
    mock_generate = mocker.patch("kpops.api.generate", return_value=mock_pipeline)

    result = runner.invoke(
        app,
        [
            "generate",
            str(pipeline_file),
            "--dotenv",
            str(dotenv_file),
            "--config",
            str(config_dir),
            "--steps",
            "step_a,step_b",
            "--filter-type",
            "exclude",
            "--environment",
            "development",
            "--verbose",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    mock_generate.assert_called_once_with(
        pipeline_path=pipeline_file,
        dotenv=[dotenv_file],
        config=config_dir,
        steps={"step_a", "step_b"},
        filter_type=FilterType.EXCLUDE,
        environment="development",
        verbose=True,
    )


@pytest.mark.parametrize("command", ["deploy", "destroy", "reset"])
@pytest.mark.parametrize("operation_mode", [OperationMode.MANIFEST, OperationMode.ARGO])
def test_manifest_operations(
    command: str,
    operation_mode: OperationMode,
    pipeline_file: Path,
    dotenv_file: Path,
    config_dir: Path,
    mocker: MockerFixture,
) -> None:
    mock_api = mocker.patch(f"kpops.api.{command}")
    mock_manifest = mocker.patch(f"kpops.api.manifest_{command}", return_value=[])

    result = runner.invoke(
        app,
        [
            command,
            str(pipeline_file),
            "--dotenv",
            str(dotenv_file),
            "--config",
            str(config_dir),
            "--steps",
            "step_a,step_b",
            "--filter-type",
            "include",
            "--environment",
            "production",
            "--verbose",
            "--operation-mode",
            operation_mode.value,
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    mock_manifest.assert_called_once_with(
        pipeline_file,
        [dotenv_file],
        config_dir,
        {"step_a", "step_b"},
        FilterType.INCLUDE,
        "production",
        True,
        operation_mode,
    )
    mock_api.assert_not_called()


def test_manifest_clean(
    pipeline_file: Path,
    dotenv_file: Path,
    config_dir: Path,
    mocker: MockerFixture,
) -> None:
    mock_clean = mocker.patch("kpops.api.clean")
    mock_manifest_clean = mocker.patch("kpops.api.manifest_clean", return_value=[])

    result = runner.invoke(
        app,
        [
            "clean",
            str(pipeline_file),
            "--dotenv",
            str(dotenv_file),
            "--config",
            str(config_dir),
            "--steps",
            "step_a,step_b",
            "--filter-type",
            "exclude",
            "--environment",
            "production",
            "--verbose",
            "--operation-mode",
            OperationMode.MANIFEST.value,
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    mock_manifest_clean.assert_called_once_with(
        pipeline_file,
        [dotenv_file],
        config_dir,
        {"step_a", "step_b"},
        FilterType.EXCLUDE,
        "production",
        True,
        OperationMode.MANIFEST,
    )
    mock_clean.assert_not_called()


def test_argo_clean(
    pipeline_file: Path,
    mocker: MockerFixture,
) -> None:
    mock_clean = mocker.patch("kpops.api.clean")
    mock_manifest_clean = mocker.patch("kpops.api.manifest_clean")

    with capture_logs() as cap_logs:
        result = runner.invoke(
            app,
            [
                "clean",
                str(pipeline_file),
                "--operation-mode",
                OperationMode.ARGO.value,
            ],
            catch_exceptions=False,
        )

    assert result.exit_code == 0
    mock_clean.assert_not_called()
    mock_manifest_clean.assert_not_called()
    assert any(
        e["log_level"] == "warning"
        and "No cleanup jobs are manifested in Argo mode" in e["event"]
        for e in cap_logs
    )
