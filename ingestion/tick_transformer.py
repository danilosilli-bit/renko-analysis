import numpy as np
from ingestion.tick_analysis import (
    calculate_aggression,
    is_auction_tick
)


def remove_duplicates_ticks(ticks):
    """Remove duplicate ticks"""
    return np.unique(ticks)


def clean_ticks(ticks):
    mask = ticks['volume'] != 0
    return ticks[mask]


def add_aggression_fields(ticks):

    for i, tick in enumerate(ticks):

        ticks['is_auction'][i] = is_auction_tick(
            tick['bid'],
            tick['ask']
        )

        aggression = calculate_aggression(
            bid=tick['bid'],
            ask=tick['ask'],
            volume=tick['volume'],
            last=tick['last']
        )

        ticks['buy_qty'][i] = aggression.buy_qty
        ticks['sell_qty'][i] = aggression.sell_qty

        ticks['buy_financial'][i] = aggression.buy_financial
        ticks['sell_financial'][i] = aggression.sell_financial

    return ticks


def normalize_ticks(ticks):

    ticks = clean_ticks(ticks)
    ticks = remove_duplicates_ticks(ticks)

    timestamp = ticks['time'].astype('datetime64[s]')
    timestamp_ms = ticks['time_msc'].astype('datetime64[ms]')

    new_dtype = [
        ('timestamp', 'datetime64[s]'),
        ('timestamp_ms', 'datetime64[ms]'),

        ('bid', '<f8'),
        ('ask', '<f8'),
        ('last', '<f8'),

        ('volume', '<u8'),
        ('flags', '<i8'),
        ('volume_real', '<f8'),

        ('is_auction', '?'),

        ('buy_qty', '<f8'),
        ('sell_qty', '<f8'),

        ('buy_financial', '<f8'),
        ('sell_financial', '<f8')
    ]

    new_ticks = np.empty(
        ticks.shape,
        dtype=new_dtype
    )

    new_ticks['timestamp'] = timestamp
    new_ticks['timestamp_ms'] = timestamp_ms

    for name in ticks.dtype.names:
        if name not in ('time', 'time_msc'):
            new_ticks[name] = ticks[name]

    new_ticks = add_aggression_fields(new_ticks)

    return new_ticks