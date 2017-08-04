"""All of the necessary constants."""

import re

# API urls

STASH_API = 'http://api.pathofexile.com/api/public-stash-tabs?id='
NEXT_API = 'http://api.poe.ninja/api/Data/GetStats'
RATES_API = 'http://poe.ninja/api/Data/GetCurrencyOverview?league='

# Currency strings

CURRENCY_FULL = ['Orb of Alteration', 'Orb of Fusing',
                 'Orb of Alchemy', 'Chaos Orb',
                 'Gemcutter\'s Prism', 'Exalted Orb',
                 'Chromatic Orb', 'Jeweller\'s Orb',
                 'Orb of Chance', 'Cartographer\'s Chisel',
                 'Orb of Scouring', 'Blessed Orb',
                 'Orb of Regret', 'Regal Orb', 'Divine Orb',
                 'Vaal Orb']

CURRENCY_ABBREVIATED = ['alt', 'fuse', 'alch', 'chaos', 'gcp', 'exa',
                        'chrom', 'jew', 'chance', 'chisel', 'scour',
                        'blessed', 'regret', 'regal', 'divine',
                        'vaal']

CURRENCY_NICE = ['alteration', 'fusing', 'alchemy', 'chaos', 'gcp',
                 'exalted', 'chromatic', 'jewellers', 'chance',
                 'chisel', 'scouring', 'blessed', 'regret', 'regal',
                 'divine', 'vaal']

LEAGUES = ['Harbinger', 'Hardcore Harbinger', 'Standard', 'Hardcore']

FRAME_TYPES = ['Normal', 'Magic', 'Rare', 'Unique', 'Gem',
               'Currency', 'Divination Card', 'Quest Item',
               'Prophecy', 'Relic']

# Config defaults

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

# Regex for cleaning item text

LOCALIZATION = re.compile('<<.*>>')
PRICE_REGEX = re.compile('~(b/o|price) ([0-9]+) (' + '|'.join(CURRENCY_ABBREVIATED) + ')')