import re
import threading

import requests

stash_api = 'http://pathofexile.com/api/public-stash-tabs?id='
localization = re.compile('<<.*>>')

class ParserThread(threading.Thread):
    """Thread that parses each chunk of stash API data"""

    def __init__(self, spawner, parse_id, league, maxprice, minprice, currency, sockets, links, corrupted, regex):
        """Initializes the thread with a reference to the creator thread and specified seearch parameters."""
        threading.Thread.__init__(self)
        self.dead = False
        self.spawner = spawner
        self.parse_id = parse_id
        self.league = league
        self.maxprice = maxprice
        self.minprice = minprice
        self.sockets = sockets
        self.links = links
        self.price_regex = re.compile('~(b/o|price) ([0-9]+) (' + currency + ')')
        self.corrupted = corrupted
        self.regex = re.compile(regex, re.IGNORECASE)
        self.start()
        
    def get_stashes(self):
        """Reads the JSON data from the stash API into a dictionary.
        Also returns the id of the next chunk of data to the main thread via queue.
        """
        self.stash_data = requests.get(stash_api + self.parse_id).json()
        self.spawner.queue_parse_ids.put(self.stash_data['next_change_id'])
    
    def parse_stashes(self):
        """Parses the stash data for items matching input specifications.
        Returns matching items to the main thread via queue.
        """
        for stash in self.stash_data['stashes']:
            for item in stash['items']:
                if self.dead:
                    return
                checked_item = self.check_item(item, stash['stash'])
                if checked_item:
                    self.spawner.queue_results.put({'name':stash['lastCharacterName'], 'item':checked_item[0],
                                                    'price':checked_item[1], 'league':item['league'],
                                                    'stash':stash['stash'], 'x':item['x'], 'y':item['y']})
        
    
    def check_item(self, item, stash):
        """Checks whether an item meets the search conditions."""
        if not item['league'] == self.league:
            return None
            
        if not self.corrupted and item['corrupted'] == 'True':
            return None
            
            
        # if not check links
        
        full_name = localization.sub('', ' '.join(filter(None, [item['name'], item['typeLine']])))
        full_text = ' '.join([full_name]
                             + item.get('implicitMods', [])
                             + item.get('enchantMods', [])
                             + item.get('explicitMods', [])
                             + item.get('craftedMods', []))
        
        if not self.regex.search(full_text):
            return None
            
        price_regex_match = self.price_regex.match(stash)
        try:
            price_regex_match = self.price_regex.match(item['note'])
        except KeyError:
            pass
            
        if not price_regex_match:
            return None
            
        if float(price_regex_match.group(2)) > self.maxprice or float(price_regex_match.group(2)) < self.minprice:
            return None
        
        return full_name, price_regex_match
        
    def run(self):
        """Main actions of thread.
        First reads the API into an dictionary before parsing that dictionary for the desired items.
        """
        try:
            self.get_stashes()
            self.parse_stashes()
        except KeyError:
            self.spawner.queue_parse_ids.put(self.parse_id)
            self.spawner.queue_results.put(self.stash_data)
        self.spawner.remove_thread(self)
    
    def kill(self):
        """Sets the flag to stop processing and terminate the thread."""
        self.dead = True