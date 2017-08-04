import threading

import requests

import constants

class ExchangeRatesThread(threading.Thread):
    """Class that parses the exchange rate data from poe.ninja"""

    def __init__(self, spawner, league):
        """Initializes the thread with reference to the creator thread and league"""
        threading.Thread.__init__(self)
        self.spawner = spawner
        self.league = league

        self.rates = []
        self.start()

    def run(self):
        """Gets the exchange rate information from the API"""
        rates_data = requests.get(constants.RATES_API + self.league).json()
        parsed_rates_data = {}

        if rates_data:
            for currency_data in rates_data['lines']:
                if currency_data['currencyTypeName'] in constants.CURRENCY_FULL:
                    parsed_rates_data[currency_data['currencyTypeName']] = currency_data['chaosEquivalent']

        self.spawner.queue_exchange_rates.put((self.league, parsed_rates_data))

    def kill(self):
        """Does nothing."""
        pass