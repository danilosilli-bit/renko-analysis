import sqlite3

DB_PATH = "data/renko.db"

conn = sqlite3.connect(DB_PATH)

cursor = conn.cursor()

cursor.execute("""
SELECT name
FROM sqlite_master
WHERE type='table'
""")

tables = cursor.fetchall()

print("Tabelas encontradas:")
for table in tables:
    print(table[0])

conn.close()


# criar a tabela
conn = sqlite3.connect("data/renko.db")

cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS renko_petr4 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        brick_size REAL,

        open_time TEXT,
        close_time TEXT,

        open REAL,
        close REAL,

        high REAL,
        low REAL,

        direction TEXT,

        volume REAL,

        buy_qty REAL,
        sell_qty REAL,

        buy_financial REAL,
        sell_financial REAL,

        trades_count INTEGER
    )
    """)

conn.commit()

print(f"Registros alterados: {cursor.rowcount}")

conn.close()


#Inserir registro renko

def insert_renko(
    conn,
    symbol,
    brick_size,
    open_time,
    close_time,
    open_price,
    close_price,
    high,
    low,
    direction,
    volume,
    trades_count
):
    table_name = f"renko_{symbol.lower()}"

    conn.execute(
        f"""
        INSERT INTO {table_name} (
            brick_size,
            open_time,
            close_time,
            open,
            close,
            high,
            low,
            direction,
            volume,
            buy_qty,
            sell_qty,
            buy_financial,
            sell_financial,
            trades_count
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            brick_size,
            open_time,
            close_time,
            open_price,
            close_price,
            high,
            low,
            direction,
            volume,
            0,
            0,
            0,
            0,
            trades_count
        )
    )

import sqlite3

DB_PATH = "data/renko.db"

conn = sqlite3.connect(DB_PATH)

insert_renko(
    conn=conn,
    symbol="PETR4",
    brick_size=15,
    open_time="2026-07-31T15:05.390",
    close_time="2026-07-31T19:30.000",
    open_price=43.40,
    close_price=43.26,
    high=43.55,
    low=43.26,
    direction="DOWN",  #DOWN or UP
    volume=15620000,
    trades_count=25610
)

conn.commit()

conn.close()