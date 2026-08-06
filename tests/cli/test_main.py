import pytest
from pytest_mock import MockerFixture
from structlog.testing import capture_logs

from kpops.cli.main import cli
from kpops.core.exception import KpopsException


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
