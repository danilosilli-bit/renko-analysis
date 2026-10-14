def query_intraday_bricks(
    intraday_repository,
    brick_size: int,
    symbol: str,
) -> list[dict]:

    if intraday_repository is None:
        return []

    table_name = (
        intraday_repository
        .renko_repository
        .get_table_name(
            symbol
        )
    )

    rows = (
        intraday_repository
        .renko_db
        .execute(
            f"""
            SELECT *
            FROM {table_name}
            WHERE brick_size = ?
            ORDER BY id
            """,
            (
                brick_size,
            ),
        )
    )

    return [
        dict(row)
        for row in rows
    ]


def query_latest_intraday_brick(
    intraday_repository,
    brick_size: int,
    symbol: str,
):

    bricks = query_intraday_bricks(
        intraday_repository=intraday_repository,
        brick_size=brick_size,
        symbol=symbol,
    )

    if not bricks:
        return None

    return bricks[-1]