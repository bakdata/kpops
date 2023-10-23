import os
from collections.abc import Iterator
from unittest import mock

import pytest


@pytest.fixture()
def mock_env() -> Iterator[os._Environ[str]]:
    """Clear ``os.environ``.

    :yield: ``os.environ``. Prevents the function and the mock
        context from exiting.
    """
    with mock.patch.dict(os.environ, clear=True):
        yield os.environ
