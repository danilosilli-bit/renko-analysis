from datetime import datetime, timedelta, time, date


class TickCollector:

    def __init__(self, client):
        self.client = client

    def collect_ticks_batch(self, symbol, date_start, batch_size):
        ticks = self.client.get_ticks(
            symbol,
            date_start,
            count=batch_size
        )

        return ticks

    def collect_ticks_day(self, symbol, target_date):
        if isinstance(target_date, datetime):
            target_date = target_date.date()

        if not isinstance(target_date, date):
            raise TypeError(
                "target_date must be a datetime.date or datetime.datetime"
            )

        date_start = datetime.combine(target_date, time.min)
        date_end = date_start + timedelta(days=1)

        ticks = self.client.get_ticks_range(
            symbol,
            date_start,
            date_end
        )

        return ticks