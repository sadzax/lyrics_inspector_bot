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
replace_list_for_artists = (' ','_','.','_','&','and','(','',')','','+','and')
i = 1
while i < len(replace_list_for_artists):
    artist = artist.replace(replace_list_for_artists[i-1],replace_list_for_artists[i])
    i = i + 2

## 2. By now we have a decent artist name for a URL search at amalgama-lab project
## url_artist = "https://www.amalgama-lab.com/songs/" + artist[0] + '/' + artist
## print (url_artist)
## data = requests.get(url_artist, verify=False)

## 3.1 Open the file with some textes and code stuff, a batch from the website
text = io.open("txt/fulltext.txt", mode="r", encoding='utf-8').read().lower().splitlines()
## 3.2 Form only english lyrics from the song
eng_lyrics = []
i = 0
while i < len(text):
    if text[i].startswith('<div class="string_container">') is True: #include original
        eng_lyrics.append(text[i])
        if text[i+1].startswith('<div class="translate">') is True: #exculde translations
            i = i + 1
        else:
            eng_lyrics.append(text[i+1]) #include in original 2nd value (because some texts got splitted with their <div>s
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