from services.renko_service import (
    RenkoService,
)


def main():

    service = RenkoService(
        symbol="WINV26",
        brick_sizes=(10, 30, 45),
    )

    service.initialize(
        initial_price=186000,
    )

    dummy_tick = {
        "timestamp_ms": 1,
        "last": 186000.0,
        "volume": 0.0,
        "buy_qty": 0.0,
        "sell_qty": 0.0,
        "buy_financial": 0.0,
        "sell_financial": 0.0,
    }

    for brick_size in (
        10,
        30,
        45,
    ):
        service.engines[
            brick_size
        ]._initialize_state(
            dummy_tick
        )

    snapshot_a = (
        service.get_runtime_snapshot()
    )

    snapshot_b = (
        service.get_runtime_snapshot()
    )

    print()
    print("TESTE RUNTIME SNAPSHOT")
    print("=" * 60)

    all_ok = True

    for brick_size in (
        10,
        30,
        45,
    ):

        state_a = snapshot_a[
            brick_size
        ]["state"]

        state_b = snapshot_b[
            brick_size
        ]["state"]

        brick_a = snapshot_a[
            brick_size
        ]["last_closed_brick"]

        brick_b = snapshot_b[
            brick_size
        ]["last_closed_brick"]

        same_state_object = (
            state_a is state_b
        )

        same_brick_object = (
            brick_a is brick_b
        )

        print()
        print(f"{brick_size}R")
        print("-" * 60)

        print(
            "mesmo objeto state :",
            same_state_object,
        )

        print(
            "mesmo objeto brick :",
            same_brick_object,
        )

        if (
            same_state_object
            or same_brick_object
        ):
            all_ok = False

    print()
    print("=" * 60)

    if all_ok:

        print(
            "RESULTADO: SNAPSHOTS "
            "INDEPENDENTES"
        )

    else:

        raise AssertionError(
            "Snapshots compartilham objetos."
        )


if __name__ == "__main__":
    main()