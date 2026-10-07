from unittest.mock import patch

from services.application_runtime import ApplicationRuntime


def test_reset_intraday_storage_delegates_to_storage():
    runtime = ApplicationRuntime()

    with patch(
        "services.application_runtime.reset_intraday_storage"
    ) as reset_mock:
        runtime._reset_intraday_storage()

    reset_mock.assert_called_once_with()


def test_start_initializes_current_startup_steps():
    runtime = ApplicationRuntime()

    with patch.object(
        runtime,
        "_reset_intraday_storage",
    ) as reset_mock, patch.object(
        runtime,
        "_open_historical_repository",
    ) as historical_mock:

        runtime.start()

    reset_mock.assert_called_once_with()
    historical_mock.assert_called_once_with()

    assert runtime.started is False

def test_open_historical_repository_stores_repository():
    runtime = ApplicationRuntime()

    with patch(
        "services.application_runtime.SQLiteManager"
    ) as sqlite_manager_mock, patch(
        "services.application_runtime.RenkoRepository"
    ) as repository_mock:

        db_mock = sqlite_manager_mock.return_value
        repository = repository_mock.return_value

        runtime._open_historical_repository()

    sqlite_manager_mock.assert_called_once()
    repository_mock.assert_called_once_with(db_mock)
    assert runtime.historical_repository is repository