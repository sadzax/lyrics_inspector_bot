from bs4 import BeautifulSoup as BS
import requests
from collections import Counter
import io
import re
import ssl
from urllib3 import poolmanager
import spacy

# 1.1. Ask user to type the name of the artist and force it to lowercase
artist = input('Select Artist: ').lower()

# 1.2. Check if there's some article in artists' name and ignore it
if artist[0:4] == 'the ':
    artist = artist[4:]
elif artist[0:2] == 'a ':
    artist = artist[2:]

# 1.3. Make a list of replacements for a further URL usage (what to replace / by what) and execute replacements
replace_list_for_artists = (' ', '_', '.', '_', '&', 'and', '(', '', ')', '', '+', 'and')
i = 1
while i < len(replace_list_for_artists):
    artist = artist.replace(replace_list_for_artists[i - 1], replace_list_for_artists[i])
    i = i + 2

# 2. By now we have a decent artist name for a URL search at amalgama-lab project
url_artist = 'https://www.amalgama-lab.com/songs/' + artist[0] + '/' + artist


# 2.1. !secure_warn! SSL @ https://stackoverflow.com/questions/61631955/python-requests-ssl-error-during-requests
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

# 2.2. By now we have a list of strings from HTML response from proj as `artist_response`. Aiming to get urls of songs
artist_songs_urls = []
i = 0
while i < len(artist_response):
    if artist_response[i].startswith('            <div class="list_songs"></div>') is True:
        break
    else:
        i = i + 1
j = 0
while j < len(artist_response):
    if artist_response[j].startswith(
            '\t\t\t<!-- ajax загрузка оставшихся переводов, если их количество превышает 250') is True:
        break
    else:
        j = j + 1
artist_songs_urls = [response_piece for response_piece in artist_response[i:j]]

# 2.3. By now we have some dirty list with URLS, so we're extracting URLs
print ('Wait, please...')
every_song_urls = []
for element in artist_songs_urls:
    soup = str(BS(element, 'html.parser').find_all('a', href=True))  # clear some stuff
    soup = soup.rpartition('<a href="')[2]  # trim left side
    soup = soup.partition('.html">')[0] + soup.partition('.html')[1]  # trim right side
    every_song_urls.append(soup)
every_song_urls = [url_tail for url_tail in every_song_urls if
                   re.search('html', url_tail)]  # delete nulls and non-rurl_tailevant

# 2.4. By now our `every_song_urls` URLs is full of copy-paste endings to urls with lyrics
text = []
for url_tail in every_song_urls:
    url_song = 'https://www.amalgama-lab.com/songs/' + artist[0] + '/' + artist + '/' + url_tail + '/'
    session = requests.session()
    session.mount('https://', TLSAdapter())
    song_response = session.get(url_song).text.lower().splitlines()
    text.extend(song_response)

# 3.1 Open the dirty text_dump_file

# 3.2 Form lyrics from the song
# 3.2.1. English:
eng_lyrics = []
i = 0
while i < len(text):
    if text[i].startswith('<div class="string_container">') is True:
        eng_lyrics.append(text[i])  # include original
    i = i + 1
# 3.2.2. Russian translation:
translated_lyrics = []
i = 0
while i < len(text):
    if text[i].startswith('<div class="translate">') is True:
        translated_lyrics.append(text[i])
    i = i + 1

# 4.1 Clearing the text from commas, articles etc., defining the lists of exclude words and symbols
# 4.1.1.1. /text_reunion is out of use/
def text_reunion(target_str, reunion_values, ):
    for el in reunion_values:
        target_str = target_str.replace(el, '')
    return target_str
# 4.1.1.2. /text_reunion is out of use/
eng_shorts = io.open('txt/excludes/eng_shorts.txt', mode="r", encoding='utf-8').read().lower().splitlines()
reunion_values = eng_shorts
# 4.1.2.1. text_replace is very useful !
def text_replace(target_str, replace_values, ):
    for el in replace_values:
        target_str = target_str.replace(el, ' ')
    return target_str
# 4.1.2.2. text_replace is very useful !
code_elements = io.open('txt/excludes/code_elements.txt', mode="r", encoding='utf-8').read().lower().splitlines()
commas_and_symbols = io.open('txt/excludes/commas_and_symbols.txt', mode="r",
                             encoding='utf-8').read().lower().splitlines()
eng_commons = io.open('txt/excludes/eng_commons.txt', mode="r", encoding='utf-8').read().lower().splitlines()
eng_commons_expanded = io.open('txt/excludes/eng_commons_expanded.txt', mode="r",
                               encoding='utf-8').read().lower().splitlines()
stuff_values = io.open('txt/excludes/stuff_values.txt', mode="r", encoding='utf-8').read().lower().splitlines()
replace_values = code_elements + commas_and_symbols + eng_commons + eng_commons_expanded + stuff_values

# 4.2. Finally...
eng_lyrics = ' '.join(eng_lyrics)
eng_lyrics = text_replace(eng_lyrics, replace_values)
eng_lyrics = text_replace(eng_lyrics, replace_values) # sometimes cleaning leads to a new replaceable values
# eng_lyrics = text_reunion(eng_lyrics, reunion_values) # Unused
words = eng_lyrics.split(' ')
words = [value for value in words if value] # Remove empty values in list
nlp = spacy.load("en_core_web_sm")
lemmatizer = nlp.get_pipe("lemmatizer")
doc = nlp(' '.join(map(str, words)))
words = [token.lemma_ for token in doc]

translated_lyrics = ' '.join(map(str, translated_lyrics))
translated_lyrics = text_replace(translated_lyrics, replace_values)
translates = translated_lyrics.split(' ')
translates = [value for value in translates if value]  # Remove empty values in list
nlp = spacy.load("ru_core_news_sm")
lemmatizer = nlp.get_pipe("lemmatizer")
doc = nlp(' '.join(map(str, translates)))
translates = [token.lemma_ for token in doc if token.pos_ == 'ADV' or  token.pos_ == 'ADJ'
              or token.pos_ == 'NOUN' or token.pos_ == 'VERB']

# Unused
def words_replace(target_str, words_replace_list, ):
    for el in words_replace_list:
        target_str = target_str.replace(el, ' ')
    return target_str

words_counter_list = Counter(words).most_common()
if len(words_counter_list) > 150:
    words_counter_str = '\n'.join(map(str, words_counter_list[0:150]))
else:
    words_counter_str = '\n'.join(map(str, words_counter_list))

translates_counter_list = Counter(translates).most_common()
if len(translates_counter_list) > 150:
    translates_counter_str = '\n'.join(map(str, translates_counter_list[0:150]))
else:
    translates_counter_str = '\n'.join(map(str, translates_counter_list))

for i in translates_counter_list:
    print(i)