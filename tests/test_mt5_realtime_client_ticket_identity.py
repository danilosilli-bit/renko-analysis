from types import SimpleNamespace

from ingestion.mt5_realtime_client import (
    MT5RealtimeClient,
)

import ingestion.mt5_realtime_client as mt5_module


def test_get_position_ticket_from_deal():

    client = MT5RealtimeClient()

    deal = SimpleNamespace(
        ticket=563094259,
        position_id=650401954,
    )

    original_function = (
        mt5_module.mt5.history_deals_get
    )

    try:

        mt5_module.mt5.history_deals_get = (
            lambda ticket: (deal,)
        )

        result = (
            client
            .get_position_ticket_from_deal(
                563094259
            )
        )

        assert result == 650401954

    finally:

        mt5_module.mt5.history_deals_get = (
            original_function
        )


def test_get_position_ticket_from_deal_not_found():

    client = MT5RealtimeClient()

    original_function = (
        mt5_module.mt5.history_deals_get
    )

    try:

        mt5_module.mt5.history_deals_get = (
            lambda ticket: ()
        )

        result = (
            client
            .get_position_ticket_from_deal(
                999999999
            )
        )

        assert result is None

    finally:

        mt5_module.mt5.history_deals_get = (
            original_function
        )

def test_position_ticket_resolution_error_is_preserved():

    client = MT5RealtimeClient()

    original_function = (
        mt5_module.mt5.history_deals_get
    )

    try:

        mt5_module.mt5.history_deals_get = (
            lambda ticket: None
        )

        try:

            client.get_position_ticket_from_deal(
                563094259
            )

            assert False

        except RuntimeError as exc:

            assert (
                "history_deals_get retornou None"
                in str(exc)
            )

    finally:

        mt5_module.mt5.history_deals_get = (
            original_function
        )

def test_send_market_order_keeps_success_when_position_resolution_fails(
    monkeypatch,
):

    client = MT5RealtimeClient()

    class FakeCheck:

        retcode = 0

        def _asdict(self):
            return {
                "retcode": self.retcode,
            }


    class FakeResult:

        retcode = (
            mt5_module
            .mt5
            .TRADE_RETCODE_DONE
        )

        order = 654321
        deal = 123456
        price = 183600.0

        def _asdict(self):
            return {
                "retcode": self.retcode,
                "order": self.order,
                "deal": self.deal,
                "price": self.price,
            }


    fake_info = SimpleNamespace(
        volume_min=0.01,
        volume_max=100.0,
        filling_mode=1,
    )

    fake_tick = SimpleNamespace(
        ask=183600.0,
        bid=183595.0,
    )


    monkeypatch.setattr(
        client,
        "ensure_symbol",
        lambda symbol: None,
    )

    monkeypatch.setattr(
        mt5_module.mt5,
        "symbol_info",
        lambda symbol: fake_info,
    )

    monkeypatch.setattr(
        mt5_module.mt5,
        "symbol_info_tick",
        lambda symbol: fake_tick,
    )

    monkeypatch.setattr(
        mt5_module.mt5,
        "order_check",
        lambda request: FakeCheck(),
    )

    monkeypatch.setattr(
        mt5_module.mt5,
        "order_send",
        lambda request: FakeResult(),
    )

    monkeypatch.setattr(
        client,
        "get_position_ticket_from_deal",
        lambda deal_ticket: (
            (_ for _ in ())
            .throw(
                RuntimeError(
                    "Falha simulada ao resolver "
                    "position_id."
                )
            )
        ),
    )


    result = client.send_market_order(
        symbol="WINV26",
        side="BUY",
        volume=1.0,
        check_only=False,
    )


    assert result["success"] is True

    assert result["stage"] == "send"

    assert (
        result["result"]["order"]
        == 654321
    )

    assert (
        result["result"]["deal"]
        == 123456
    )

    assert (
        result["position_ticket"]
        is None
    )

    assert (
        "Falha simulada"
        in result["position_ticket_error"]
    )