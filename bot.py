from bs4 import BeautifulSoup as BS
import requests
from collections import Counter
import io
import re
import ssl
from urllib3 import poolmanager
import telebot
import spacy

# The backend process for inspection - requires only artists' name)
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
        i = i + 1

    def text_replace(target_str, replace_values, ):
        for el in replace_values:
            target_str = target_str.replace(el, ' ')
        return target_str
    code_elements = io.open('/root/sadzax/lyrics/txt/excludes/code_elements.txt',
                            mode="r", encoding='utf-8').read().lower().splitlines()
    commas_and_symbols = io.open('/root/sadzax/lyrics/txt/excludes/commas_and_symbols.txt',
                                 mode="r", encoding='utf-8').read().lower().splitlines()
    eng_commons = io.open('/root/sadzax/lyrics/txt/excludes/eng_commons.txt',
                          mode="r", encoding='utf-8').read().lower().splitlines()
    eng_commons_expanded = io.open('/root/sadzax/lyrics/txt/excludes/eng_commons_expanded.txt',
                                   mode="r", encoding='utf-8').read().lower().splitlines()
    stuff_values = io.open('/root/sadzax/lyrics/txt/excludes/stuff_values.txt',
                           mode="r", encoding='utf-8').read().lower().splitlines()
    replace_values = code_elements + commas_and_symbols + eng_commons + eng_commons_expanded + stuff_values

    eng_lyrics = ' '.join(eng_lyrics)
    eng_lyrics = text_replace(eng_lyrics, replace_values)
    eng_lyrics = text_replace(eng_lyrics, replace_values)
    words = eng_lyrics.split(' ')
    words = [value for value in words if value]
    nlp = spacy.load("en_core_web_sm")
    lemmatizer = nlp.get_pipe("lemmatizer")
    doc = nlp(' '.join(map(str, words)))
    words = [token.lemma_ for token in doc if token.pos_ == 'ADV' or token.pos_ == 'ADJ'
                  or token.pos_ == 'NOUN' or token.pos_ == 'VERB']

    words_counter_list = Counter(words).most_common()
    if len(words_counter_list)>150:
        words_counter_str = '\n'.join(map(str, words_counter_list[0:150]))
    else:
        words_counter_str = '\n'.join(map(str, words_counter_list))
    return words_counter_str

def lyrics_inspector_full_cycle_translate(artist):

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

    transaled_lyrics = []
    i = 0
    while i < len(text):
        if text[i].startswith('<div class="translate">') is True:
            transaled_lyrics.append(text[i])
        i = i + 1

    def text_replace(target_str, replace_values, ):
        for el in replace_values:
            target_str = target_str.replace(el, ' ')
        return target_str
    code_elements = io.open('/root/sadzax/lyrics/txt/excludes/code_elements.txt',
                            mode="r", encoding='utf-8').read().lower().splitlines()
    commas_and_symbols = io.open('/root/sadzax/lyrics/txt/excludes/commas_and_symbols.txt',
                                 mode="r", encoding='utf-8').read().lower().splitlines()
    eng_commons = io.open('/root/sadzax/lyrics/txt/excludes/eng_commons.txt',
                          mode="r", encoding='utf-8').read().lower().splitlines()
    eng_commons_expanded = io.open('/root/sadzax/lyrics/txt/excludes/eng_commons_expanded.txt',
                                   mode="r", encoding='utf-8').read().lower().splitlines()
    stuff_values = io.open('/root/sadzax/lyrics/txt/excludes/stuff_values.txt',
                           mode="r", encoding='utf-8').read().lower().splitlines()
    replace_values = code_elements + commas_and_symbols + eng_commons + eng_commons_expanded + stuff_values

    translated_lyrics = ' '.join(map(str, translated_lyrics))
    translated_lyrics = text_replace(translated_lyrics, replace_values)
    translates = translated_lyrics.split(' ')
    translates = [value for value in translates if value]  # Remove empty values in list
    nlp = spacy.load("ru_core_news_sm")
    lemmatizer = nlp.get_pipe("lemmatizer")
    doc = nlp(' '.join(map(str, translates)))
    translates = [token.lemma_ for token in doc if token.pos_ == 'ADV' or token.pos_ == 'ADJ'
                  or token.pos_ == 'NOUN' or token.pos_ == 'VERB']

    translates_counter_list = Counter(translates).most_common()
    if len(translates_counter_list)>150:
        translates_counter_str = '\n'.join(map(str, translates_counter_list[0:150]))
    else:
        translates_counter_str = '\n'.join(map(str, translates_counter_list))
    return translates_counter_str

tokenTG = io.open('/root/sadzax/lyrics/token.txt', mode="r", encoding='utf-8').read()
bot = telebot.TeleBot(tokenTG)

@bot.message_handler(commands=['start', 'help'])
def start(message):
    bot_resopnse_on_start = f'<b>Hello, {message.from_user.first_name}</b>\n\n' \
                            f'You ca switch to Russian translations by sending me messages like' \
                            f' "Ru", "Translations" etc.\n' \
                            f'(Переключиться на переводы можно, ответив на это сообщение чем-то вроде' \
                            f' "переводы", "рус" и т.д.)\n\n' \
                            f'Send me the name of the Artist:'
    bot.send_message(message.chat.id, bot_resopnse_on_start, parse_mode='html')


@bot.message_handler()
def switcher_and_request(message):
    rus_switcher = ['ru', 'rus', 'russian', 'translation', 'translations', 'trans', 'tr', 'ру', 'рус', 'русский', 'руский', 'русское', 'россия', 'по-русски', 'по-ру', 'порусски', 'перевод', 'переводы']
    if message.text.lower() in rus_switcher:
        reply_to_rus_switcher = bot.reply_to(message, """\
Мы теперь переключились на переводы\n\n
Switch back to English by sending me /start commamd\n
Переключиться обратно на оригиналы можно через команду /start\n\n
Пришлите мне зарубежного артиста, чьи самые распространённые слова (в русском переводе) вы хотите увидеть:
""")
        bot.register_next_step_handler(reply_to_rus_switcher, get_russian_request_from_the_user)
        def get_russian_request_from_the_user(message_rus):
            artist_requested_by_user = message_rus.text
            bot.send_message(message_rus.chat.id, f"Вы выбрали {artist_requested_by_user} \n Пожалуйста, "
                                                      f"немного подожите, если имя введено корректно, то я"
                                                      f"постараюсь всё найти для вас. Обычно, на это уходит пара"
                                                      f"минут. Если долго не отвечаю, значит, я на починке")
            bot.send_message(message_rus.chat.id, f"Вот какие слова больше всего любит "
                                                      f"{artist_requested_by_user}: \n\n"
                                                      f"{lyrics_inspector_full_cycle_translate(artist_requested_by_user)}\n\n "
                                                      f"Я постарался убрать частицы, местоимения, союзы и всё такое "
                                                      f"подобное, но я ещё совсем юный робот, и я только учусь, "
                                                      f"поэтому буду рад замечаниям. Контакты есть в моём профиле")
    elif message.text == 'testme':
        bot.send_message(message.chat.id, f'<b>Your Technical Data:</b>\n\n{message}', parse_mode='html')
    elif message.text.lower() not in rus_switcher and message.text.lower() != 'testme':
        artist_requested_by_user = message.text
        bot.send_message(message.chat.id, f"So, it's {artist_requested_by_user}\nNice choice\nI'll try it"
                                          f"\nWait, please...")
        bot.send_message(message.chat.id, f"I search in all data aviable for me online, it usually takes from 30 "
                                          f"sec to a couple of minutes\nIf I don't response for a too long "
                                          f"that means I'm on repair today")
        bot.send_message(message.chat.id, f"So that's {artist_requested_by_user}'s favourite words:\n\n"
                                          f"{lyrics_inspector_full_cycle(artist_requested_by_user)}\n\n"
                                          f"Please consider I have tried to exclude articles, preverbs and "
                                          f"constructinal words like 'am', 'have', 'been', etc. If you find "
                                          f"some words like this, feel free to contact me (check 'about')")

bot.polling(none_stop=True)