import numpy as np

def remove_duplicates_ticks(ticks):
    """Remove duplicate ticks"""
    ticks = np.unique(ticks)
    return ticks

def clean_ticks(ticks):
    mask = ticks['volume'] != 0
    ticks = ticks[mask]
    return ticks

def normalize_ticks(ticks):
    ticks = clean_ticks(ticks)

    timestamp = ticks['time'].astype('datetime64[s]')
    timestamp_ms = ticks['time_msc'].astype('datetime64[ms]')

    new_dtype = [('timestamp','datetime64[s]'), ('timestamp_ms','datetime64[ms]'),
                 ('bid', '<f8'), ('ask', '<f8'), ('last', '<f8'), ('volume', '<u8'),
                 ('flags', '<i8'), ('volume_real', '<f8')]

    new_ticks = np.empty(ticks.shape, dtype=new_dtype)
    new_ticks['timestamp'] = timestamp
    new_ticks['timestamp_ms'] = timestamp_ms
    for name in ticks.dtype.names:
        if name not in ('time', 'time_msc'):
            new_ticks[name] = ticks[name]

    return new_ticks

