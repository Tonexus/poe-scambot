import re
import threading

import requests

STASH_API = 'http://betaapi.pathofexile.com/api/public-stash-tabs?id='
LOCALIZATION = re.compile('<<.*>>')

class ParserThread(threading.Thread):
    """Thread that parses each chunk of stash API data"""

    def __init__(self, spawner, parse_id, params):
        """Initializes the thread with a reference to the creator thread and specified seearch parameters."""
        threading.Thread.__init__(self)
        self.dead = False
        self.spawner = spawner
        self.parse_id = parse_id
        self.params = params
        self.start()
        
    def run(self):
        """Main actions of thread.
        First reads the API into an dictionary before parsing that dictionary for the desired items.
        """
        self.get_stashes()
        self.parse_stashes()
    
    def kill(self):
        """Sets the flag to stop processing and terminate the thread."""
        self.dead = True
        
    def get_stashes(self):
        """Reads the JSON data from the stash API into a dictionary.
        Also returns the id of the next chunk of data to the main thread via queue.
        """
        stash_data = requests.get(STASH_API + self.parse_id).json()
        self.spawner.queue_parse_ids.put(stash_data['next_change_id'])
        self.stashes = stash_data['stashes']
    
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
    
    def check_item(self, item, stash):
        """Checks whether the item matches specifications."""
        if not item['league'] == self.params.league:
            return None
            
        if not self.params.corrupted and item['corrupted'] == 'True':
            return None
            
        if not self.params.crafted and 'craftedMods' in item:
            return None
            
        if not self.params.frame_type == item['frameType']:
            return None
            
        if len(item['sockets']) < self.params.sockets:
            return None
        
        if not self.check_links(item['sockets']):
            return None
        
        full_name = LOCALIZATION.sub('', ' '.join(filter(None, [item['name'], item['typeLine']])))
        full_text = ' '.join([full_name] + (item['implicitMods'] if 'implicitMods' in item else []) + (item['explicitMods'] if 'explicitMods' in item else []))
        
        if not self.params.regex.search(full_text):
            return None
            
        price_regex_match = self.params.price_regex.match(stash)
        try:
            price_regex_match = self.params.price_regex.match(item['note'])
        except KeyError:
            pass
            
        if not price_regex_match:
            return None
            
        if float(price_regex_match.group(2)) > self.params.maxprice or float(price_regex_match.group(2)) < self.params.minprice:
            return None
        
        return full_name, price_regex_match
        
    def check_links(self, item_sockets):
        """Checks whether the item has the desired number of links."""
        groups = [0] * 6
        for socket in item_sockets:
            groups[socket['group']] += 1
        for i in groups:
            if i >= self.params.links:
                return True
        return False