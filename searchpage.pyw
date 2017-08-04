import re
import tkinter as tk
from tkinter import ttk

import constants

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

        return {'league': self.league.get(), 'maxprice': maxprice, 'minprice': minprice, 'sockets': sockets,
                'links': links, 'frame type': constants.FRAME_TYPES.index(self.frame_type.get()),
                'corrupted': self.corrupted.get(), 'crafted': self.crafted.get(), 'regex': re.compile(self.regex.get(), re.IGNORECASE)}