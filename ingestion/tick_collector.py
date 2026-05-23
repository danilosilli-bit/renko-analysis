

class TickCollector:

    def __init__(self, client):
        self.client = client

    def collect_ticks_batch(self, symbol, date_start, batch_size): 
            ticks = self.client.get_ticks(symbol, date_start, count=batch_size)
            return ticks
