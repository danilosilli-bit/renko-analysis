import pytest
from unittest.mock import Mock, call, patch

from services.application_runtime import ApplicationRuntime



def test_reset_intraday_storage_delegates_to_storage():
    runtime = ApplicationRuntime(
        historical_symbol="WIN_TEST",
        intraday_symbol="CFD_TEST",
        bootstrap_renko_service=Mock(),
        xp_terminal_path="XP_TEST",
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
        xp_terminal_path="XP_TEST",
    )

    with patch.object(
        runtime, "_reset_intraday_storage", calls.reset,
    ), patch.object(
        runtime, "_open_historical_repository", calls.historical,
    ), patch.object(
        runtime, "_prepare_intraday_repository", calls.intraday,
    ), patch.object(
        runtime, "_initialize_historical_renko", calls.renko,
    ), patch.object(
        runtime, "_fetch_today_xp_ticks", calls.fetch,
    ), patch.object(
        runtime, "_replay_today_xp_ticks", calls.replay,
    ):
        calls.fetch.return_value = ["tick1", "tick2"]
        calls.replay.return_value = {
            "processed_ticks": 2,
            "last_timestamp_ms": 123456,
        }

        runtime.start()

    assert calls.mock_calls == [
        call.reset(),
        call.historical(),
        call.intraday(),
        call.renko(),
        call.fetch(),
        call.replay(["tick1", "tick2"]),
    ]

    assert runtime.bootstrap_result == {
        "processed_ticks": 2,
        "last_timestamp_ms": 123456,
    }

    assert runtime.started is False


def test_open_historical_repository_stores_repository():
    runtime = ApplicationRuntime(
        historical_symbol="WIN_TEST",
        intraday_symbol="CFD_TEST",
        bootstrap_renko_service=Mock(),
        xp_terminal_path="XP_TEST",
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
        xp_terminal_path="XP_TEST",
    )

    assert runtime.historical_symbol == "WIN_TEST"
    assert runtime.intraday_symbol == "CFD_TEST"

def test_prepare_intraday_repository_prepares_both_symbols():
    runtime = ApplicationRuntime(
        historical_symbol="WIN_TEST",
        intraday_symbol="CFD_TEST",
        bootstrap_renko_service=Mock(),
        xp_terminal_path="XP_TEST",
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
        xp_terminal_path="XP_TEST",
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

def test_fetch_today_xp_ticks_disconnects_after_success():
    runtime = ApplicationRuntime(
        historical_symbol="WIN_TEST",
        intraday_symbol="CFD_TEST",
        bootstrap_renko_service=Mock(),
        xp_terminal_path="XP_TEST",
    )

    with patch(
        "services.application_runtime.MT5IntradayHistoryClient"
    ) as client_class:
        client = client_class.return_value
        client.get_today_ticks.return_value = ["tick1"]

        result = runtime._fetch_today_xp_ticks()

    client_class.assert_called_once_with(
        terminal_path="XP_TEST"
    )
    client.connect.assert_called_once_with()
    client.get_today_ticks.assert_called_once_with(
        "WIN_TEST"
    )
    client.disconnect.assert_called_once_with()
    assert result == ["tick1"]


def test_fetch_today_xp_ticks_disconnects_after_error():
    runtime = ApplicationRuntime(
        historical_symbol="WIN_TEST",
        intraday_symbol="CFD_TEST",
        bootstrap_renko_service=Mock(),
        xp_terminal_path="XP_TEST",
    )

    with patch(
        "services.application_runtime.MT5IntradayHistoryClient"
    ) as client_class:
        client = client_class.return_value
        client.get_today_ticks.side_effect = RuntimeError(
            "Falha na consulta"
        )

        with pytest.raises(RuntimeError, match="Falha na consulta"):
            runtime._fetch_today_xp_ticks()

    client.disconnect.assert_called_once_with()


def test_replay_today_xp_ticks_processes_each_tick_once():
    bootstrap_service = Mock()

    runtime = ApplicationRuntime(
        historical_symbol="WIN_TEST",
        intraday_symbol="CFD_TEST",
        bootstrap_renko_service=bootstrap_service,
        xp_terminal_path="XP_TEST",
    )

    raw_ticks = [object(), object()]
    converted_ticks = [
        Mock(timestamp_ms=1000),
        Mock(timestamp_ms=2000),
    ]

    with patch(
        "services.application_runtime.mt5_history_to_intraday_tick",
        side_effect=converted_ticks,
    ) as adapter:
        result = runtime._replay_today_xp_ticks(raw_ticks)

    assert adapter.call_args_list == [
        call(
            raw_ticks[0],
            symbol="WIN_TEST",
            source_type="FUTURES",
            price_source="last",
        ),
        call(
            raw_ticks[1],
            symbol="WIN_TEST",
            source_type="FUTURES",
            price_source="last",
        ),
    ]

    assert bootstrap_service.process_intraday_tick.call_args_list == [
        call(converted_ticks[0]),
        call(converted_ticks[1]),
    ]

    assert result == {
        "processed_ticks": 2,
        "last_timestamp_ms": 2000,
    }

def test_replay_today_xp_ticks_with_no_ticks():
    bootstrap_service = Mock()

    runtime = ApplicationRuntime(
        historical_symbol="WIN_TEST",
        intraday_symbol="CFD_TEST",
        bootstrap_renko_service=bootstrap_service,
        xp_terminal_path="XP_TEST",
    )

    result = runtime._replay_today_xp_ticks([])

    assert result == {
        "processed_ticks": 0,
        "last_timestamp_ms": None,
    }

    bootstrap_service.process_intraday_tick.assert_not_called()    