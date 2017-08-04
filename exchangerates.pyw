import threading

import requests

RATES_API = 'http://poe.ninja/api/Data/GetCurrencyOverview?league='

class ExchangeRatesThread(threading.Thread):

    def __init__(self, league, currencies):
    threading.Thread.__init__(self)
        self.league = league
        self.currencies = currencies
        
        self.rates = []
        self.start()
    
    def run(self):
        rates_data = requests.get(RATES_API + league).json().get('lines')
        for currency in self.currencies:
            