from unittest.mock import patch

from services.application_runtime import ApplicationRuntime


def test_reset_intraday_storage_delegates_to_storage():
    runtime = ApplicationRuntime()

    with patch(
        "services.application_runtime.reset_intraday_storage"
    ) as reset_mock:
        runtime._reset_intraday_storage()

    reset_mock.assert_called_once_with()
