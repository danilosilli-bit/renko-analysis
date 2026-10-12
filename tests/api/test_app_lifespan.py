import asyncio
from unittest.mock import MagicMock, patch

import api.app as app_module


def test_lifespan_starts_and_stops_runtime():

    runtime = MagicMock()
    runtime.dual_feed_service.cfd_symbol = "Bra50Oct26"

    async def run_lifespan():

        with (
            patch.object(
                app_module,
                "create_application_runtime",
                return_value=runtime,
            ),
            patch.object(app_module, "BrokerRouter"),
            patch.object(app_module, "OrderGuard"),
            patch.object(app_module, "TradingOperationRepository"),
            patch.object(app_module, "OperationManager"),
            patch.object(app_module, "TradingService"),
            patch.object(app_module, "configure_trading_router"),
        ):
            async with app_module.lifespan(app_module.app):

                runtime.start.assert_called_once_with()

                assert (
                    app_module.dual_feed_service
                    is runtime.dual_feed_service
                )

                assert (
                    app_module.win_renko_service
                    is runtime.win_renko_service
                )

                assert (
                    app_module.cfd_renko_service
                    is runtime.cfd_renko_service
                )

                assert app_module.renko_initialized is True

            runtime.stop.assert_called_once_with()

            assert app_module.renko_initialized is False

    asyncio.run(run_lifespan())

def test_lifespan_stops_runtime_when_trading_setup_fails():

    runtime = MagicMock()
    runtime.dual_feed_service.cfd_symbol = "Bra50Oct26"

    async def run_lifespan():
        with (
            patch.object(
                app_module,
                "create_application_runtime",
                return_value=runtime,
            ),
            patch.object(
                app_module,
                "BrokerRouter",
                side_effect=RuntimeError("Falha no trading"),
            ),
        ):
            async with app_module.lifespan(app_module.app):
                pass

    import pytest

    with pytest.raises(RuntimeError, match="Falha no trading"):
        asyncio.run(run_lifespan())

    runtime.start.assert_called_once_with()
    runtime.stop.assert_called_once_with()
    assert app_module.renko_initialized is False


def test_lifespan_resets_state_when_shutdown_fails():

    runtime = MagicMock()
    runtime.dual_feed_service.cfd_symbol = "Bra50Oct26"
    runtime.stop.side_effect = RuntimeError("Falha no shutdown")

    async def run_lifespan():
        with (
            patch.object(
                app_module,
                "create_application_runtime",
                return_value=runtime,
            ),
            patch.object(app_module, "BrokerRouter"),
            patch.object(app_module, "OrderGuard"),
            patch.object(app_module, "TradingOperationRepository"),
            patch.object(app_module, "OperationManager"),
            patch.object(app_module, "TradingService"),
            patch.object(app_module, "configure_trading_router"),
        ):
            async with app_module.lifespan(app_module.app):
                assert app_module.renko_initialized is True

    import pytest

    with pytest.raises(RuntimeError, match="Falha no shutdown"):
        asyncio.run(run_lifespan())

    runtime.stop.assert_called_once_with()
    assert app_module.renko_initialized is False