from unittest.mock import Mock, call, patch

from services.application_runtime import ApplicationRuntime



def test_reset_intraday_storage_delegates_to_storage():
    runtime = ApplicationRuntime(
        historical_symbol="WIN_TEST",
        intraday_symbol="CFD_TEST",
        bootstrap_renko_service=Mock(),
    )

    with patch(
        "services.application_runtime.reset_intraday_storage"
    ) as reset_mock:
        runtime._reset_intraday_storage()

    reset_mock.assert_called_once_with()


def test_start_initializes_current_startup_steps():
    calls = Mock()

    runtime = ApplicationRuntime(
        historical_symbol="WIN_TEST",
        intraday_symbol="CFD_TEST",
        bootstrap_renko_service=Mock(),
    )

    with patch.object(
        runtime,
        "_reset_intraday_storage",
        calls.reset,
    ), patch.object(
        runtime,
        "_open_historical_repository",
        calls.historical,
    ), patch.object(
        runtime,
        "_prepare_intraday_repository",
        calls.intraday,
    ), patch.object(
        runtime,
        "_initialize_historical_renko",
        calls.renko,
    ):
        runtime.start()

    assert calls.mock_calls == [
        call.reset(),
        call.historical(),
        call.intraday(),
        call.renko(),
    ]

    assert runtime.started is False


def test_open_historical_repository_stores_repository():
    runtime = ApplicationRuntime(
        historical_symbol="WIN_TEST",
        intraday_symbol="CFD_TEST",
        bootstrap_renko_service=Mock(),
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
        bootstrap_renko_service=Mock(),
    )

    assert runtime.historical_symbol == "WIN_TEST"
    assert runtime.intraday_symbol == "CFD_TEST"

def test_prepare_intraday_repository_prepares_both_symbols():
    runtime = ApplicationRuntime(
        historical_symbol="WIN_TEST",
        intraday_symbol="CFD_TEST",
        bootstrap_renko_service=Mock(),
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

def test_initialize_historical_renko_uses_common_win_state():
    bootstrap_service = Mock()

    runtime = ApplicationRuntime(
        historical_symbol="WIN_TEST",
        intraday_symbol="CFD_TEST",
        bootstrap_renko_service=bootstrap_service,
    )

    historical_repository = Mock()
    intraday_repository = Mock()

    runtime.historical_repository = historical_repository
    runtime.intraday_repository = intraday_repository

    runtime._initialize_historical_renko()

    bootstrap_service.initialize_from_history.assert_called_once_with(
        historical_repository=historical_repository,
        intraday_repository=intraday_repository.renko_repository,
        historical_symbol="WIN_TEST",
        intraday_symbol="WIN_TEST",
        defer_persistence=True,
    )
    