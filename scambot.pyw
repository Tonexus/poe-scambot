import time
import os
import queue
import configparser
import threading
import tkinter as tk
from tkinter import ttk

import requests

import constants
import searchparameters as sp
import parserthread as pt
import beepthread as bt
import exchangerates as er

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
        
        self.search_pages = []
        self.exchange_rates = {}
        self.queue_results = queue.Queue()
        self.queue_parse_ids = queue.Queue()
        self.queue_exchange_rates = queue.Queue()
        self.start = False
        self.dead = False
        
        for i in range(constants.RESULTS_WIDTH + 2):
            self.columnconfigure(i, weight=1, minsize=70)
        for i in range(constants.RESULTS_HEIGHT + 1):
            self.rowconfigure(i, weight=1, minsize=35)
        
        self.parse_config()
        
        self.create_widgets()
        
        for league in constants.LEAGUES:
            self.handle_print('Retrieving exchange rates for ' + league + ' league...')
            er.ExchangeRatesThread(self, league)
        
        self.after(50, self.check_queue)

    def create_widgets(self):
        """Creates the app\'s widgets."""
        self.create_search_results()
        self.create_params_notebook()
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
        
        config.set('defaults', 'league', constants.DEFAULT_LEAGUE)
        config.set('defaults', 'maxprice', str(constants.DEFAULT_MAXPRICE))
        config.set('defaults', 'minprice', str(constants.DEFAULT_MINPRICE))
        config.set('defaults', 'currency', constants.DEFAULT_CURRENCY)
        config.set('defaults', 'sockets', str(constants.DEFAULT_SOCKETS))
        config.set('defaults', 'links', str(constants.DEFAULT_LINKS))
        config.set('defaults', 'frame type', constants.DEFAULT_FRAME_TYPE)
        config.set('defaults', 'corrupted', 'y')
        config.set('defaults', 'crafted', 'y')
        
        config.set('system', 'refresh_rate', str(constants.DEFAULT_REFRESH_RATE))
        
        config.set('output', 'max_console_size', str(constants.DEFAULT_CONSOLE_SIZE))
        config.set('output', 'beep_frequency', str(constants.DEFAULT_BEEP_FREQUENCY))
        config.set('output', 'beep_duration', str(constants.DEFAULT_BEEP_DURATION))
        config.set('output', 'clipboard', 'y')
        config.set('output', 'log', 'n')
        config.set('output', 'log_path', '')
        
        try:
            with open(fn, 'r') as cfg_file:
                config.read_file(cfg_file)
        except FileNotFoundError:
            pass
        
        if config.get('defaults', 'league') in constants.LEAGUES:
            self.league = config.get('defaults', 'league')
        else:
            self.league = constants.DEFAULT_LEAGUE
        self.maxprice = config.get('defaults', 'maxprice')
        self.minprice = config.get('defaults', 'minprice')
        if config.get('defaults', 'currency') in constants.CURRENCY_ABBREVIATED:
            self.currency = config.get('defaults', 'currency')
        else:
            self.currency = constants.DEFAULT_CURRENCY
        self.sockets = config.get('defaults', 'sockets')
        self.links = config.get('defaults', 'links')
        if config.get('defaults', 'frame type') in constants.FRAME_TYPES:
            self.frame_type = config.get('defaults', 'frame type')
        else:
            self.frame_type = constants.DEFAULT_FRAME_TYPE
        self.corrupted = (config.get('defaults', 'corrupted') == 'y')
        self.crafted = (config.get('defaults', 'crafted') == 'y')
        
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
        self.results_frame.grid(row=0, column=0, rowspan=constants.RESULTS_HEIGHT, columnspan=constants.RESULTS_WIDTH, padx=5, pady=5)
        
        self.results_scroll = tk.Scrollbar(self.results_frame)
        self.results_scroll.pack(side='right', fill='y')
        
        self.results_text = tk.Text(self.results_frame, bd=0, height=30, width=100)
        self.results_text.pack()
        self.results_text.configure(state='disabled')
        
        self.results_scroll.configure(command=self.results_text.yview)
        self.results_text['yscrollcommand'] = self.results_scroll.set
    
    def create_params_notebook(self):
        """Creates the notebook (tabs) for each set of search parameters"""
        self.params_notebook = ttk.Notebook(self)
        self.params_notebook.grid(row=0, column=constants.RESULTS_WIDTH, rowspan=constants.RESULTS_HEIGHT, columnspan=4, padx=5, pady=5, sticky='nesw')
        
        self.search_pages.append(SearchPage(self.params_notebook))
        self.search_pages.append(SearchPage(self.params_notebook))
        self.search_pages.append(SearchPage(self.params_notebook))
        self.search_pages.append(SearchPage(self.params_notebook))
        self.params_notebook.add(self.search_pages[0], text='  1  ')
        self.params_notebook.add(self.search_pages[1], text='  2  ')
        self.params_notebook.add(self.search_pages[2], text='  3  ')
        self.params_notebook.add(self.search_pages[3], text='  4  ')
        
    def create_button_start(self):
        """Creates the start, which begins the automatic parsing of
        stash data.
        """
        self.button_start = ttk.Button(self, text='Start', command=self.start_parsing, width=0)
        self.button_start.grid(row=constants.RESULTS_HEIGHT, column=constants.RESULTS_WIDTH, padx=5, pady=5, sticky='ew')
        
    def create_button_stop(self):
        """Creates the stop button, which ends the automatic parsing
        of stash data.
        """
        self.button_stop = ttk.Button(self, text='Stop', command=self.stop_parsing, state='disabled', width=0)
        self.button_stop.grid(row=constants.RESULTS_HEIGHT, column=constants.RESULTS_WIDTH + 1, padx=5, pady=5, sticky='ew')
        
    def kill(self):
        """Sets the flag to stop all functionality. Ensures that all
        subthreads have been terminated before terminating.
        """
        self.protocol('WM_DELETE_WINDOW', None)
        self.dead = True
        self.unbind('<Return>')
        self.button_start.configure(state='disabled')
        self.button_stop.configure(state='disabled')
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
        self.handle_print('Starting search...')
        self.start = True
        self.queue_parse_ids.put(requests.get(constants.NEXT_API).json()['nextChangeId'])
        self.parse_stash_data()
        
    def stop_parsing(self):
        """Stops the automatic parsing of stash data."""
        self.bind('<Return>', lambda event: self.start_parsing())
        self.button_start.configure(state='normal')
        self.button_stop.configure(state='disabled')
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
                params_list = []
                for page in self.search_pages:
                    params_list.append(page.get_params())
                pt.ParserThread(self, parse_id, params_list, self.exchange_rates)
                self.after(self.refresh_rate, self.parse_stash_data)
            else:
                self.after(50, self.parse_stash_data)

    def check_queue(self):
        """Checks whether any threads have reported results and, if
        so, handles the results.
        """
        if not self.queue_results.empty():
            self.handle_result(self.queue_results.get())
        if not self.queue_exchange_rates.empty():
            tuple = self.queue_exchange_rates.get()
            self.exchange_rates[tuple[0]] = tuple[1]
            self.handle_print('Successfully retrieved exchange rates for ' + tuple[0] + ' league.')
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
        return str(price) + ' ' + constants.CURRENCY_NICE[constants.CURRENCY_ABBREVIATED.index(to_parse[1])]

class SearchPage(ttk.Frame):
    """Custom widget that displays all of the search information."""

    def __init__(self, parent):
        """Initializes the search page."""
        ttk.Frame.__init__(self, parent)
        
        self.league = tk.StringVar()
        self.league.set(self.master.master.league)
        self.maxprice = tk.StringVar()
        self.maxprice.set(self.master.master.maxprice)
        self.minprice = tk.StringVar()
        self.minprice.set(self.master.master.minprice)
        self.currency = tk.StringVar()
        self.currency.set(self.master.master.currency)
        self.sockets = tk.StringVar()
        self.sockets.set(self.master.master.sockets)
        self.links = tk.StringVar()
        self.links.set(self.master.master.links)
        self.frame_type = tk.StringVar()
        self.frame_type.set(self.master.master.frame_type)
        self.corrupted = tk.BooleanVar()
        self.corrupted.set(self.master.master.corrupted)
        self.crafted = tk.BooleanVar()
        self.crafted.set(self.master.master.crafted)
        self.regex = tk.StringVar()
        
        self.create_widgets()
    
    def create_widgets(self):
        """Creates the search page\'s widgets."""
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
        
    def create_option_league(self):
        """Creates the league field. League determines the league
        that the items will be searched in.
        """
        self.label_league = ttk.Label(self, text='League')
        self.label_league.grid(row=0, column=0, columnspan=2, padx=5, pady=1, sticky='w')
        
        self.option_league = ttk.Combobox(self, textvariable=self.league, state='readonly', width=0)
        self.option_league.grid(row=1, column=0, columnspan=2, padx=5, pady=1, sticky='ew')
        self.option_league['values'] = constants.LEAGUES
        
    def create_option_maxprice(self):
        """Creates the max price field. Max price determines the
        maximum price of an item that the system will return.
        """
        self.label_maxprice = ttk.Label(self, text='Maximum Price')
        self.label_maxprice.grid(row=2, column=0, columnspan=2, padx=5, pady=1, sticky='w')
        
        self.option_maxprice = ttk.Entry(self, textvariable=self.maxprice, width=0)
        self.option_maxprice.grid(row=3, column=0, padx=5, pady=1, sticky='ew')
        
    def create_option_minprice(self):
        """Creates the min price field. Min price determines the
        minimum price of an item that the system will return.
        """
        self.label_minprice = ttk.Label(self, text='Minimum Price')
        self.label_minprice.grid(row=4, column=0, columnspan=2, padx=5, pady=1, sticky='w')
        
        self.option_minprice = ttk.Entry(self, textvariable=self.minprice, width=0)
        self.option_minprice.grid(row=5, column=0, padx=5, pady=1, sticky='ew')
        
    def create_option_currency(self):
        """Creates the currency field. Currency determines the type
        of currency that an item will be priced in. Note that this
        script does not support currency exchange rates.
        """
        self.option_currency = []
        self.option_currency.append(ttk.Combobox(self, textvariable=self.currency, state='readonly', width=0))
        self.option_currency[0].grid(row=3, column=0 + 1, padx=5, pady=1, sticky='ew')
        self.option_currency[0]['values'] = constants.CURRENCY_ABBREVIATED
        
        self.option_currency.append(ttk.Combobox(self, textvariable=self.currency, state='readonly', width=0))
        self.option_currency[1].grid(row=5, column=0 + 1, padx=5, pady=1, sticky='ew')
        self.option_currency[1]['values'] = constants.CURRENCY_ABBREVIATED
        
    def create_option_sockets(self):
        """Creates the sockets field. Sockets determines the minimum
        number of sockets that the item must have.
        """
        self.label_sockets = ttk.Label(self, text='Sockets')
        self.label_sockets.grid(row=6, column=0, padx=5, pady=1, sticky='w')
        
        self.option_sockets = ttk.Entry(self, textvariable=self.sockets, width=0)
        self.option_sockets.grid(row=7, column=0, padx=5, pady=1, sticky='ew')
        
    def create_option_links(self):
        """Creates the links field. Links determines the minimum
        number of links that the item must have.
        """
        self.label_links = ttk.Label(self, text='Links')
        self.label_links.grid(row=6, column=0 + 1, padx=5, pady=1, sticky='w')
        
        self.option_links = ttk.Entry(self, textvariable=self.links, width=0)
        self.option_links.grid(row=7, column=0 + 1, padx=5, pady=1, sticky='ew')
        
    def create_option_frame_type(self):
        """Creates the frame type field. Frame type determines what
        rarity the item must have.
        """
        self.label_frame_type = ttk.Label(self, text='Rarity')
        self.label_frame_type.grid(row=8, column=0, columnspan=2, padx=5, pady=1, sticky='w')
        
        self.option_frame_type = ttk.Combobox(self, textvariable=self.frame_type, state='readonly', width=0)
        self.option_frame_type.grid(row=9, column=0, columnspan=2, padx=5, pady=1, sticky='ew')
        self.option_frame_type['values'] = constants.FRAME_TYPES
        
    def create_option_corrupted(self):
        """Creates the corrupted field. Corrupted determines whether
        items that have been corrupted are included.
        """
        self.option_corrupted = ttk.Checkbutton(self, text='Allow Corrupted', variable=self.corrupted)
        self.option_corrupted.grid(row=10, column=0, columnspan=2, padx=5, pady=1, sticky='w')
        
    def create_option_crafted(self):
        """Creates the crafted field. Crafted determines whether
        items that have been crafted are included.
        """
        self.option_crafted = ttk.Checkbutton(self, text='Allow Crafted', variable=self.crafted)
        self.option_crafted.grid(row=11, column=0, columnspan=2, padx=5, pady=1, sticky='w')
        
    def create_option_regex(self):
        """Creates the regex field. Regex is not case sensitice and
        by default are delineated by a space and a comma. Regex is
        searched within the item text (name, implicit mods, and
        explicit mods).
        """
        self.lable_regex = ttk.Label(self, text='Search Regex')
        self.lable_regex.grid(row=12, column=0, columnspan=2, padx=5, pady=1, sticky='w')
        
        self.option_regex = ttk.Entry(self, textvariable=self.regex, width=0)
        self.option_regex.grid(row=13, column=0, columnspan=2, padx=5, pady=1, sticky='ew')
        self.option_regex.focus_set()
    
    def get_params(self):
        """Returns the search parameters"""
        try:
            maxprice = float(self.maxprice.get())
        except ValueError:
            maxprice = constants.DEFAULT_MAXPRICE
        maxprice *= self.master.master.exchange_rates.get(self.league.get()).get(constants.CURRENCY_FULL[constants.CURRENCY_ABBREVIATED.index(self.currency.get())], 1.0)
        
        try:
            minprice = float(self.minprice.get())
        except ValueError:
            minprice = constants.DEFAULT_MINPRICE
        minprice *= self.master.master.exchange_rates.get(self.league.get()).get(constants.CURRENCY_FULL[constants.CURRENCY_ABBREVIATED.index(self.currency.get())], 1.0)
        
        try:
            sockets = int(self.sockets.get())
        except ValueError:
            sockets = constants.DEFAULT_SOCKETS
        
        try:
            links = int(self.links.get())
        except ValueError:
            links = constants.DEFAULT_LINKS
        
        return sp.SearchParameters(self.league.get(), maxprice, minprice, sockets, links,
                                   constants.FRAME_TYPES.index(self.frame_type.get()),
                                   self.corrupted.get(), self.crafted.get(), self.regex.get())
        
if __name__ == '__main__':
    App().mainloop()