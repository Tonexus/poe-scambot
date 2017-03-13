import re
import threading

import requests

stash_api = 'http://pathofexile.com/api/public-stash-tabs?id='

class ParserThread(threading.Thread):
    """Thread that parses each chunk of stash API data"""

    def __init__(self, spawner, parse_id, league, maxprice, minprice, currency, regex):
        """Initializes the thread with a reference to the creator thread and specified seearch parameters."""
        threading.Thread.__init__(self)
        self.dead = False
        self.spawner = spawner
        self.parse_id = parse_id
        self.league = league
        self.maxprice = maxprice
        self.minprice = minprice
        self.currency = currency
        self.regex = re.compile(regex, re.IGNORECASE)
        self.start()
        
    def get_stashes(self):
        """Reads the JSON data from the stash API into a dictionary.
        Also returns the id of the next chunk of data to the main thread via queue.
        """
        stash_data = requests.get(stash_api + self.parse_id).json()
        self.spawner.queue_parse_ids.put(stash_data['next_change_id'])
        self.stashes = stash_data['stashes']
    
    def parse_stashes(self):
        """Parses the stash data for items matching input specifications.
        Returns matching items to the main thread via queue.
        """
        price_regex = re.compile('~(b/o|price) ([0-9]+) (' + self.currency + ')')
        for stash in self.stashes:
            for item in stash['items']:
                if self.dead:
                    return
                if item['league'] == self.league:
                    full_name = item['typeLine'] if item['name'] == '' else item['name'][28:] + ' ' + item['typeLine']
                    full_text = ' '.join([full_name] + (item['implicitMods'] if 'implicitMods' in item else []) + (item['explicitMods'] if 'explicitMods' in item else []))
                    if self.regex.search(full_text):
                        price_regex_match = price_regex.match(stash['stash'])
                        try:
                            price_regex_match = price_regex.match(item['note'])
                            if price_regex_match and float(price_regex_match.group(2)) <= self.maxprice \
                               and float(price_regex_match.group(2)) >= self.minprice:
                                self.spawner.queue_results.put({'name':stash['lastCharacterName'], 'item':full_name,
                                                                'price':price_regex_match, 'league':item['league'],
                                                                'stash':stash['stash'], 'x':item['x'], 'y':item['y']})
                        except KeyError:
                            pass
        
    def run(self):
        """Main actions of thread.
        First reads the API into an dictionary before parsing that dictionary for the desired items.
        """
        self.get_stashes()
        self.parse_stashes()
        self.spawner.remove_thread(self)
    
    def kill(self):
        """Sets the flag to stop processing and terminate the thread."""
        self.dead = True