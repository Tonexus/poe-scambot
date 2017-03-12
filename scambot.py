import time
import queue
import configparser
import urllib.request
import json
import tkinter as tk
from tkinter import ttk

import parserthread as pt
import beepthread as bt

currency_abbreviated = ['alt', 'fuse', 'alch', 'chaos', 'gcp', 'exa',
                        'chrom', 'jew', 'chance', 'chisel', 'scour',
                        'blessed', 'regret', 'regal', 'divine',
                        'vaal']

currency_singular = ['Orb of Alteration', 'Orb of Fusing',
                     'Orb of Alchemy', 'Chaos Orb',
                     'Gemcutter\'s Prism', 'Exalted Orb',
                     'Chromatic Orb', 'Jeweller\'s Orb',
                     'Orb of Chance', 'Cartographer\'s Chisel',
                     'Orb of Scouring', 'Blessed Orb',
                     'Orb of Regret', 'Regal Orb', 'Divine Orb',
                     'Vaal Orb']

currency_plural = ['Orbs of Alteration', 'Orbs of Fusing',
                   'Orbs of Alchemy', 'Chaos Orbs',
                   'Gemcutter\'s Prisms', 'Exalted Orbs',
                   'Chromatic Orbs', 'Jeweller\'s Orbs',
                   'Orbs of Chance', 'Cartographer\'s Chisels',
                   'Orbs of Scouring', 'Blessed Orbs',
                   'Orbs of Regret', 'Regal Orbs', 'Divine Orbs',
                   'Vaal Orbs']

parse_id_api = 'http://api.poe.ninja/api/Data/GetStats'

class App(tk.Tk):
    """App that centralizes all of the live search functionality with
    a simple UI.
    """

    def __init__(self):
        """Initializes the app."""
        tk.Tk.__init__(self)
        self.title('PoE Stash Searcher')
        self.geometry('800x375+900+200')
        self.resizable(False, False)
        self.protocol('WM_DELETE_WINDOW', self.kill)
        
        self.subthreads = []
        self.queue_results = queue.Queue()
        self.queue_parse_ids = queue.Queue()
        self.start = False
        self.dead = False
        
        self.parse_id = tk.StringVar()
        self.league = tk.StringVar()
        self.maxprice = tk.DoubleVar()
        self.minprice = tk.DoubleVar()
        self.currency = tk.StringVar()
        self.terms = tk.StringVar()
        
        self.create_widgets()
        
        self.parse_config()
        
        self.after(500, self.check_queue)

    def create_widgets(self):
        """Creates the app\'s widgets."""
        self.create_search_results()
        self.create_option_parse_id()
        self.create_option_league()
        self.create_option_maxprice()
        self.create_option_currency()
        self.create_option_minprice()
        self.create_option_terms()
        self.create_button_start()
        self.create_button_stop()
        
    def parse_config(self):
        """Parses the config file \'scambot.cfg\' or creates a
        default one if it does not exist.
        """
        fn = 'scambot.cfg'
        config = configparser.ConfigParser()
        config['defaults'] = {}
        config['output'] = {}
        config['input'] = {}
        
        config.set('defaults', 'league', 'Legacy')
        config.set('defaults', 'currency', 'chaos')
        config.set('defaults', 'maxprice', '20')
        config.set('defaults', 'minprice', '1')
        
        config.set('output', 'max_console_size', '1000')
        config.set('output', 'clipboard', 'y')
        config.set('output', 'log', 'n')
        config.set('output', 'log_path', '')
        
        config.set('input', 'get_parse_id', 'y')
        
        try:
            with open(fn, 'r') as cfg_file:
                config.read_file(cfg_file)
        except FileNotFoundError:
            with open(fn, 'w') as cfg_file:
                config.write(cfg_file)
        
        self.league.set(config.get('defaults', 'league'))
        self.currency.set(config.get('defaults', 'currency'))
        self.maxprice.set(float(config.get('defaults', 'maxprice')))
        self.minprice.set(float(config.get('defaults', 'minprice')))
        
        self.max_console_size = int(config.get('output', 'max_console_size'))
        self.slim = True if config.get('output', 'slim') == 'y' else False
        self.clipboard = True if config.get('output', 'clipboard') == 'y' else False
        self.log = True if config.get('output', 'log') == 'y' else False
        if self.log:
            self.log_path = config.get('output', 'log_path')
            
        self.get_parse_id = True if config.get('input', 'get_parse_id') == 'y' else False
        if self.get_parse_id:
            self.option_parse_id.configure(state='disabled')
        
    def create_search_results(self):
        """Creates the search results pane."""
        self.results_frame = ttk.Frame(self)
        self.results_frame.grid(row=0, column=0, rowspan=15, columnspan=8, padx=5, pady=5)
        
        self.results_text = tk.Text(self.results_frame, height=20, width=76)
        self.results_text.grid(row=0, column=0)
        self.results_text.configure(state='disabled')
        
        self.results_scroll = tk.Scrollbar(self.results_frame, command=self.results_text.yview)
        self.results_scroll.grid(row=0, column=1, sticky=tk.N+tk.S)
        
        self.results_text['yscrollcommand'] = self.results_scroll.set
        
    def create_option_parse_id(self):
        """Creates the parse id field. Parse id determines the next
        chunk of stash data to parse.
        """
        self.label_parse_id = ttk.Label(self, text='Parse ID')
        self.label_parse_id.grid(row=0, column=8, columnspan=2, padx=5, pady=1, sticky=tk.W)
        
        self.option_parse_id = ttk.Entry(self, textvariable=self.parse_id, width=23)
        self.option_parse_id.grid(row=1, column=8, columnspan=2, padx=5, pady=1)
        
    def create_option_league(self):
        """Creates the league field. League determines the league
        that the items will be searched in.
        """
        self.label_league = ttk.Label(self, text='League')
        self.label_league.grid(row=2, column=8, columnspan=2, padx=5, pady=1, sticky=tk.W)
        
        self.option_league = ttk.Combobox(self, textvariable=self.league, state='readonly', width=20)
        self.option_league.grid(row=3, column=8, columnspan=2, padx=5, pady=1)
        self.option_league['values'] = ['Legacy', 'Hardcore Legacy', 'Standard', 'Hardcore']
        
    def create_option_maxprice(self):
        """Creates the max price field. Max price determines the
        maximum price of an item that the system will return.
        """
        self.label_maxprice = ttk.Label(self, text='Maximum Price')
        self.label_maxprice.grid(row=4, column=8, columnspan=2, padx=5, pady=1, sticky=tk.W)
        
        self.option_maxprice = ttk.Entry(self, textvariable=self.maxprice, width=10)
        self.option_maxprice.grid(row=5, column=8, padx=5, pady=1)
        self.option_maxprice.delete(0, tk.END)
        
    def create_option_minprice(self):
        """Creates the min price field. Min price determines the
        minimum price of an item that the system will return.
        """
        self.label_minprice = ttk.Label(self, text='Minimum Price')
        self.label_minprice.grid(row=6, column=8, columnspan=2, padx=5, pady=1, sticky=tk.W)
        
        self.option_minprice = ttk.Entry(self, textvariable=self.minprice, width=10)
        self.option_minprice.grid(row=7, column=8, padx=5, pady=1)
        self.option_minprice.delete(0, tk.END)
        
    def create_option_currency(self):
        """Creates the currency field. Currency determines the type
        of currency that an item will be priced in. Note that this
        script does not support currency exchange rates.
        """
        self.option_currency = []
        self.option_currency.append(ttk.Combobox(self, textvariable=self.currency, state='readonly', width=7))
        self.option_currency[0].grid(row=5, column=9, padx=5, pady=1)
        self.option_currency[0]['values'] = currency_abbreviated
        
        self.option_currency.append(ttk.Combobox(self, textvariable=self.currency, state='readonly', width=7))
        self.option_currency[1].grid(row=7, column=9, padx=5, pady=1)
        self.option_currency[1]['values'] = currency_abbreviated
        
    def create_option_terms(self):
        """Creates the terms field. Terms are not case sensitice and
        by default are delineated by a space and a comma. Terms are
        searched within the item name.
        """
        self.lable_terms = ttk.Label(self, text='Search Terms')
        self.lable_terms.grid(row=15, column=0, padx=5, pady=5)
        
        self.option_terms = ttk.Entry(self, textvariable=self.terms, width=75)
        self.option_terms.grid(row=15, column=1, columnspan=7, padx=5, pady=5, sticky=tk.W)
        
    def create_button_start(self):
        """Creates the start, which begins the automatic parsing of
        stash data.
        """
        self.button_start = ttk.Button(self, text='Start', command=self.start_parsing, width=9)
        self.button_start.grid(row=15, column=8, padx=5, pady=5)
        
    def create_button_stop(self):
        """Creates the stop button, which ends the automatic parsing
        of stash data.
        """
        self.button_stop = ttk.Button(self, text='Stop', command=self.stop_parsing, state='disabled', width=9)
        self.button_stop.grid(row=15, column=9, padx=5, pady=5)
        
    def kill(self):
        """Sets the flag to stop all functionality. Ensures that all
        subthreads have been terminated before terminating.
        """
        self.protocol('WM_DELETE_WINDOW', None)
        self.dead = True
        self.button_start.configure(state='disabled')
        self.button_stop.configure(state='disabled')
        self.option_parse_id.configure(state='disabled')
        self.option_league.configure(state='disabled')
        self.option_maxprice.configure(state='disabled')
        self.option_minprice.configure(state='disabled')
        self.option_currency[0].configure(state='disabled')
        self.option_currency[1].configure(state='disabled')
        self.option_terms.configure(state='disabled')
        for thread in self.subthreads:
            thread.kill()
        self.kill_loop()
        
    def kill_loop(self):
        """Loop that checks whether subthreads have been killed."""
        if len(self.subthreads) == 0:
            self.destroy()
        else:
            self.handle_print('Waiting for subthreads to terminate...')
        self.after(2000, self.kill_loop)
        
    def remove_thread(self, thread):
        """Removes the thread from known active subthreads."""
        self.subthreads.remove(thread)
        
    def start_parsing(self):
        """Starts the automatic parsing of stash data."""
        self.results_text.configure(state='normal')
        self.results_text.delete(1.0, tk.END)
        self.results_text.configure(state='disabled')
        self.button_start.configure(state='disabled')
        self.button_stop.configure(state='normal')
        self.option_parse_id.configure(state='disabled')
        self.option_league.configure(state='disabled')
        self.option_maxprice.configure(state='disabled')
        self.option_minprice.configure(state='disabled')
        self.option_currency[0].configure(state='disabled')
        self.option_currency[1].configure(state='disabled')
        self.option_terms.configure(state='disabled')
        self.handle_print('Starting search...')
        self.start = True
        if self.get_parse_id:
            self.parse_id.set(json.loads(urllib.request.urlopen(parse_id_api).read())['nextChangeId'])
        self.queue_parse_ids.put(self.parse_id.get())
        self.parse_stash_data()
        
    def stop_parsing(self):
        """Stops the automatic parsing of stash data."""
        self.button_start.configure(state='normal')
        self.button_stop.configure(state='disabled')
        if not self.get_parse_id:
            self.option_parse_id.configure(state='normal')
        self.option_league.configure(state='normal')
        self.option_maxprice.configure(state='normal')
        self.option_minprice.configure(state='normal')
        self.option_currency[0].configure(state='normal')
        self.option_currency[1].configure(state='normal')
        self.option_terms.configure(state='normal')
        self.handle_print('Stopping search...')
        self.start = False
        for thread in self.subthreads:
            thread.kill()
        
    def parse_stash_data(self):
        """If there exists a new id to parse, spawns a new thread to
        parse the last id.
        """
        if self.start and not self.dead:
            parse_id = None
            while not self.queue_parse_ids.empty():
                parse_id = self.queue_parse_ids.get()
            if parse_id is not None:
                self.handle_print('Parsing ' + parse_id + '...')
                self.subthreads.append(pt.ParserThread(self, parse_id, self.league.get(), self.maxprice.get(),
                                       self.minprice.get(), self.currency.get(), self.terms.get()))
                self.parse_id.set(parse_id)
            self.after(500, self.parse_stash_data)

    def make_nice_price(self, to_parse):
        """Returns the unabbreviated name of the currency."""
        price = round(float(to_parse[0]), 1)
        if price == 1.0:
            return str(price) + ' ' + currency_singular[currency_abbreviated.index(to_parse[1])]
        else:
            return str(price) + ' ' + currency_plural[currency_abbreviated.index(to_parse[1])]

    def check_queue(self):
        """Checks whether any threads have reported results and, if
        so, copies a message to the clipboard and reports them to the
        results pane.
        """
        while not self.queue_results.empty():
            self.handle_result(self.queue_results.get())
        self.after(500, self.check_queue)
        
    def handle_print(self, string):
        """Handles printing to the results pane."""
        new_string = time.strftime('[%Y-%m-%d %H:%M] ') + string + '\n'
        scroll = (self.results_scroll.get()[1] == 1.0)
        
        self.results_text.configure(state='normal')
        self.results_text.insert(tk.END, new_string)
        while float(self.results_text.index(tk.END)) > self.max_console_size + 2:
            self.results_text.delete(1.0, 2.0)
        self.results_text.configure(state='disabled')
        
        if scroll:
            self.results_text.see(tk.END)
        
        if self.log:
            try:
                with open(self.log_path, 'a') as log_file:
                    log_file.write(new_string)
            except OSError:
                self.log = False
        
    def handle_result(self, result):
        """Handles one result from the queue."""
        string = '@ {name} Hi, I would like you buy you {item} ' \
                 'listed for {price} in {league} ' \
                 '(stash tab {stash}; position: left {x}, top {y})'
        string = string.format(name=result['name'], item=result['item'],
                               price=self.make_nice_price(result['price'].group(2, 3)), league=result['league'],
                               stash=result['stash'], x=result['x'], y=result['y'])
        if self.clipboard:
            self.clipboard_clear()
            self.clipboard_append(string)
        self.handle_print('Found result: ' + string)
        self.subthreads.append(bt.BeepThread(self))
            
if __name__ == '__main__':
    App().mainloop()