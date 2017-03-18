Name:                   PoE ScamBot
Author:                 Tony Lau
System Requirements:    Windows, Python 3.6
Dependencies:           requests

PoE ScamBot is tool for maintaining a live search of the Path of
Exile stash tab API. Unlike some other indexers, such as poe.trade or
poe.ninja, ScamBot does not track historical data and is only a
lightweight parser. Thus, an item may show up multiple times if a
player modified other items in the stash.

Usage:
1.  Run scambot.pyw
2.  Under the default settings, simply input the desired parameters
    then press "Start". The app will automatically start searching for
    items with the input parameters.
3.  Start playing Path of Exile.
4.  When the app finds a result, it will play a tone and copy a
    whisper message to your clipboard.
5.  Paste the message into chat and profit!

Fields:
League          - the league that the item should be found in
Maximum Price   - the maximum price that the item should have
Minimum Price   - the minimum price that the item should have
Sockets         - the number of sockets that the item should have
Links           - the number of links that the item should have
Rarity          - the rarity type that the item should have
Allow Corrupted - whether the item can be corrupted
Allow Crafted   - whether the item can be crafted
Search Regex    - the regular expression that should match the item's
                  text. (The item's text is made by concatenating the
                  item's name, implicit mods, and explicit mods.)