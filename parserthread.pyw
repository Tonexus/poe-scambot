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
        self.sockets = max(sockets, links)
        self.links = links
        self.price_regex = re.compile('~(b/o|price) ([0-9]+) (' + currency + ')')
        self.corrupted = corrupted
        self.regex = re.compile(regex, re.IGNORECASE)
        self.start()
        
    def get_stashes(self):
        """Reads the JSON data from the stash API into a dictionary.
        Also returns the id of the next chunk of data to the main thread via queue.
        """
        stash_data = requests.get(stash_api + self.parse_id).json()
        self.spawner.queue_parse_ids.put(stash_data['next_change_id'])
        self.stashes = stash_data['stashes']
    
    def check_item(self, item, stash):
        """Checks whether the item matches specifications."""
        if not item['league'] == self.league:
            return None
            
        if not self.corrupted and item['corrupted'] == 'True':
            return None
            
        if len(item['sockets']) < self.sockets:
            return None
        
        if not self.check_links(item['sockets']):
            return None
        
        full_name = localization.sub('', ' '.join(filter(None, [item['name'], item['typeLine']])))
        full_text = ' '.join([full_name] + (item['implicitMods'] if 'implicitMods' in item else []) + (item['explicitMods'] if 'explicitMods' in item else []))
        
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
    
    def parse_stashes(self):
        """Parses the stash data for items matching input specifications.
        Returns matching items to the main thread via queue.
        """
        for stash in self.stashes:
            for item in stash['items']:
                if self.dead:
                    return
                checked_item = self.check_item(item, stash['stash'])
                if checked_item:
                    self.spawner.queue_results.put({'name':stash['lastCharacterName'], 'item':checked_item[0],
                                                    'price':checked_item[1], 'league':item['league'],
                                                    'stash':stash['stash'], 'x':item['x'], 'y':item['y']})
        
    def check_links(self, item_sockets):
        """Checks whether the item has the desired number of links."""
        groups = [0] * 6
        for socket in item_sockets:
            groups[socket['group']] += 1
        for i in groups:
            if i >= self.links:
                return True
        return False
        
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