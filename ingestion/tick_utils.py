def get_last_tick_time(ticks):
    """Get the time of the last tick in the batch"""
    if len(ticks) == 0:
        return None
    return ticks[-1]['time']