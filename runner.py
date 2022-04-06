from bs4 import BeautifulSoup
import requests
from collections import Counter
import io
import re
import pandas
import ssl
from urllib3 import poolmanager

## 1. Ask user to type the name of the artist and force it to lowercase
artist = input('Select Artist: ').lower()
## 1.1. Check if there's some article in artists' name and ignore it
if artist[0:4] == 'the ':
    artist = artist[4:]
elif artist[0:2] == 'a ':
    artist = artist[2:]
## 1.2. Make a list of replacements for a further URL usage (what to replace / by what) and execute replacements
replace_list_for_artists = (' ','_','.','_','&','and','(','',')','','+','and','''''','_')
i = 1
while i < len(replace_list_for_artists):
    artist = artist.replace(replace_list_for_artists[i-1],replace_list_for_artists[i])
    i = i + 2

## 2. By now we have a decent artist name for a URL search at amalgama-lab project
url_artist = 'https://www.amalgama-lab.com/songs/' + artist[0] + '/' + artist

## 2.1. !Secuirty_warning! Found SSL Error decision @ https://stackoverflow.com/questions/61631955/python-requests-ssl-error-during-requests
class TLSAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        """ Create and initialize the urllib3 PoolManager. """
        ctx = ssl.create_default_context()
        ctx.set_ciphers('DEFAULT@SECLEVEL=1')
        self.poolmanager = poolmanager.PoolManager(
                num_pools=connections,
                maxsize=maxsize,
                block=block,
                ssl_version=ssl.PROTOCOL_TLS,
                ssl_context=ctx)
session = requests.session()
session.mount('https://', TLSAdapter())
artist_response = session.get(url_artist).text.lower().splitlines()
## 2.2. By now we have a list of strings from HTML response from project as `artist_response`. We are aiming to get urls of songs
artist_songs_urls = []
i = 0
while i < len(artist_response):
    if artist_response[i].startswith('            <div class="list_songs"></div>') is True:
        break
    else:
        i = i+1
j = 0
while j < len(artist_response):
    if artist_response[j].startswith('\t\t\t<!-- ajax загрузка оставшихся переводов, если их количество превышает 250') is True:
        break
    else:
        j = j+1
artist_songs_urls = [response_piece for response_piece in artist_response[i:j]]

# 2.3. By now we have some dirty list with URLS, so we're extracting URLs
every_song_urls = []
for element in artist_songs_urls:
    soup = str(bs(element, 'html.parser').find_all('a', href=True)) # clear some stuff
    soup = soup.rpartition('<a href="')[2] # trim left side
    soup = soup.partition('.html">')[0]+soup.partition('.html')[1] # trim right side
    every_song_urls.append(soup)
every_song_urls = [element for element in every_song_urls if re.search('html', element)] #delete nulls and non-relevants
## 2.4. By now our `every_song_urls` URLs is full of copy-paste endings to urls with lyrics

## 3.1 Open the file with some textes and code stuff, a batch from the website
text = io.open("txt/fulltext.txt", mode="r", encoding='utf-8').read().lower().splitlines()
## 3.2 Form only english lyrics from the song
eng_lyrics = []
i = 0
while i < len(text):
    if text[i].startswith('<div class="string_container">') is True:
        eng_lyrics.append(text[i]) # include original
        if text[i+1].startswith('<div class="translate">') is True: # but exculde translations
            i = i + 1
        else:
            eng_lyrics.append(text[i+1]) # and include in original 2nd value (because some texts got splitted with their <div>s
    i = i + 1

## 4. Clearing the text from commas, articles etc.
## 4.1. Defining the lists of exclude words and symbols
def text_replace(target_str, replace_values):
    for element in replace_values:
        target_str = target_str.replace(element,' ')
    return target_str
stuff_values = io.open("txt/excludes/stuff_values.txt", mode="r", encoding='utf-8').read().lower().splitlines()
commas_and_symbols = io.open("txt/excludes/commas_and_symbols.txt", mode="r", encoding='utf-8').read().lower().splitlines()
code_elements = io.open("txt/excludes/code_elements.txt", mode="r", encoding='utf-8').read().lower().splitlines()
eng_shorts = io.open("txt/excludes/eng_shorts.txt", mode="r", encoding='utf-8').read().lower().splitlines()
eng_commons = io.open("txt/excludes/eng_commons.txt", mode="r", encoding='utf-8').read().lower().splitlines()
replace_values = commas_and_symbols + code_elements + stuff_values + eng_shorts + eng_commons

## 4.2. Finally...
eng_lyrics = ' '.join(eng_lyrics)
eng_lyrics = text_replace(eng_lyrics, replace_values)
words = eng_lyrics.split(' ')
c = Counter(words).most_common()
for i in c:
    print(i)