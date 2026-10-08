import pytest
from unittest.mock import Mock, call, patch

from services.application_runtime import ApplicationRuntime



def test_reset_intraday_storage_delegates_to_storage():
    runtime = ApplicationRuntime(
        historical_symbol="WIN_TEST",
        intraday_symbol="CFD_TEST",
        bootstrap_renko_service=Mock(),
        xp_terminal_path="XP_TEST",
        activtrades_terminal_path="ACTIVTRADES_TEST",
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
        activtrades_terminal_path="ACTIVTRADES_TEST",
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
    ), patch.object(
        runtime, "_prepare_source_handoffs", calls.handoffs,
    ), patch.object(
        runtime, "_prepare_market_pipelines", calls.pipelines,
    ),patch.object(
    runtime, "_load_cfd_symbol_spec", calls.spec,
    ), patch.object(
        runtime, "_start_dual_feed", calls.feed,
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
        call.handoffs(),
        call.pipelines(),
        call.spec(),
        call.feed(),
    ]

    assert runtime.bootstrap_result == {
        "processed_ticks": 2,
        "last_timestamp_ms": 123456,
    }

    assert runtime.started is True


def test_open_historical_repository_stores_repository():
    runtime = ApplicationRuntime(
        historical_symbol="WIN_TEST",
        intraday_symbol="CFD_TEST",
        bootstrap_renko_service=Mock(),
        xp_terminal_path="XP_TEST",
        activtrades_terminal_path="ACTIVTRADES_TEST",
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
        activtrades_terminal_path="ACTIVTRADES_TEST",
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
        activtrades_terminal_path="ACTIVTRADES_TEST",
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
        activtrades_terminal_path="ACTIVTRADES_TEST",
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
        activtrades_terminal_path="ACTIVTRADES_TEST",
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
        activtrades_terminal_path="ACTIVTRADES_TEST",
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
        activtrades_terminal_path="ACTIVTRADES_TEST",
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
        activtrades_terminal_path="ACTIVTRADES_TEST",
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
        activtrades_terminal_path="ACTIVTRADES_TEST",
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
        activtrades_terminal_path="ACTIVTRADES_TEST",
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
        activtrades_terminal_path="ACTIVTRADES_TEST",
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

def test_prepare_source_handoffs():
    runtime = ApplicationRuntime(
        historical_symbol="WIN_TEST",
        intraday_symbol="CFD_TEST",
        bootstrap_renko_service=Mock(),
        xp_terminal_path="XP_TEST",
        activtrades_terminal_path="ACTIVTRADES_TEST",
        brick_sizes=[10, 30, 45],
        win_renko_service=Mock(),
        cfd_renko_service=Mock(),
    )

    runtime.bootstrap_result = {
        "processed_ticks": 2,
        "last_timestamp_ms": 123456,
    }

    with patch(
        "services.application_runtime.SourceHandoffService"
    ) as handoff_class:
        runtime._prepare_source_handoffs()

    assert handoff_class.call_args_list == [
        call(
            last_bootstrap_timestamp_ms=123456,
            from_source="FUTURES",
            from_symbol="WIN_TEST",
            to_source="FUTURES",
            to_symbol="WIN_TEST",
        ),
        call(
            last_bootstrap_timestamp_ms=123456,
            from_source="FUTURES",
            from_symbol="WIN_TEST",
            to_source="CFD",
            to_symbol="CFD_TEST",
        ),
    ]


def test_prepare_market_pipelines():
    win_service = Mock()
    cfd_service = Mock()

    runtime = ApplicationRuntime(
        historical_symbol="WIN_TEST",
        intraday_symbol="CFD_TEST",
        bootstrap_renko_service=Mock(),
        xp_terminal_path="XP_TEST",
        activtrades_terminal_path="ACTIVTRADES_TEST",
        brick_sizes=[10, 30, 45],
        win_renko_service=win_service,
        cfd_renko_service=cfd_service,
    )

    runtime.intraday_repository = Mock()

    with patch(
        "services.application_runtime.IntradayMarketPipeline"
    ) as pipeline_class:
        runtime._prepare_market_pipelines()

    tick_repository = runtime.intraday_repository.tick_repository

    assert pipeline_class.call_args_list == [
        call(
            tick_repository=tick_repository,
            renko_service=win_service,
            symbol="WIN_TEST",
            source_type="FUTURES",
        ),
        call(
            tick_repository=tick_repository,
            renko_service=cfd_service,
            symbol="CFD_TEST",
            source_type="CFD",
        ),
    ]

    import pytest


@pytest.mark.parametrize("market", ["win", "cfd"])
def test_realtime_tick_rejected_by_handoff(market):
    runtime = ApplicationRuntime(
        historical_symbol="WIN_TEST",
        intraday_symbol="CFD_TEST",
        bootstrap_renko_service=Mock(),
        xp_terminal_path="XP_TEST",
        activtrades_terminal_path="ACTIVTRADES_TEST",
        brick_sizes=[10, 30, 45],
        win_renko_service=Mock(),
        cfd_renko_service=Mock(),
    )

    handoff = Mock()
    handoff.accept_realtime_tick.return_value = {
        "accepted": False,
        "source_transition": False,
    }

    pipeline = Mock()
    setattr(runtime, f"{market}_source_handoff_service", handoff)
    setattr(runtime, f"{market}_intraday_pipeline", pipeline)

    tick = Mock(timestamp_ms=123457)

    getattr(runtime, f"handle_{market}_realtime_tick")(tick)

    handoff.accept_realtime_tick.assert_called_once_with(123457)
    pipeline.process_realtime_tick.assert_not_called()


@pytest.mark.parametrize("market", ["win", "cfd"])
def test_first_realtime_tick_preserves_source_transition(market):
    runtime = ApplicationRuntime(
        historical_symbol="WIN_TEST",
        intraday_symbol="CFD_TEST",
        bootstrap_renko_service=Mock(),
        xp_terminal_path="XP_TEST",
        activtrades_terminal_path="ACTIVTRADES_TEST",
        brick_sizes=[10, 30, 45],
        win_renko_service=Mock(),
        cfd_renko_service=Mock(),
    )

    handoff = Mock()
    handoff.accept_realtime_tick.return_value = {
        "accepted": True,
        "source_transition": True,
    }

    pipeline = Mock()
    setattr(runtime, f"{market}_source_handoff_service", handoff)
    setattr(runtime, f"{market}_intraday_pipeline", pipeline)

    tick = Mock(timestamp_ms=123457)

    getattr(runtime, f"handle_{market}_realtime_tick")(tick)

    pipeline.process_realtime_tick.assert_called_once_with(
        tick,
        source_transition=True,
    )

def test_load_cfd_symbol_spec():
    runtime = ApplicationRuntime(
        historical_symbol="WIN_TEST",
        intraday_symbol="CFD_TEST",
        bootstrap_renko_service=Mock(),
        xp_terminal_path="XP_TEST",
        brick_sizes=[10, 30, 45],
        win_renko_service=Mock(),
        cfd_renko_service=Mock(),
        activtrades_terminal_path="ACTIVTRADES_TEST",
    )

    with patch(
        "services.application_runtime.MT5RealtimeClient"
    ) as client_class:
        client = client_class.return_value
        client.get_symbol_spec.return_value = {"symbol": "CFD_TEST"}

        runtime._load_cfd_symbol_spec()

        client_class.assert_called_once_with(
            path="ACTIVTRADES_TEST"
        )
        client.connect.assert_called_once()
        client.get_symbol_spec.assert_called_once_with("CFD_TEST")
        client.disconnect.assert_called_once()

    assert runtime.cfd_symbol_spec == {"symbol": "CFD_TEST"}


def test_load_cfd_symbol_spec_handles_error():
    runtime = ApplicationRuntime(
        historical_symbol="WIN_TEST",
        intraday_symbol="CFD_TEST",
        bootstrap_renko_service=Mock(),
        xp_terminal_path="XP_TEST",
        brick_sizes=[10, 30, 45],
        win_renko_service=Mock(),
        cfd_renko_service=Mock(),
        activtrades_terminal_path="ACTIVTRADES_TEST",
    )

    with patch(
        "services.application_runtime.MT5RealtimeClient"
    ) as client_class:
        client = client_class.return_value
        client.connect.side_effect = RuntimeError("MT5 unavailable")

        runtime._load_cfd_symbol_spec()

        client.disconnect.assert_called_once()

    assert runtime.cfd_symbol_spec is None


def test_start_dual_feed_registers_callbacks():
    runtime = ApplicationRuntime(
        historical_symbol="WIN_TEST",
        intraday_symbol="CFD_TEST",
        bootstrap_renko_service=Mock(),
        xp_terminal_path="XP_TEST",
        brick_sizes=[10, 30, 45],
        win_renko_service=Mock(),
        cfd_renko_service=Mock(),
        activtrades_terminal_path="ACTIVTRADES_TEST",
    )

    with patch(
        "services.application_runtime.DualMT5FeedService"
    ) as feed_class:
        runtime._start_dual_feed()

        feed_class.assert_called_once_with(
            win_terminal_path="XP_TEST",
            win_symbol="WIN_TEST",
            cfd_terminal_path="ACTIVTRADES_TEST",
            cfd_symbol="CFD_TEST",
            poll_interval=0.02,
        )

        feed = feed_class.return_value

        feed.set_win_callback.assert_called_once_with(
            runtime.handle_win_realtime_tick
        )
        feed.set_cfd_callback.assert_called_once_with(
            runtime.handle_cfd_realtime_tick
        )
        feed.start.assert_called_once()

    assert runtime.dual_feed_service is feed


def test_start_dual_feed_cleans_up_on_error():
    runtime = ApplicationRuntime(
        historical_symbol="WIN_TEST",
        intraday_symbol="CFD_TEST",
        bootstrap_renko_service=Mock(),
        xp_terminal_path="XP_TEST",
        brick_sizes=[10, 30, 45],
        win_renko_service=Mock(),
        cfd_renko_service=Mock(),
        activtrades_terminal_path="ACTIVTRADES_TEST",
    )

    with patch(
        "services.application_runtime.DualMT5FeedService"
    ) as feed_class:
        feed = feed_class.return_value
        feed.start.side_effect = RuntimeError("Worker failed")

        with pytest.raises(RuntimeError, match="Worker failed"):
            runtime._start_dual_feed()

        feed.stop.assert_called_once()


def test_stop_dual_feed():
    runtime = ApplicationRuntime(
        historical_symbol="WIN_TEST",
        intraday_symbol="CFD_TEST",
        bootstrap_renko_service=Mock(),
        xp_terminal_path="XP_TEST",
        brick_sizes=[10, 30, 45],
        win_renko_service=Mock(),
        cfd_renko_service=Mock(),
        activtrades_terminal_path="ACTIVTRADES_TEST",
    )

    runtime.dual_feed_service = Mock()
    runtime.started = True

    runtime.stop()

    runtime.dual_feed_service.stop.assert_called_once()
    assert runtime.started is False


def test_stop_without_feed():
    runtime = ApplicationRuntime(
        historical_symbol="WIN_TEST",
        intraday_symbol="CFD_TEST",
        bootstrap_renko_service=Mock(),
        xp_terminal_path="XP_TEST",
        brick_sizes=[10, 30, 45],
        win_renko_service=Mock(),
        cfd_renko_service=Mock(),
        activtrades_terminal_path="ACTIVTRADES_TEST",
    )

    runtime.stop()

    assert runtime.started is False