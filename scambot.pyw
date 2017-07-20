import time
import os
import queue
import configparser
import threading
import tkinter as tk
from tkinter import ttk

import requests

import searchparameters as sp
import parserthread as pt
import beepthread as bt

CURRENCY_ABBREVIATED = ['alt', 'fuse', 'alch', 'chaos', 'gcp', 'exa',
                        'chrom', 'jew', 'chance', 'chisel', 'scour',
                        'blessed', 'regret', 'regal', 'divine',
                        'vaal']

CURRENCY_NICE = ['alteration', 'fusing', 'alchemy', 'chaos', 'gcp',
                 'exalted', 'chromatic', 'jewellers', 'chance',
                 'chisel', 'scouring', 'blessed', 'regret', 'regal',
                 'divine', 'vaal']

LEAGUES = ['Legacy', 'Standard', 'Hardcore']

FRAME_TYPES = ['Normal', 'Magic', 'Rare', 'Unique', 'Gem',
               'Currency', 'Divination Card', 'Quest Item',
               'Prophecy', 'Relic']

NINJA_API = 'http://api.poe.ninja/api/Data/GetStats'

DEFAULT_LEAGUE = LEAGUES[0]
DEFAULT_MINPRICE = 1.0
DEFAULT_MAXPRICE = 20.0
DEFAULT_CURRENCY = CURRENCY_ABBREVIATED[3]
DEFAULT_SOCKETS = 0
DEFAULT_LINKS = 0
DEFAULT_FRAME_TYPE = FRAME_TYPES[3]

DEFAULT_REFRESH_RATE = 750

DEFAULT_CONSOLE_SIZE = 1000
DEFAULT_BEEP_DURATION = 1000
DEFAULT_BEEP_FREQUENCY = 440

RESULTS_WIDTH = 7
RESULTS_HEIGHT = 13

class App(tk.Tk):
    """App that centralizes all of the live search functionality with
    a simple UI.
    """

    def __init__(self):
        """Initializes the app."""
        tk.Tk.__init__(self)
        self.title('PoE ScamBot')
        self.geometry('900x500+900+200')
        self.configure(bd=5)
        self.resizable(False, False)
        self.iconbitmap(os.path.join(os.path.dirname(__file__), 'favicon.ico'))
        self.protocol('WM_DELETE_WINDOW', self.kill)
        
        self.queue_results = queue.Queue()
        self.queue_parse_ids = queue.Queue()
        self.start = False
        self.dead = False
        
        for i in range(RESULTS_WIDTH + 2):
            self.columnconfigure(i, weight=1, minsize=70)
        for i in range(RESULTS_HEIGHT + 1):
            self.rowconfigure(i, weight=1, minsize=35)
        
        self.league = tk.StringVar()
        self.maxprice = tk.StringVar()
        self.minprice = tk.StringVar()
        self.currency = tk.StringVar()
        self.sockets = tk.StringVar()
        self.links = tk.StringVar()
        self.frame_type = tk.StringVar()
        self.corrupted = tk.BooleanVar()
        self.crafted = tk.BooleanVar()
        self.regex = tk.StringVar()
        
        self.create_widgets()
        
        self.parse_config()
        
        self.after(50, self.check_queue)

    def create_widgets(self):
        """Creates the app\'s widgets."""
        self.create_search_results()
        self.create_option_league()
        self.create_option_maxprice()
        self.create_option_currency()
        self.create_option_minprice()
        self.create_option_sockets()
        self.create_option_links()
        self.create_option_frame_type()
        self.create_option_corrupted()
        self.create_option_crafted()
        self.create_option_regex()
        self.create_button_start()
        self.create_button_stop()
        self.bind('<Return>', lambda event: self.start_parsing())
        
    def parse_config(self):
        """Parses the config file \'scambot.cfg\'.
        """
        fn = 'scambot.cfg'
        config = configparser.ConfigParser()
        config['defaults'] = {}
        config['system'] = {}
        config['output'] = {}
        
        config.set('defaults', 'league', DEFAULT_LEAGUE)
        config.set('defaults', 'maxprice', str(DEFAULT_MAXPRICE))
        config.set('defaults', 'minprice', str(DEFAULT_MINPRICE))
        config.set('defaults', 'currency', DEFAULT_CURRENCY)
        config.set('defaults', 'sockets', str(DEFAULT_SOCKETS))
        config.set('defaults', 'links', str(DEFAULT_LINKS))
        config.set('defaults', 'frame type', DEFAULT_FRAME_TYPE)
        config.set('defaults', 'corrupted', 'y')
        config.set('defaults', 'crafted', 'y')
        
        config.set('system', 'refresh_rate', str(DEFAULT_REFRESH_RATE))
        
        config.set('output', 'max_console_size', str(DEFAULT_CONSOLE_SIZE))
        config.set('output', 'beep_frequency', str(DEFAULT_BEEP_FREQUENCY))
        config.set('output', 'beep_duration', str(DEFAULT_BEEP_DURATION))
        config.set('output', 'clipboard', 'y')
        config.set('output', 'log', 'n')
        config.set('output', 'log_path', '')
        
        try:
            with open(fn, 'r') as cfg_file:
                config.read_file(cfg_file)
        except FileNotFoundError:
            pass
        
        if config.get('defaults', 'league') in LEAGUES:
            self.league.set(config.get('defaults', 'league'))
        else:
            self.league.set(DEFAULT_LEAGUE)
        self.maxprice.set(config.get('defaults', 'maxprice'))
        self.minprice.set(config.get('defaults', 'minprice'))
        if config.get('defaults', 'currency') in CURRENCY_ABBREVIATED:
            self.currency.set(config.get('defaults', 'currency'))
        else:
            self.currency.set(DEFAULT_CURRENCY)
        self.sockets.set(config.get('defaults', 'sockets'))
        self.links.set(config.get('defaults', 'links'))
        if config.get('defaults', 'frame type') in FRAME_TYPES:
            self.frame_type.set(config.get('defaults', 'frame type'))
        else:
            self.currency.set(DEFAULT_FRAME_TYPE)
        self.corrupted.set(config.get('defaults', 'corrupted') == 'y')
        self.crafted.set(config.get('defaults', 'crafted') == 'y')
        
        self.refresh_rate = int(config.get('system', 'refresh_rate'))
        
        self.max_console_size = int(config.get('output', 'max_console_size'))
        self.beep_frequency = int(config.get('output', 'beep_frequency'))
        self.beep_duration = int(config.get('output', 'beep_duration'))
        self.clipboard = config.get('output', 'clipboard') == 'y'
        self.log = config.get('output', 'log') == 'y'
        if self.log:
            self.log_path = config.get('output', 'log_path')
        
    def create_search_results(self):
        """Creates the search results pane."""
        self.results_frame = tk.Frame(self, bd=1, relief='sunken')
        self.results_frame.grid(row=0, column=0, rowspan=RESULTS_HEIGHT, columnspan=RESULTS_WIDTH, padx=5, pady=5)
        
        self.results_scroll = tk.Scrollbar(self.results_frame)
        self.results_scroll.pack(side='right', fill='y')
        
        self.results_text = tk.Text(self.results_frame, bd=0, height=30, width=100)
        self.results_text.pack()
        self.results_text.configure(state='disabled')
        
        self.results_scroll.configure(command=self.results_text.yview)
        self.results_text['yscrollcommand'] = self.results_scroll.set
        
    def create_option_league(self):
        """Creates the league field. League determines the league
        that the items will be searched in.
        """
        self.label_league = ttk.Label(self, text='League')
        self.label_league.grid(row=0, column=RESULTS_WIDTH, columnspan=2, padx=5, pady=1, sticky='w')
        
        self.option_league = ttk.Combobox(self, textvariable=self.league, state='readonly', width=0)
        self.option_league.grid(row=1, column=RESULTS_WIDTH, columnspan=2, padx=5, pady=1, sticky='ew')
        self.option_league['values'] = LEAGUES
        
    def create_option_maxprice(self):
        """Creates the max price field. Max price determines the
        maximum price of an item that the system will return.
        """
        self.label_maxprice = ttk.Label(self, text='Maximum Price')
        self.label_maxprice.grid(row=2, column=RESULTS_WIDTH, columnspan=2, padx=5, pady=1, sticky='w')
        
        self.option_maxprice = ttk.Entry(self, textvariable=self.maxprice, width=0)
        self.option_maxprice.grid(row=3, column=RESULTS_WIDTH, padx=5, pady=1, sticky='ew')
        
    def create_option_minprice(self):
        """Creates the min price field. Min price determines the
        minimum price of an item that the system will return.
        """
        self.label_minprice = ttk.Label(self, text='Minimum Price')
        self.label_minprice.grid(row=4, column=RESULTS_WIDTH, columnspan=2, padx=5, pady=1, sticky='w')
        
        self.option_minprice = ttk.Entry(self, textvariable=self.minprice, width=0)
        self.option_minprice.grid(row=5, column=RESULTS_WIDTH, padx=5, pady=1, sticky='ew')
        
    def create_option_currency(self):
        """Creates the currency field. Currency determines the type
        of currency that an item will be priced in. Note that this
        script does not support currency exchange rates.
        """
        self.option_currency = []
        self.option_currency.append(ttk.Combobox(self, textvariable=self.currency, state='readonly', width=0))
        self.option_currency[0].grid(row=3, column=RESULTS_WIDTH + 1, padx=5, pady=1, sticky='ew')
        self.option_currency[0]['values'] = CURRENCY_ABBREVIATED
        
        self.option_currency.append(ttk.Combobox(self, textvariable=self.currency, state='readonly', width=0))
        self.option_currency[1].grid(row=5, column=RESULTS_WIDTH + 1, padx=5, pady=1, sticky='ew')
        self.option_currency[1]['values'] = CURRENCY_ABBREVIATED
        
    def create_option_sockets(self):
        """Creates the sockets field. Sockets determines the minimum
        number of sockets that the item must have.
        """
        self.label_sockets = ttk.Label(self, text='Sockets')
        self.label_sockets.grid(row=6, column=RESULTS_WIDTH, padx=5, pady=1, sticky='w')
        
        self.option_sockets = ttk.Entry(self, textvariable=self.sockets, width=0)
        self.option_sockets.grid(row=7, column=RESULTS_WIDTH, padx=5, pady=1, sticky='ew')
        
    def create_option_links(self):
        """Creates the links field. Links determines the minimum
        number of links that the item must have.
        """
        self.label_links = ttk.Label(self, text='Links')
        self.label_links.grid(row=6, column=RESULTS_WIDTH + 1, padx=5, pady=1, sticky='w')
        
        self.option_links = ttk.Entry(self, textvariable=self.links, width=0)
        self.option_links.grid(row=7, column=RESULTS_WIDTH + 1, padx=5, pady=1, sticky='ew')
        
    def create_option_frame_type(self):
        """Creates the frame type field. Frame type determines what
        rarity the item must have.
        """
        self.label_frame_type = ttk.Label(self, text='Rarity')
        self.label_frame_type.grid(row=8, column=RESULTS_WIDTH, columnspan=2, padx=5, pady=1, sticky='w')
        
        self.option_frame_type = ttk.Combobox(self, textvariable=self.frame_type, state='readonly', width=0)
        self.option_frame_type.grid(row=9, column=RESULTS_WIDTH, columnspan=2, padx=5, pady=1, sticky='ew')
        self.option_frame_type['values'] = FRAME_TYPES
        
    def create_option_corrupted(self):
        """Creates the corrupted field. Corrupted determines whether
        items that have been corrupted are included.
        """
        self.option_corrupted = ttk.Checkbutton(self, text='Allow Corrupted', variable=self.corrupted)
        self.option_corrupted.grid(row=10, column=RESULTS_WIDTH, columnspan=2, padx=5, pady=1, sticky='w')
        
    def create_option_crafted(self):
        """Creates the crafted field. Crafted determines whether
        items that have been crafted are included.
        """
        self.option_crafted = ttk.Checkbutton(self, text='Allow Crafted', variable=self.crafted)
        self.option_crafted.grid(row=11, column=RESULTS_WIDTH, columnspan=2, padx=5, pady=1, sticky='w')
        
    def create_option_regex(self):
        """Creates the regex field. Regex is not case sensitice and
        by default are delineated by a space and a comma. Regex is
        searched within the item text (name, implicit mods, and
        explicit mods).
        """
        self.lable_regex = ttk.Label(self, text='Search Regex')
        self.lable_regex.grid(row=RESULTS_HEIGHT, column=0, padx=5, pady=5)
        
        self.option_regex = ttk.Entry(self, textvariable=self.regex, width=100)
        self.option_regex.grid(row=RESULTS_HEIGHT, column=1, columnspan=RESULTS_WIDTH - 1, padx=5, pady=5, sticky='w')
        self.option_regex.focus_set()
        
    def create_button_start(self):
        """Creates the start, which begins the automatic parsing of
        stash data.
        """
        self.button_start = ttk.Button(self, text='Start', command=self.start_parsing, width=0)
        self.button_start.grid(row=RESULTS_HEIGHT, column=RESULTS_WIDTH, padx=5, pady=5, sticky='ew')
        
    def create_button_stop(self):
        """Creates the stop button, which ends the automatic parsing
        of stash data.
        """
        self.button_stop = ttk.Button(self, text='Stop', command=self.stop_parsing, state='disabled', width=0)
        self.button_stop.grid(row=RESULTS_HEIGHT, column=RESULTS_WIDTH + 1, padx=5, pady=5, sticky='ew')
        
    def kill(self):
        """Sets the flag to stop all functionality. Ensures that all
        subthreads have been terminated before terminating.
        """
        self.protocol('WM_DELETE_WINDOW', None)
        self.dead = True
        self.unbind('<Return>')
        self.button_start.configure(state='disabled')
        self.button_stop.configure(state='disabled')
        self.option_league.configure(state='disabled')
        self.option_maxprice.configure(state='disabled')
        self.option_minprice.configure(state='disabled')
        self.option_currency[0].configure(state='disabled')
        self.option_currency[1].configure(state='disabled')
        self.option_sockets.configure(state='disabled')
        self.option_links.configure(state='disabled')
        self.option_frame_type.configure(state='disabled')
        self.option_corrupted.configure(state='disabled')
        self.option_crafted.configure(state='disabled')
        self.option_regex.configure(state='disabled')
        for thread in threading.enumerate():
            if not thread == threading.main_thread():
                thread.kill()
        self.handle_print('Waiting for subthreads to terminate...')
        self.kill_loop()
        
    def kill_loop(self):
        """Loop that checks whether subthreads have been killed."""
        if threading.active_count() == 1:
            self.destroy()
        self.after(50, self.kill_loop)
        
    def start_parsing(self):
        """Starts the automatic parsing of stash data."""
        self.bind('<Return>', lambda event: self.stop_parsing())
        self.button_start.configure(state='disabled')
        self.button_stop.configure(state='normal')
        self.option_league.configure(state='disabled')
        self.option_maxprice.configure(state='disabled')
        self.option_minprice.configure(state='disabled')
        self.option_currency[0].configure(state='disabled')
        self.option_currency[1].configure(state='disabled')
        self.option_sockets.configure(state='disabled')
        self.option_links.configure(state='disabled')
        self.option_frame_type.configure(state='disabled')
        self.option_corrupted.configure(state='disabled')
        self.option_crafted.configure(state='disabled')
        self.option_regex.configure(state='disabled')
        self.handle_print('Starting search...')
        self.start = True
        self.queue_parse_ids.put(requests.get(NINJA_API).json()['nextBetaChangeId'])
        self.parse_stash_data()
        
    def stop_parsing(self):
        """Stops the automatic parsing of stash data."""
        self.bind('<Return>', lambda event: self.start_parsing())
        self.button_start.configure(state='normal')
        self.button_stop.configure(state='disabled')
        self.option_league.configure(state='readonly')
        self.option_maxprice.configure(state='normal')
        self.option_minprice.configure(state='normal')
        self.option_currency[0].configure(state='readonly')
        self.option_currency[1].configure(state='readonly')
        self.option_sockets.configure(state='enabled')
        self.option_links.configure(state='enabled')
        self.option_frame_type.configure(state='enabled')
        self.option_corrupted.configure(state='enabled')
        self.option_crafted.configure(state='enabled')
        self.option_regex.configure(state='normal')
        self.handle_print('Stopping search...')
        self.start = False
        for thread in threading.enumerate():
            if not thread == threading.main_thread():
                thread.kill()
        
    def parse_stash_data(self):
        """If there exists a new id to parse, spawns a new thread to
        parse the last id.
        """
        if self.start and not self.dead:
            parse_id = None
            while not self.queue_parse_ids.empty():
                parse_id = self.queue_parse_ids.get()
            if parse_id:
                self.handle_print('Parsing ' + parse_id + '...')
                try:
                    maxprice = float(self.maxprice.get())
                except ValueError:
                    maxprice = DEFAULT_MAXPRICE
                try:
                    minprice = float(self.minprice.get())
                except ValueError:
                    minprice = DEFAULT_MINPRICE
                try:
                    sockets = int(self.sockets.get())
                except ValueError:
                    sockets = DEFAULT_SOCKETS
                try:
                    links = int(self.links.get())
                except ValueError:
                    links = DEFAULT_LINKS
                params = sp.SearchParameters(self.league.get(), maxprice, minprice,
                                             self.currency.get(), sockets, links,
                                             FRAME_TYPES.index(self.frame_type.get()),
                                             self.corrupted.get(), self.crafted.get(),
                                             self.regex.get())
                pt.ParserThread(self, parse_id, params)
                self.after(self.refresh_rate, self.parse_stash_data)
            else:
                self.after(50, self.parse_stash_data)

    def check_queue(self):
        """Checks whether any threads have reported results and, if
        so, copies a message to the clipboard and reports them to the
        results pane.
        """
        if not self.queue_results.empty():
            self.handle_result(self.queue_results.get())
        self.after(50, self.check_queue)
        
    def handle_result(self, result):
        """Handles one result from the queue."""
        if result.get('error', None):
            self.handle_print('Rate limited. Trying again...')
        else:
            string = '@{name} Hi, I would like to buy your {item} ' \
                     'listed for {price} in {league} ' \
                     '(stash tab \"{stash}\"; position: left {x}, top {y})'
            string = string.format(name=result['name'], item=result['item'],
                                   price=self.make_nice_price(result['price'].group(2, 3)),
                                   league=result['league'], stash=result['stash'],
                                   x=result['x'], y=result['y'])
            if self.clipboard:
                self.clipboard_clear()
                self.clipboard_append(string)
            self.handle_print('Found result: ' + string)
            bt.BeepThread(self.beep_frequency, self.beep_duration)
        
    def handle_print(self, string):
        """Handles printing to the results pane."""
        new_string = time.strftime('[%y-%m-%d %H:%M:%S] ') + string + '\n'
        scroll = (self.results_scroll.get()[1] == 1.0)
        
        self.results_text.configure(state='normal')
        self.results_text.insert('end', new_string)
        while float(self.results_text.index('end')) > self.max_console_size + 2:
            self.results_text.delete(1.0, 2.0)
        self.results_text.configure(state='disabled')
        
        if scroll:
            self.results_text.see('end')
        
        if self.log:
            try:
                with open(self.log_path, 'a') as log_file:
                    log_file.write(new_string)
            except OSError:
                self.log = False

    def make_nice_price(self, to_parse):
        """Returns the unabbreviated name of the currency."""
        price = round(float(to_parse[0]), 1)
        if price.is_integer():
            price = int(price)
        return str(price) + ' ' + CURRENCY_NICE[CURRENCY_ABBREVIATED.index(to_parse[1])]
            
if __name__ == '__main__':
    App().mainloop()