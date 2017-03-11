import argparse
import urllib2
import json
import re

parser = argparse.ArgumentParser(description='Rapid searching item searching via the Path of Exile stash tab API')
parser.add_argument('init_id', help='id for first page of api to be searched (can usually be found at http://poe.ninja/stats)')
parser.add_argument('league', help='the league to search')
parser.add_argument('search_terms', nargs='+', help='the terms used to search')

args = vars(parser.parse_args())

currency_abbreviated = ['alt', 'fuse', 'alc', 'chaos', 'gcp', 'exa', 'chrom', 'jew', 'chance', 'chisel', 'scour', 'blessed', 'regret', 'regal', 'divine', 'vaal']
currency_single = ['Orb of Alteration', 'Orb of Fusing', 'Orb of Alchemy', 'Chaos Orb', 'Gemcutter\'s Prism', 'Exalted Orb', 'Chromatic Orb', 'Jeweller\'s Orb', 'Orb of Chance', 'Cartographer\'s Chisel', 'Orb of Scouring', 'Blessed Orb', 'Orb of Regret', 'Regal Orb', 'Divine Orb', 'Vaal Orb']
currency_plural = ['Orbs of Alteration', 'Orbs of Fusing', 'Orbs of Alchemy', 'Chaos Orbs', 'Gemcutter\'s Prisms', 'Exalted Orbs', 'Chromatic Orbs', 'Jeweller\'s Orbs', 'Orbs of Chance', 'Cartographer\'s Chisels', 'Orbs of Scouring', 'Blessed Orbs', 'Orbs of Regret', 'Regal Orbs', 'Divine Orbs', 'Vaal Orbs']

price_regex = re.compile('~(b/o|price) ([0-9]+) (alt|fuse|alch|chaos|gcp|exa|chrom|jew|chance|chisel|scour|blessed|regret|regal|divine|vaal)')

stash_api = 'http://pathofexile.com/api/public-stash-tabs?id='
league = args['league']
search_terms = args['search_terms']

def parse_price(to_parse):
    price = round(float(to_parse[0]), 1)
    
    if price == 1.0:
        return str(price) + ' ' + currency_single[currency_abbreviated.index(to_parse[1])]
    else:
        return str(price) + ' ' + currency_plural[currency_abbreviated.index(to_parse[1])]

def parse_stash_data(parse_id):
    stash_data = json.loads(urllib2.urlopen(stash_api + parse_id).read())
    
    for stash in stash_data['stashes']:
        for item in stash['items']:
            if item['league'] == league:
                for search_term in search_terms:
                    if search_term in item['name']:
                        price_regex_match = price_regex.match(stash['stash'])
                        try:
                            price_regex_match = price_regex.match(item['note'])
                        except KeyError:
                            pass
                        if price_regex_match:
                            print '@' + stash['accountName'] + ' Hi, I would like to buy your ' + item['name'][28:] + \
                                  ' listed for ' + parse_price(price_regex_match.group(2, 3)) + ' in ' + \
                                  item['league'] + ' (stash tab \"' + stash['stash'] + '\"; position: left ' + \
                                  str(item['x']) + ', top ' + str(item['y']) + ')'
                        else:
                            print '@' + stash['accountName'] + ' Hi, I would like to buy your ' + item['name'][28:] + \
                                  ' in ' + item['league'] + ' (stash tab \"' + stash['stash'] + '\"; position: left ' + \
                                  str(item['x']) + ', top ' + str(item['y']) + ')'
    
    return stash_data['next_change_id']

next_id = args['init_id']

for i in range (0, 5):
    next_id = parse_stash_data(next_id)