from config.storage_config import (
    INTRADAY_DIR,
    INTRADAY_TICKS_DB,
    INTRADAY_RENKO_DB,
)


def reset_intraday_storage():
    """
    Remove os bancos temporários da sessão intraday.

    IMPORTANTE:
    esta função atua somente em data/intraday/.
    Os bancos históricos nunca são alterados aqui.
    """

    INTRADAY_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    for db_path in (
        INTRADAY_TICKS_DB,
        INTRADAY_RENKO_DB,
    ):
        if db_path.exists():
            db_path.unlink()