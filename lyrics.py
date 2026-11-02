import html
import logging
import re
import ssl
from collections import Counter
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
# eng_commons_questionable.txt лежит рядом намеренно и в фильтр не входит:
# там содержательные слова (know, always, never), а не служебные.
STOP_FILES = (
    "eng_commons.txt",
    "eng_commons_expanded.txt",
    "rus_commons.txt",
    "stuff_values.txt",
)
TOKEN_RE = re.compile(r"[a-zа-яё']+", re.IGNORECASE)
LEMMA_RE = re.compile(r"[a-zа-яё]+")
CONTENT_POS = {"ADV", "ADJ", "NOUN", "VERB"}
TIMEOUT = (5, 20)
CHUNK_WORDS = 400
TOP_LIMIT = 30
SITE = "https://www.amalgama-lab.com"
_REPLACEMENTS = (
    (" ", "_"),
    (".", "_"),
    ("&", "and"),
    ("(", ""),
    (")", ""),
    ("+", "and"),
)

logger = logging.getLogger(__name__)


class ArtistNotFound(Exception):
    pass


class LyricsError(Exception):
    pass


class TLSAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False, **kwargs):
        context = ssl.create_default_context()
        context.set_ciphers("DEFAULT@SECLEVEL=1")
        kwargs["ssl_context"] = context
        return super().init_poolmanager(connections, maxsize, block, **kwargs)


def make_session() -> requests.Session:
    session = requests.Session()
    session.mount("https://", TLSAdapter())
    session.headers["User-Agent"] = (
        "Mozilla/5.0 (compatible; LyricsInspector/1.0; +https://t.me/Lyrics_Inspector_Bot)"
    )
    return session


def artist_slug(name: str) -> str:
    artist = " ".join(name.strip().lower().split())
    if artist.startswith("the "):
        artist = artist[4:].strip()
    elif artist == "the":
        artist = ""
    elif artist.startswith("a "):
        artist = artist[2:].strip()
    elif artist == "a":
        artist = ""
    for old, new in _REPLACEMENTS:
        artist = artist.replace(old, new)
    artist = artist.strip("_")
    if not artist or not artist[0].isalnum():
        raise ValueError("empty artist")
    return artist


def artist_page_url(slug: str) -> str:
    return f"{SITE}/songs/{slug[0]}/{slug}/"


def song_url(slug: str, filename: str) -> str:
    return f"{SITE}/songs/{slug[0]}/{slug}/{filename}"


def load_word_file(name: str) -> set[str]:
    text = html.unescape((ROOT / name).read_text(encoding="utf-8"))
    words = set()
    for line in text.splitlines():
        for match in TOKEN_RE.finditer(line):
            token = match.group(0).lower().strip("'")
            if token:
                words.add(token)
    return words


def load_stopwords() -> set[str]:
    words: set[str] = set()
    for name in STOP_FILES:
        words.update(load_word_file(name))
    return words


def tokens(text: str) -> list[str]:
    found = []
    for match in TOKEN_RE.finditer(text):
        token = match.group(0).lower().strip("'")
        if token:
            found.append(token)
    return found


def _filename(href: str) -> str | None:
    name = href.strip().split("?", 1)[0].split("/")[-1]
    if not name.endswith(".html") or name == "index.html":
        return None
    return name


def _filenames_from_list(node) -> list[str]:
    names = []
    if node is None:
        return names
    for anchor in node.find_all("a", href=True):
        name = _filename(anchor["href"])
        if name:
            names.append(name)
    return names


def parse_song_filenames(page_html: str) -> list[str]:
    soup = BeautifulSoup(page_html, "html.parser")
    active = soup.select_one("li.active")
    if active is None:
        return []
    return _dedupe(_filenames_from_list(active.find_next_sibling("ul")))


def parse_more_filenames(page_html: str) -> list[str]:
    soup = BeautifulSoup(page_html, "html.parser")
    return _dedupe(_filenames_from_list(soup.select_one("ul.more_songs")))


def more_songs_body(page_html: str, slug: str) -> str | None:
    expected = f"folder_path=/songs/{slug[0]}/{slug}&"
    for match in re.finditer(r'data:\s*"([^"]+)"', page_html):
        body = match.group(1)
        if body.startswith(expected):
            return body
    return None


def _dedupe(names: list[str]) -> list[str]:
    seen = set()
    unique = []
    for name in names:
        if name in seen:
            continue
        seen.add(name)
        unique.append(name)
    return unique


def fetch_song_filenames(session: requests.Session, slug: str) -> list[str]:
    page_url = artist_page_url(slug)
    response = session.get(page_url, timeout=TIMEOUT)
    if response.status_code == 404:
        raise ArtistNotFound(slug)
    if response.status_code >= 400:
        raise requests.HTTPError(f"artist page status {response.status_code}")

    names = parse_song_filenames(response.text)
    body = more_songs_body(response.text, slug)
    if body:
        try:
            extra = session.post(
                f"{SITE}/ajax/more_songs.php",
                data=body,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": page_url,
                },
                timeout=TIMEOUT,
            )
        except requests.RequestException:
            logger.warning("extra songs were not loaded for %s", slug)
        else:
            if extra.status_code < 400:
                names.extend(parse_more_filenames(extra.text))
            else:
                logger.warning("extra songs status %s for %s", extra.status_code, slug)

    unique = _dedupe(names)
    if not unique:
        raise ArtistNotFound(slug)
    return unique


def song_lines(page_html: str, kind: str) -> list[str]:
    css = "div.original" if kind == "en" else "div.translate"
    soup = BeautifulSoup(page_html, "html.parser")
    lines = []
    for node in soup.select(css):
        line = node.get_text(" ", strip=True)
        if line:
            lines.append(line)
    return lines


def collect_lyrics(session: requests.Session, slug: str, filenames: list[str], kind: str) -> str:
    lines = []
    for name in filenames:
        url = song_url(slug, name)
        try:
            response = session.get(url, timeout=TIMEOUT)
        except requests.RequestException:
            logger.warning("song skipped: %s", url)
            continue
        if response.status_code != 200:
            logger.warning("song skipped: %s status %s", url, response.status_code)
            continue
        lines.extend(song_lines(response.text, kind))
    if not lines:
        raise LyricsError("no lyrics")
    return "\n".join(lines)


def top_words(nlp, text: str, stopwords: set[str], limit: int = TOP_LIMIT) -> str:
    raw = [token for token in tokens(text) if token not in stopwords]
    lemmas = []
    for start in range(0, len(raw), CHUNK_WORDS):
        chunk = " ".join(raw[start:start + CHUNK_WORDS])
        if not chunk:
            continue
        for token in nlp(chunk):
            if token.pos_ not in CONTENT_POS:
                continue
            lemma = token.lemma_.lower().strip("'")
            if not lemma or lemma in stopwords or LEMMA_RE.fullmatch(lemma) is None:
                continue
            lemmas.append(lemma)
    if not lemmas:
        return ""
    rows = Counter(lemmas).most_common(limit)
    return "\n".join(f"{word} — {count}" for word, count in rows)


def favourite_words(session, nlp, artist: str, stopwords: set[str], kind: str) -> str:
    slug = artist_slug(artist)
    filenames = fetch_song_filenames(session, slug)
    logger.info("artist %s songs %s kind %s", slug, len(filenames), kind)
    text = collect_lyrics(session, slug, filenames, kind)
    report = top_words(nlp, text, stopwords)
    if not report:
        raise LyricsError("no content words")
    return report
