import pytest
from unittest.mock import Mock, call, patch

from services.application_runtime import ApplicationRuntime



def test_reset_intraday_storage_delegates_to_storage():
    runtime = ApplicationRuntime(
        historical_symbol="WIN_TEST",
        intraday_symbol="CFD_TEST",
        bootstrap_renko_service=Mock(),
        xp_terminal_path="XP_TEST",
        brick_sizes=[10, 30, 45],
        win_renko_service=Mock(),
        cfd_renko_service=Mock(),
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
        brick_sizes=[10, 30, 45],
        win_renko_service=Mock(),
        cfd_renko_service=Mock(),
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
    ), patch.object(
        runtime, "_create_runtime_snapshot", calls.snapshot,
    ), patch.object(
        runtime, "_persist_bootstrap_bricks", calls.persist,
    ), patch.object(
        runtime, "_initialize_market_runtimes", calls.runtimes,
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
        call.snapshot(),
        call.persist(),
        call.runtimes(),
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
        brick_sizes=[10, 30, 45],
        win_renko_service=Mock(),
        cfd_renko_service=Mock(),
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
        brick_sizes=[10, 30, 45],
        win_renko_service=Mock(),
        cfd_renko_service=Mock(),
    )

    assert runtime.historical_symbol == "WIN_TEST"
    assert runtime.intraday_symbol == "CFD_TEST"

def test_prepare_intraday_repository_prepares_both_symbols():
    runtime = ApplicationRuntime(
        historical_symbol="WIN_TEST",
        intraday_symbol="CFD_TEST",
        bootstrap_renko_service=Mock(),
        xp_terminal_path="XP_TEST",
        brick_sizes=[10, 30, 45],
        win_renko_service=Mock(),
        cfd_renko_service=Mock(),        
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
        brick_sizes=[10, 30, 45],
        win_renko_service=Mock(),
        cfd_renko_service=Mock(),
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
        brick_sizes=[10, 30, 45],
        win_renko_service=Mock(),
        cfd_renko_service=Mock(),
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
        brick_sizes=[10, 30, 45],
        win_renko_service=Mock(),
        cfd_renko_service=Mock(),
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
        brick_sizes=[10, 30, 45],
        win_renko_service=Mock(),
        cfd_renko_service=Mock(),
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
        brick_sizes=[10, 30, 45],
        win_renko_service=Mock(),
        cfd_renko_service=Mock(),
    )

    result = runtime._replay_today_xp_ticks([])

    assert result == {
        "processed_ticks": 0,
        "last_timestamp_ms": None,
    }

    bootstrap_service.process_intraday_tick.assert_not_called()    

def test_create_runtime_snapshot():
    bootstrap_service = Mock()
    snapshot = object()
    bootstrap_service.get_runtime_snapshot.return_value = snapshot

    runtime = ApplicationRuntime(
        historical_symbol="WIN_TEST",
        intraday_symbol="CFD_TEST",
        bootstrap_renko_service=bootstrap_service,
        xp_terminal_path="XP_TEST",
        brick_sizes=[10, 30, 45],
        win_renko_service=Mock(),
        cfd_renko_service=Mock(),
    )

    runtime._create_runtime_snapshot()

    bootstrap_service.get_runtime_snapshot.assert_called_once_with()
    assert runtime.runtime_snapshot is snapshot


def test_persist_bootstrap_bricks_to_both_markets():
    bootstrap_service = Mock()

    repositories = {
        10: Mock(),
        30: Mock(),
        45: Mock(),
    }
    bootstrap_service.repositories = repositories

    runtime = ApplicationRuntime(
        historical_symbol="WIN_TEST",
        intraday_symbol="CFD_TEST",
        bootstrap_renko_service=bootstrap_service,
        xp_terminal_path="XP_TEST",
        brick_sizes=[10, 30, 45],
        win_renko_service=Mock(),
        cfd_renko_service=Mock(),
    )

    runtime._persist_bootstrap_bricks()

    for repository in repositories.values():
        repository.persist_bricks.assert_called_once_with(
            ["WIN_TEST", "CFD_TEST"]
        )


def test_initialize_market_runtimes_from_same_snapshot():
    snapshot = object()
    win_service = Mock()
    cfd_service = Mock()

    runtime = ApplicationRuntime(
        historical_symbol="WIN_TEST",
        intraday_symbol="CFD_TEST",
        bootstrap_renko_service=Mock(),
        xp_terminal_path="XP_TEST",
        brick_sizes=[10, 30, 45],
        win_renko_service=win_service,
        cfd_renko_service=cfd_service,
    )

    intraday_repository = Mock()
    runtime.intraday_repository = intraday_repository
    runtime.runtime_snapshot = snapshot

    runtime._initialize_market_runtimes()

    win_service.initialize_from_snapshot.assert_called_once_with(
        snapshot=snapshot,
        intraday_repository=intraday_repository.renko_repository,
        intraday_symbol="WIN_TEST",
    )

    cfd_service.initialize_from_snapshot.assert_called_once_with(
        snapshot=snapshot,
        intraday_repository=intraday_repository.renko_repository,
        intraday_symbol="CFD_TEST",
    )