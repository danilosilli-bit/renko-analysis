from unittest.mock import patch

from services.application_runtime import ApplicationRuntime


def test_reset_intraday_storage_delegates_to_storage():
    runtime = ApplicationRuntime(
        historical_symbol="WIN_TEST",
        intraday_symbol="CFD_TEST",
    )

    with patch(
        "services.application_runtime.reset_intraday_storage"
    ) as reset_mock:
        runtime._reset_intraday_storage()

    reset_mock.assert_called_once_with()


def test_start_initializes_current_startup_steps():
    runtime = ApplicationRuntime(
        historical_symbol="WIN_TEST",
        intraday_symbol="CFD_TEST",
    )

    with patch.object(
        runtime,
        "_reset_intraday_storage",
    ) as reset_mock, patch.object(
        runtime,
        "_open_historical_repository",
    ) as historical_mock, patch.object(
        runtime,
        "_prepare_intraday_repository",
    ) as intraday_mock:

        runtime.start()

    reset_mock.assert_called_once_with()
    historical_mock.assert_called_once_with()
    intraday_mock.assert_called_once_with()

    assert runtime.started is False


def test_open_historical_repository_stores_repository():
    runtime = ApplicationRuntime(
        historical_symbol="WIN_TEST",
        intraday_symbol="CFD_TEST",
    )

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


def test_runtime_stores_market_symbols():
    runtime = ApplicationRuntime(
        historical_symbol="WIN_TEST",
        intraday_symbol="CFD_TEST",
    )

    assert runtime.historical_symbol == "WIN_TEST"
    assert runtime.intraday_symbol == "CFD_TEST"

def test_prepare_intraday_repository_prepares_both_symbols():
    runtime = ApplicationRuntime(
        historical_symbol="WIN_TEST",
        intraday_symbol="CFD_TEST",
    )

    with patch(
        "services.application_runtime.IntradayRepository"
    ) as repository_mock:

        repository = repository_mock.return_value

        runtime._prepare_intraday_repository()

    repository_mock.assert_called_once_with()

    assert repository.prepare_symbol.call_count == 2
    repository.prepare_symbol.assert_any_call("WIN_TEST")
    repository.prepare_symbol.assert_any_call("CFD_TEST")

    assert runtime.intraday_repository is repository
    