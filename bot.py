from bs4 import BeautifulSoup as BS
import requests
from collections import Counter
import io
import re
import ssl
from urllib3 import poolmanager
import telebot

def lyrics_inspector_full_cycle(artist):
    artist = artist.lower()
    if artist[0:4] == 'the ':
        artist = artist[4:]
    elif artist[0:2] == 'a ':
        artist = artist[2:]
    replace_list_for_artists = (' ', '_', '.', '_', '&', 'and', '(', '', ')', '', '+', 'and')
    i = 1
    while i < len(replace_list_for_artists):
        artist = artist.replace(replace_list_for_artists[i - 1], replace_list_for_artists[i])
        i = i + 2
    url_artist = 'https://www.amalgama-lab.com/songs/' + artist[0] + '/' + artist
    class TLSAdapter(requests.adapters.HTTPAdapter):
        def init_poolmanager(self, connections, maxsize, block=False):
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
    every_song_urls = []
    for element in artist_songs_urls:
        soup = str(BS(element, 'html.parser').find_all('a', href=True))
        soup = soup.rpartition('<a href="')[2]
        soup = soup.partition('.html">')[0] + soup.partition('.html')[1]
        every_song_urls.append(soup)
    every_song_urls = [url_tail for url_tail in every_song_urls if
                   re.search('html', url_tail)]
    text = []
    for url_tail in every_song_urls:
        url_song = 'https://www.amalgama-lab.com/songs/' + artist[0] + '/' + artist + '/' + url_tail + '/'
        session = requests.session()
        session.mount('https://', TLSAdapter())
        song_response = session.get(url_song).text.lower().splitlines()
        text.extend(song_response)
    eng_lyrics = []
    i = 0
    while i < len(text):
        if text[i].startswith('<div class="string_container">') is True:
            eng_lyrics.append(text[i])
            if text[i + 1].startswith('<div class="translate">') is True:
                i = i + 1
            else:
                eng_lyrics.append(
                    text[i + 1])
        i = i + 1
    def text_reunion(target_str, reunion_values, ):
        for el in reunion_values:
            target_str = target_str.replace(el, '')
        return target_str
    def text_replace(target_str, replace_values, ):
        for el in replace_values:
            target_str = target_str.replace(el, ' ')
        return target_str
    eng_shorts = io.open('/txt/excludes/eng_shorts.txt', mode="r", encoding='utf-8').read().lower().splitlines()
    reunion_values = eng_shorts
    commas_and_symbols = io.open('/txt/excludes/commas_and_symbols.txt', mode="r", encoding='utf-8').read().lower().splitlines()
    code_elements = io.open('/txt/excludes/code_elements.txt', mode="r", encoding='utf-8').read().lower().splitlines()
    stuff_values = io.open('/txt/excludes/stuff_values.txt', mode="r", encoding='utf-8').read().lower().splitlines()
    eng_commons = io.open('/txt/excludes/eng_commons.txt', mode="r", encoding='utf-8').read().lower().splitlines()
    eng_commons_expanded = io.open('/txt/excludes/eng_commons_expanded.txt', mode="r", encoding='utf-8').read().lower().splitlines()
    replace_values = code_elements + commas_and_symbols + eng_commons + eng_commons_expanded + stuff_values
    eng_lyrics = ' '.join(eng_lyrics)
    eng_lyrics = text_replace(eng_lyrics, replace_values)
    eng_lyrics = text_replace(eng_lyrics, replace_values)
    words = eng_lyrics.split(' ')
    words = [value for value in words if value]
    words_counter_list = Counter(words).most_common()
    if len(words_counter_list)>150:
        words_counter_str = '\n'.join(map(str, words_counter_list[0:150]))
    else:
        words_counter_str = '\n'.join(map(str, words_counter_list))
    return words_counter_str

token = io.open('/txt/token.txt', mode="r", encoding='utf-8').read()
bot = telebot.TeleBot(token)

@bot.message_handler(commands=['start'])
def start(inbox_message):
    bot_resopnse_on_start = f'<b>Hello, {inbox_message.from_user.first_name} </b> \nSend me the name of the Artist:'
    bot.send_message(inbox_message.chat.id, bot_resopnse_on_start, parse_mode='html')

@bot.message_handler()
def get_request_from_the_user(inbox_message):
    if inbox_message.text == 'testme':
        bot.send_message(inbox_message.chat.id, f'<b>Your Technical Data:</b>\n\n{inbox_message}', parse_mode='html')
    else:
        artist_requested_by_user = inbox_message.text
        bot.send_message(inbox_message.chat.id, f"So, it's {artist_requested_by_user}\nNice choice\nI'll try it"
                                                f"\nWait, please...")
        bot.send_message(inbox_message.chat.id, f"I search in all data aviable for me online, it usually takes from 30 "
                                                f"sec to a couple of minutes\nBut if I don't response that means I'm on"
                                                f" repair today")
        bot.send_message(inbox_message.chat.id, f"So that's {artist_requested_by_user}'s favourite words:\n\n"
                                                f"{lyrics_inspector_full_cycle(artist_requested_by_user)}\n\n"
                                                f"Please consider that I have tried to exclude articles, preverbs and "
                                                f"constructinal words like 'am', 'have', 'been', etc. If you find"
                                                f"some word like this, feel free to contact me (in 'about')")

bot.polling(none_stop=True)