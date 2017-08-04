import threading

import requests

import constants

class ExchangeRatesThread(threading.Thread):

    def __init__(self, spawner, league):
        threading.Thread.__init__(self)
        self.spawner = spawner
        self.league = league
        
        self.rates = []
        self.start()
    
    def run(self):
        rates_data = requests.get(constants.RATES_API + self.league).json().get('lines')
        
        parsed_rates_data = {}
        
        for currency_data in rates_data:
            if currency_data['currencyTypeName'] in constants.CURRENCY_FULL:
                parsed_rates_data[currency_data['currencyTypeName']] = currency_data['chaosEquivalent']
        
        self.spawner.queue_exchange_rates.put((self.league, parsed_rates_data))
    
    def kill(self):
        pass