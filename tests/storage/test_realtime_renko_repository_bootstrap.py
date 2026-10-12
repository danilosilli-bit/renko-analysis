from unittest.mock import MagicMock

from storage.realtime_renko_repository import RealtimeRenkoRepository


def test_bootstrap_without_new_bricks_does_not_persist():

    historical_repository = MagicMock()
    intraday_repository = MagicMock()

    repository = RealtimeRenkoRepository(
        historical_repository=historical_repository,
        intraday_repository=intraday_repository,
        historical_symbol="WINV26",
        intraday_symbol="WINV26",
        defer_persistence=True,
    )

    # O bootstrap começa sem bricks novos.
    assert repository.bricks == []

    # Simula a consulta ao último brick histórico.
    historical_repository.get_last_closed_brick.return_value = {
        "close": 150000.0,
    }

    last_brick = repository.get_last_closed_brick(
        "WINV26",
        30,
    )

    assert last_brick["close"] == 150000.0

    # A leitura histórica não deve gerar novos bricks.
    assert repository.bricks == []

    # Persistência após um replay sem ticks.
    repository.persist_bricks(
        ["WINV26", "Bra50Oct26"]
    )

    intraday_repository.save_brick.assert_not_called()