import tkinter as tk
from tkinter import ttk

class App(tk.Tk):

    def __init__(self):
        tk.Tk.__init__(self)
        self.title('PoE Stash Searcher')
        self.geometry('500x210+900+200')
        self.resizable(False, False)
        self.protocol('WM_DELETE_WINDOW', self.destroy)
        self.make_topmost()
        
        self.league = tk.StringVar()
        self.maxprice = tk.DoubleVar()
        self.currency = tk.StringVar()
        
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
        for i in range(0, 50):
            self.results_text.insert(tk.END, str(i) + 'Hello\n')
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
        self.option_currency['values'] = ['alt', 'fuse', 'alc', 'chaos', 'gcp', 'exa', 'chrom', 'jew', 'chance', 'chisel', 'scour', 'blessed', 'regret', 'regal', 'divine', 'vaal']
        self.option_currency.current(0)
        
    def create_label_terms(self):
        self.lable_terms = ttk.Label(self, text='Search Terms')
        self.lable_terms.grid(row=5, column=0, padx=5, pady=5, sticky=tk.W)
        
    def create_option_terms(self):
        self.option_terms = ttk.Entry(self, width=39)
        self.option_terms.grid(row=5, column=1, columnspan=2, padx=5, pady=5)
        
    def create_button_start(self):
        self.button_start = ttk.Button(self, width=9, text='Start')
        self.button_start.grid(row=5, column=4, padx=5, pady=5)
        
    def create_button_stop(self):
        self.button_stop = ttk.Button(self, width=9, text='Stop')
        self.button_stop.grid(row=5, column=5, padx=5, pady=5)

    def make_topmost(self):
        self.lift()
        self.attributes('-topmost', 1)
        self.attributes('-topmost', 0)

if __name__ == '__main__':
    App().mainloop()