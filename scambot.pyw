import time
import queue
import configparser
import tkinter as tk
from tkinter import ttk

import requests

import parserthread as pt
import beepthread as bt

CURRENCY_ABBREVIATED = ['alt', 'fuse', 'alch', 'chaos', 'gcp', 'exa',
                        'chrom', 'jew', 'chance', 'chisel', 'scour',
                        'blessed', 'regret', 'regal', 'divine',
                        'vaal']

CURRENCY_SINGULAR = ['Orb of Alteration', 'Orb of Fusing',
                     'Orb of Alchemy', 'Chaos Orb',
                     'Gemcutter\'s Prism', 'Exalted Orb',
                     'Chromatic Orb', 'Jeweller\'s Orb',
                     'Orb of Chance', 'Cartographer\'s Chisel',
                     'Orb of Scouring', 'Blessed Orb',
                     'Orb of Regret', 'Regal Orb', 'Divine Orb',
                     'Vaal Orb']

CURRENCY_PLURAL = ['Orbs of Alteration', 'Orbs of Fusing',
                   'Orbs of Alchemy', 'Chaos Orbs',
                   'Gemcutter\'s Prisms', 'Exalted Orbs',
                   'Chromatic Orbs', 'Jeweller\'s Orbs',
                   'Orbs of Chance', 'Cartographer\'s Chisels',
                   'Orbs of Scouring', 'Blessed Orbs',
                   'Orbs of Regret', 'Regal Orbs', 'Divine Orbs',
                   'Vaal Orbs']

LEAGUES = ['Legacy', 'Hardcore Legacy', 'Standard', 'Hardcore']

NINJA_API = 'http://api.poe.ninja/api/Data/GetStats'

DEFAULT_LEAGUE = LEAGUES[0]
DEFAULT_MINPRICE = 1.0
DEFAULT_MAXPRICE = 20.0
DEFAULT_CURRENCY = CURRENCY_ABBREVIATED[3]
DEFAULT_SOCKETS = 0
DEFAULT_LINKS = 0

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
        self.iconbitmap('favicon.ico')
        self.protocol('WM_DELETE_WINDOW', self.kill)
        
        self.subthreads = []
        self.queue_results = queue.Queue()
        self.queue_parse_ids = queue.Queue()
        self.start = False
        self.dead = False
        
        self.results_width = 7
        self.results_height = 13
        
        for i in range(self.results_width + 2):
            self.columnconfigure(i, weight=1, minsize=70)
        for i in range(self.results_height + 1):
            self.rowconfigure(i, weight=1, minsize=35)
        
        self.league = tk.StringVar()
        self.maxprice = tk.StringVar()
        self.minprice = tk.StringVar()
        self.currency = tk.StringVar()
        self.sockets = tk.StringVar()
        self.links = tk.StringVar()
        self.corrupted = tk.BooleanVar()
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
        self.create_option_corrupted()
        self.create_option_regex()
        self.create_button_start()
        self.create_button_stop()
        self.bind('<Return>', lambda event: self.start_parsing())
        
    def parse_config(self):
        """Parses the config file \'scambot.cfg\'.
        """
        fn = 'scambot.cfg'
        config = configparser.ConfigParser()
        config['DEFAULT'] = {}
        
        config.set('DEFAULT', 'league', DEFAULT_LEAGUE)
        config.set('DEFAULT', 'maxprice', str(DEFAULT_MAXPRICE))
        config.set('DEFAULT', 'minprice', str(DEFAULT_MINPRICE))
        config.set('DEFAULT', 'currency', DEFAULT_CURRENCY)
        config.set('DEFAULT', 'sockets', str(DEFAULT_SOCKETS))
        config.set('DEFAULT', 'links', str(DEFAULT_LINKS))
        config.set('DEFAULT', 'corrupted', 'y')
        
        config.set('DEFAULT', 'max_console_size', '1000')
        config.set('DEFAULT', 'clipboard', 'y')
        config.set('DEFAULT', 'log', 'n')
        config.set('DEFAULT', 'log_path', '')
        
        try:
            with open(fn, 'r') as cfg_file:
                config.read_file(cfg_file)
        except FileNotFoundError:
            pass
        
        if config.get('defaults', 'league') in LEAGUES:
            self.league.set(config.get('defaults', 'league'))
        else:
            self.league.set(config.get('DEFAULT', 'league'))
        self.maxprice.set(config.get('defaults', 'maxprice'))
        self.minprice.set(config.get('defaults', 'minprice'))
        if config.get('defaults', 'currency') in CURRENCY_ABBREVIATED:
            self.currency.set(config.get('defaults', 'currency'))
        else:
            self.currency.set(config.get('DEFAULT', 'currency'))
        self.sockets.set(config.get('defaults', 'sockets'))
        self.links.set(config.get('defaults', 'links'))
        self.corrupted.set(config.get('defaults', 'corrupted') == 'y')
        
        self.max_console_size = int(config.get('output', 'max_console_size'))
        self.clipboard = config.get('output', 'clipboard') == 'y'
        self.log = config.get('output', 'log') == 'y'
        if self.log:
            self.log_path = config.get('output', 'log_path')
        
    def create_search_results(self):
        """Creates the search results pane."""
        self.results_frame = tk.Frame(self, bd=1, relief='sunken')
        self.results_frame.grid(row=0, column=0, rowspan=self.results_height, columnspan=self.results_width, padx=5, pady=5)
        
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
        self.label_league.grid(row=0, column=self.results_width, columnspan=2, padx=5, pady=1, sticky='w')
        
        self.option_league = ttk.Combobox(self, textvariable=self.league, state='readonly', width=0)
        self.option_league.grid(row=1, column=self.results_width, columnspan=2, padx=5, pady=1, sticky='ew')
        self.option_league['values'] = LEAGUES
        
    def create_option_maxprice(self):
        """Creates the max price field. Max price determines the
        maximum price of an item that the system will return.
        """
        self.label_maxprice = ttk.Label(self, text='Maximum Price')
        self.label_maxprice.grid(row=2, column=self.results_width, columnspan=2, padx=5, pady=1, sticky='w')
        
        self.option_maxprice = ttk.Entry(self, textvariable=self.maxprice, width=0)
        self.option_maxprice.grid(row=3, column=self.results_width, padx=5, pady=1, sticky='ew')
        
    def create_option_minprice(self):
        """Creates the min price field. Min price determines the
        minimum price of an item that the system will return.
        """
        self.label_minprice = ttk.Label(self, text='Minimum Price')
        self.label_minprice.grid(row=4, column=self.results_width, columnspan=2, padx=5, pady=1, sticky='w')
        
        self.option_minprice = ttk.Entry(self, textvariable=self.minprice, width=0)
        self.option_minprice.grid(row=5, column=self.results_width, padx=5, pady=1, sticky='ew')
        
    def create_option_currency(self):
        """Creates the currency field. Currency determines the type
        of currency that an item will be priced in. Note that this
        script does not support currency exchange rates.
        """
        self.option_currency = []
        self.option_currency.append(ttk.Combobox(self, textvariable=self.currency, state='readonly', width=0))
        self.option_currency[0].grid(row=3, column=self.results_width + 1, padx=5, pady=1, sticky='ew')
        self.option_currency[0]['values'] = CURRENCY_ABBREVIATED
        
        self.option_currency.append(ttk.Combobox(self, textvariable=self.currency, state='readonly', width=0))
        self.option_currency[1].grid(row=5, column=self.results_width + 1, padx=5, pady=1, sticky='ew')
        self.option_currency[1]['values'] = CURRENCY_ABBREVIATED
        
    def create_option_sockets(self):
        """Creates the sockets field. Sockets determines the minimum
        number of sockets that the item must have.
        """
        self.label_sockets = ttk.Label(self, text='Sockets')
        self.label_sockets.grid(row=6, column=self.results_width, padx=5, pady=1, sticky='w')
        
        self.option_sockets = ttk.Entry(self, textvariable=self.sockets, width=0)
        self.option_sockets.grid(row=7, column=self.results_width, padx=5, pady=1, sticky='ew')
        
    def create_option_links(self):
        """Creates the links field. Links determines the minimum
        number of links that the item must have.
        """
        self.label_links = ttk.Label(self, text='Links')
        self.label_links.grid(row=6, column=self.results_width + 1, padx=5, pady=1, sticky='w')
        
        self.option_links = ttk.Entry(self, textvariable=self.links, width=0)
        self.option_links.grid(row=7, column=self.results_width + 1, padx=5, pady=1, sticky='ew')
        
    def create_option_corrupted(self):
        """Creates the corrupted field. Corrupted determines whether
        items that have been corrupted are included.
        """
        self.option_corrupted = ttk.Checkbutton(self, text='Allow Corrupted', variable=self.corrupted)
        self.option_corrupted.grid(row=8, column=self.results_width, columnspan=2, padx=5, pady=1, sticky='w')
        
    def create_option_regex(self):
        """Creates the regex field. Regex is not case sensitice and
        by default are delineated by a space and a comma. Regex is
        searched within the item text (name, implicit mods, and
        explicit mods).
        """
        self.lable_regex = ttk.Label(self, text='Search Regex')
        self.lable_regex.grid(row=self.results_height, column=0, padx=5, pady=5)
        
        self.option_regex = ttk.Entry(self, textvariable=self.regex, width=100)
        self.option_regex.grid(row=self.results_height, column=1, columnspan=self.results_width - 1, padx=5, pady=5, sticky='w')
        self.option_regex.focus_set()
        
    def create_button_start(self):
        """Creates the start, which begins the automatic parsing of
        stash data.
        """
        self.button_start = ttk.Button(self, text='Start', command=self.start_parsing, width=0)
        self.button_start.grid(row=self.results_height, column=self.results_width, padx=5, pady=5, sticky='ew')
        
    def create_button_stop(self):
        """Creates the stop button, which ends the automatic parsing
        of stash data.
        """
        self.button_stop = ttk.Button(self, text='Stop', command=self.stop_parsing, state='disabled', width=0)
        self.button_stop.grid(row=self.results_height, column=self.results_width + 1, padx=5, pady=5, sticky='ew')
        
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
        self.option_corrupted.configure(state='disabled')
        self.option_regex.configure(state='disabled')
        for thread in self.subthreads:
            thread.kill()
        self.handle_print('Waiting for subthreads to terminate...')
        self.kill_loop()
        
    def kill_loop(self):
        """Loop that checks whether subthreads have been killed."""
        if len(self.subthreads) == 0:
            self.destroy()
        self.after(100, self.kill_loop)
        
    def remove_thread(self, thread):
        """Removes the thread from known active subthreads."""
        self.subthreads.remove(thread)
        
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
        self.option_corrupted.configure(state='disabled')
        self.option_regex.configure(state='disabled')
        self.handle_print('Starting search...')
        self.start = True
        self.queue_parse_ids.put(requests.get(NINJA_API).json()['nextChangeId'])
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
        self.option_corrupted.configure(state='enabled')
        self.option_regex.configure(state='normal')
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
                    links = DEFAULT_LINKS
                except ValueError:
                    sockets = float(self.config.get('DEFAULT', 'links'))
                self.subthreads.append(pt.ParserThread(self, parse_id, self.league.get(), maxprice,
                                       minprice, self.currency.get(), sockets,
                                       links, self.corrupted.get(), self.regex.get()))
                self.after(750, self.parse_stash_data)
            else:
                self.after(50, self.parse_stash_data)

    def make_nice_price(self, to_parse):
        """Returns the unabbreviated name of the currency."""
        price = round(float(to_parse[0]), 1)
        if price == 1.0:
            return str(price) + ' ' + CURRENCY_SINGULAR[CURRENCY_ABBREVIATED.index(to_parse[1])]
        else:
            return str(price) + ' ' + CURRENCY_PLURAL[CURRENCY_ABBREVIATED.index(to_parse[1])]

    def check_queue(self):
        """Checks whether any threads have reported results and, if
        so, copies a message to the clipboard and reports them to the
        results pane.
        """
        while not self.queue_results.empty():
            self.handle_result(self.queue_results.get())
        self.after(50, self.check_queue)
        
    def handle_result(self, result):
        """Handles one result from the queue."""
        if result.get('error', None):
            self.handle_print('Rate limited. Trying again...')
        else:
            string = '@{name} Hi, I would like to buy your {item} ' \
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
            
if __name__ == '__main__':
    App().mainloop()