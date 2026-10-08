import pytest
import threading
from unittest.mock import Mock

from services.dual_mt5_feed_service import (
    DualMT5FeedService,
)


def create_service():
    return DualMT5FeedService(
        win_terminal_path="XP_TEST",
        win_symbol="WIN_TEST",
        cfd_terminal_path="ACTIVTRADES_TEST",
        cfd_symbol="CFD_TEST",
    )


def test_stop_before_start():
    service = create_service()

    service.stop()

    assert service._running is False


def test_stop_twice():
    service = create_service()

    service.stop()
    service.stop()

    assert service._running is False


def test_stop_does_not_join_process_that_never_started():
    service = create_service()

    process = Mock()
    process.pid = None
    process.is_alive.return_value = False

    service._running = True
    service._win_process = process

    service.stop()

    process.join.assert_not_called()

def test_stop_closes_all_queues():
    service = create_service()

    tick_queue = Mock()
    win_command_queue = Mock()
    cfd_command_queue = Mock()

    service._running = True

    service._queue = tick_queue
    service._win_command_queue = win_command_queue
    service._cfd_command_queue = cfd_command_queue

    service.stop()

    for mocked_queue in (
        tick_queue,
        win_command_queue,
        cfd_command_queue,
    ):
        mocked_queue.cancel_join_thread.assert_called_once()
        mocked_queue.close.assert_called_once()

    assert service._queue is None
    assert service._win_command_queue is None
    assert service._cfd_command_queue is None

def test_stop_kills_worker_that_survives_terminate():
    service = create_service()

    process = Mock()
    process.pid = 12345
    process.is_alive.side_effect = [
        True,   # Antes do terminate()
        True,   # Depois do primeiro join()
        False,  # Depois do kill() e segundo join()
        False,  # Log final do worker
        False,  # Verificação na limpeza das referências
    ]

    service._running = True
    service._win_process = process

    service.stop()

    process.terminate.assert_called_once()
    process.kill.assert_called_once()
    assert process.join.call_count == 2

def test_stop_cleans_queues_when_worker_survives_kill():
    service = create_service()

    process = Mock()
    process.pid = 12345
    process.is_alive.return_value = True

    tick_queue = Mock()
    win_command_queue = Mock()
    cfd_command_queue = Mock()

    service._running = True
    service._win_process = process

    service._queue = tick_queue
    service._win_command_queue = win_command_queue
    service._cfd_command_queue = cfd_command_queue

    with pytest.raises(
        RuntimeError,
        match="permanece ativo após kill",
    ):
        service.stop()

    process.terminate.assert_called_once()
    process.kill.assert_called_once()

    for mocked_queue in (
        tick_queue,
        win_command_queue,
        cfd_command_queue,
    ):
        mocked_queue.close.assert_called_once()

    assert service._queue is None
    assert service._win_command_queue is None
    assert service._cfd_command_queue is None

def test_stop_does_not_join_thread_that_never_started():
    service = create_service()

    consumer = threading.Thread(
        target=lambda: None,
        name="test-consumer",
    )

    service._running = True
    service._consumer_thread = consumer

    service.stop()

    assert service._running is False
    assert service._consumer_thread is None

def test_stop_reports_consumer_thread_timeout():
    service = create_service()

    consumer = Mock()
    consumer.ident = 12345
    consumer.is_alive.return_value = True

    tick_queue = Mock()

    service._running = True
    service._consumer_thread = consumer
    service._queue = tick_queue

    with pytest.raises(
        RuntimeError,
        match="Thread consumidora permanece ativa",
    ):
        service.stop()

    consumer.join.assert_called_once_with(timeout=2)
    tick_queue.close.assert_called_once()

def test_start_cleans_resources_when_cfd_worker_fails():
    service = create_service()

    win_process = Mock()
    win_process.pid = 1234
    win_process.is_alive.side_effect = [
        True,   # Log do start()
        True,   # Verificação no stop(), antes de terminate()
        False,  # Verificação após join()
        False,  # Log final do worker
    ]

    cfd_process = Mock()
    cfd_process.pid = None
    cfd_process.start.side_effect = RuntimeError(
        "Falha ao iniciar CFD"
    )

    tick_queue = Mock()
    win_command_queue = Mock()
    cfd_command_queue = Mock()

    service._context = Mock()

    service._context.Queue.side_effect = [
        tick_queue,
        win_command_queue,
        cfd_command_queue,
    ]

    service._context.Process.side_effect = [
        win_process,
        cfd_process,
    ]

    with pytest.raises(
        RuntimeError,
        match="Falha ao iniciar CFD",
    ):
        service.start()

    win_process.start.assert_called_once()
    win_process.terminate.assert_called_once()
    win_process.join.assert_called_once_with(timeout=5)

    cfd_process.start.assert_called_once()
    cfd_process.join.assert_not_called()

    for mocked_queue in (
        tick_queue,
        win_command_queue,
        cfd_command_queue,
    ):
        mocked_queue.close.assert_called_once()

    assert service._running is False
    assert service._win_process is None
    assert service._cfd_process is None

def test_stop_retries_worker_after_failed_shutdown():
    service = create_service()

    process = Mock()
    process.pid = 12345

    # Simula o estado real do processo.
    state = {"alive": True}

    process.is_alive.side_effect = lambda: state["alive"]

    # Na primeira tentativa, terminate() não funciona.
    # Na segunda tentativa, o processo encerra.
    def terminate():
        if process.terminate.call_count >= 2:
            state["alive"] = False

    process.terminate.side_effect = terminate

    service._running = True
    service._win_process = process

    # ====================================================
    # PRIMEIRA TENTATIVA
    # ====================================================

    with pytest.raises(
        RuntimeError,
        match="permanece ativo após kill",
    ):
        service.stop()

    # O processo continua ativo e referenciado.
    assert service._win_process is process
    assert service._running is False

    assert process.terminate.call_count == 1
    assert process.kill.call_count == 1

    # ====================================================
    # SEGUNDA TENTATIVA
    # ====================================================

    service.stop()

    # Agora o processo encerrou após terminate().
    assert process.terminate.call_count == 2

    # kill() não deve ser chamado novamente.
    assert process.kill.call_count == 1

    # A referência deve ser liberada.
    assert service._win_process is None

def test_start_rejects_previous_active_worker():
    service = create_service()

    process = Mock()
    process.pid = 12345
    process.is_alive.return_value = True

    context = Mock()
    service._context = context

    service._win_process = process
    service._running = False

    with pytest.raises(
        RuntimeError,
        match="worker anterior",
    ):
        service.start()

    context.Queue.assert_not_called()
    process.terminate.assert_not_called()

    assert service._running is False
    assert service._win_process is process