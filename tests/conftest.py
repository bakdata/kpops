import os
from unittest import mock
import pytest
from collections.abc import Iterator

@pytest.fixture()
def _mock_env() -> Iterator[None]:
    """Clear ``os.environ``

    :yield: None. Prevents the function and the mock
        context from exiting.
    """
    with mock.patch.dict(os.environ, clear=True):
        yield
