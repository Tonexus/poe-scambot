import argparse
import urllib.request
import json
import re
import tkinter as tk
from tkinter import ttk

currency_abbreviated = ['alt', 'fuse', 'alc', 'chaos', 'gcp', 'exa', 'chrom', 'jew', 'chance', 'chisel', 'scour', 'blessed', 'regret', 'regal', 'divine', 'vaal']
currency_singular = ['Orb of Alteration', 'Orb of Fusing', 'Orb of Alchemy', 'Chaos Orb', 'Gemcutter\'s Prism', 'Exalted Orb', 'Chromatic Orb', 'Jeweller\'s Orb', 'Orb of Chance', 'Cartographer\'s Chisel', 'Orb of Scouring', 'Blessed Orb', 'Orb of Regret', 'Regal Orb', 'Divine Orb', 'Vaal Orb']
currency_plural = ['Orbs of Alteration', 'Orbs of Fusing', 'Orbs of Alchemy', 'Chaos Orbs', 'Gemcutter\'s Prisms', 'Exalted Orbs', 'Chromatic Orbs', 'Jeweller\'s Orbs', 'Orbs of Chance', 'Cartographer\'s Chisels', 'Orbs of Scouring', 'Blessed Orbs', 'Orbs of Regret', 'Regal Orbs', 'Divine Orbs', 'Vaal Orbs']

price_regex = re.compile('~(b/o|price) ([0-9]+) (alt|fuse|alch|chaos|gcp|exa|chrom|jew|chance|chisel|scour|blessed|regret|regal|divine|vaal)')

stash_api = 'http://pathofexile.com/api/public-stash-tabs?id='

class App(tk.Tk):

    def __init__(self):
        tk.Tk.__init__(self)
        self.title('PoE Stash Searcher')
        self.geometry('500x210+900+200')
        self.resizable(False, False)
        self.protocol('WM_DELETE_WINDOW', self.destroy)
        self.make_topmost()
        
        self.parse_id = ''
        
        self.results = tk.StringVar()
        self.league = tk.StringVar()
        self.maxprice = tk.DoubleVar()
        self.currency = tk.StringVar()
        self.terms = tk.StringVar()
        
        self.create_search_results()
        self.create_label_league()
        self.create_option_league()
        self.create_label_maxprice()
        self.create_option_maxprice()
        self.create_option_currency()
        self.create_label_terms()
        self.create_option_terms()
        self.create_button_start()
        self.create_button_stop()

    def create_search_results(self):
        self.results_frame = ttk.Frame(self)
        self.results_frame.grid(row=0, column=0, rowspan=5, columnspan=4, padx=5, pady=5)
        
        self.results_text = tk.Text(self.results_frame, height=10, width=39)
        self.results_text.grid(row=0, column=0)
        self.results_text.configure(state='disabled')
        
        self.results_scroll = tk.Scrollbar(self.results_frame, command=self.results_text.yview)
        self.results_scroll.grid(row=0, column=1, sticky=tk.N+tk.S)
        
        self.results_text['yscrollcommand'] = self.results_scroll.set
        
    def create_label_league(self):
        self.label_league = ttk.Label(self, text='League')
        self.label_league.grid(row=0, column=4, columnspan=2, padx=5, pady=1, sticky=tk.W)
        
    def create_option_league(self):
        self.option_league = ttk.Combobox(self, textvariable=self.league, state='readonly', width=20)
        self.option_league.grid(row=1, column=4, columnspan=2, padx=5, pady=1)
        self.option_league['values'] = ['Legacy', 'Hardcore Legacy', 'Standard', 'Hardcore']
        self.option_league.current(0)
        
    def create_label_maxprice(self):
        self.label_maxprice = ttk.Label(self, text='Maximum Price')
        self.label_maxprice.grid(row=2, column=4, columnspan=2, padx=5, pady=1, sticky=tk.W)
        
    def create_option_maxprice(self):
        self.option_maxprice = ttk.Entry(self, textvariable=self.maxprice, width=10)
        self.option_maxprice.grid(row=3, column=4, padx=5, pady=1)
        
    def create_option_currency(self):
        self.option_currency = ttk.Combobox(self, textvariable=self.currency, state='readonly', width=7)
        self.option_currency.grid(row=3, column=5, padx=5, pady=1)
        self.option_currency['values'] = currency_abbreviated
        self.option_currency.current(0)
        
    def create_label_terms(self):
        self.lable_terms = ttk.Label(self, text='Search Terms')
        self.lable_terms.grid(row=5, column=0, padx=5, pady=5, sticky=tk.W)
        
    def create_option_terms(self):
        self.option_terms = ttk.Entry(self, textvariable=self.terms, width=39)
        self.option_terms.grid(row=5, column=1, columnspan=2, padx=5, pady=5)
        
    def create_button_start(self):
        self.button_start = ttk.Button(self, text='Start', command=self.parse_stash_data, width=9)
        self.button_start.grid(row=5, column=4, padx=5, pady=5)
        
    def create_button_stop(self):
        self.button_stop = ttk.Button(self, text='Stop', state=tk.DISABLED, width=9)
        self.button_stop.grid(row=5, column=5, padx=5, pady=5)

    def make_topmost(self):
        self.lift()
        self.attributes('-topmost', 1)
        self.attributes('-topmost', 0)

    def parse_price(self, to_parse):
        price = round(float(to_parse[0]), 1)
        
        if price == 1.0:
            return str(price) + ' ' + currency_singular[currency_abbreviated.index(to_parse[1])]
        else:
            return str(price) + ' ' + currency_plural[currency_abbreviated.index(to_parse[1])]

    def parse_stash_data(self):
        stash_data = json.loads(urllib.request.urlopen(stash_api + self.parse_id).read())
        search_terms = self.terms.get().split(', ')
        self.parse_id = stash_data['next_change_id']
        
        for stash in stash_data['stashes']:
            for item in stash['items']:
                if item['league'] == self.league.get():
                    for search_term in search_terms:
                        if search_term in item['name']:
                            price_regex_match = price_regex.match(stash['stash'])
                            try:
                                price_regex_match = price_regex.match(item['note'])
                            except KeyError:
                                pass
                            self.results_text.configure(state='normal')
                            if price_regex_match:
                                self.results_text.insert(tk.END, '@' + stash['accountName'] + ' Hi, I would like to buy your ' \
                                      + item['name'][28:] + ' listed for ' + self.parse_price(price_regex_match.group(2, 3)) \
                                      + ' in ' + item['league'] + ' (stash tab \"' + stash['stash'] + '\"; position: left ' + \
                                      str(item['x']) + ', top ' + str(item['y']) + ')\n\n')
                            else:
                                self.results_text.insert(tk.END, '@' + stash['accountName'] + ' Hi, I would like to buy your ' \
                                      + item['name'][28:] + ' in ' + item['league'] + ' (stash tab \"' + stash['stash'] \
                                      + '\"; position: left ' + str(item['x']) + ', top ' + str(item['y']) + ')\n\n')
                            self.results_text.configure(state='normal')


if __name__ == '__main__':
    App().mainloop()