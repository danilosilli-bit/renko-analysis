import pandas as pd
from ingestion.mt5_client import MT5Client
from ingestion.tick_collector import TickCollector
import ingestion.tick_utils as tick_utils
import ingestion.tick_transformer as tick_transformer
import numpy as np
from IPython.display import display
from storage.tick_repository import TickRepository
from storage.sqlite_manager import SQLiteManager



client = MT5Client(login=50390846, server='XPMT5-DEMO')
client.connect()
infoterminal = client.get_terminal_info()

for k in infoterminal.keys():
    print(k, ' -> ', infoterminal[k])

ticks = TickCollector(client).collect_ticks_batch('PETR4', pd.Timestamp('2026-05-12'), 1000)
display(ticks)

client.disconnect()

new_ticks = tick_transformer.normalize_ticks(ticks)
print(type(new_ticks))
display(new_ticks)

db = SQLiteManager("ticks.db")

repository = TickRepository(db)

repository.create_table("PETR4")

repository.save_ticks(
    "PETR4",
    new_ticks
)

print(
    repository.count_ticks("PETR4")
)

