import unittest

import requests

from bot import fit_message, is_russian_switch, start_text, utf16_len
from lyrics import (
    ArtistNotFound,
    LyricsError,
    artist_page_url,
    artist_slug,
    favourite_words,
    load_stopwords,
    load_word_file,
    more_songs_body,
    parse_more_filenames,
    parse_song_filenames,
    song_lines,
    song_url,
    tokens,
    top_words,
)


ARTIST_PAGE = """
<ul>
  <li class="active">Radiohead:<div class="list_songs"></div></li>
  <ul>
    <li><a href="creep.html">Creep</a></li>
    <li><a href="karma_police.html">Karma Police</a></li>
    <li><a href="creep.html">Creep again</a></li>
  </ul>
</ul>
<li><a href="/songs/m/michael_jackson/billie_jean.html">Billie Jean</a></li>
<script>
$.ajax({ url: "/ajax/more_songs.php", data: "folder_path=/songs/r/radiohead&name_song=index&imax=250" });
$.ajax({ data: "folder_path=/songs/r/rammstein&name_song=index&imax=250" });
</script>
"""

MORE_PAGE = """
<ul class="more_songs">
  <li><a href="extra_song.html">Extra</a></li>
</ul>
"""

SONG_PAGE = """
<div class="string_container">
  <div class="original">The love <b>song</b></div>
  <div class="translate">Любовь, любовь!</div>
</div>
<div class="original">love again</div>
<div class="translate">снова любовь</div>
"""


class FakeToken:
    def __init__(self, text):
        self.lemma_ = text
        self.pos_ = "DET" if text == "the" else "NOUN"


class FakeDoc:
    def __init__(self, text):
        self._tokens = [FakeToken(word) for word in text.split()]

    def __iter__(self):
        return iter(self._tokens)


def fake_nlp(text):
    return FakeDoc(text)


class FakeResponse:
    def __init__(self, text, status=200):
        self.text = text
        self.status_code = status


class FakeSession:
    def __init__(self, pages):
        self.pages = pages
        self.posts = []
        self.gets = []

    def get(self, url, timeout=None):
        self.gets.append(url)
        if url not in self.pages:
            return FakeResponse("", 404)
        return self.pages[url]

    def post(self, url, data=None, headers=None, timeout=None):
        self.posts.append((url, data, headers))
        return self.pages[url]


class SlugAndWordsTest(unittest.TestCase):
    def test_slug_strips_article_and_replaces_symbols(self):
        self.assertEqual(artist_slug("The Beatles"), "beatles")
        self.assertEqual(artist_slug("a tribe called quest"), "tribe_called_quest")
        self.assertEqual(artist_slug("pink.floyd"), "pink_floyd")
        self.assertEqual(artist_slug("AC/DC"), "ac/dc")

    def test_empty_artist_is_rejected(self):
        for name in ("", "   ", "the ", "!!!", "a "):
            with self.assertRaises(ValueError):
                artist_slug(name)

    def test_stopwords_are_whole_words(self):
        stop = load_stopwords()
        self.assertIn("the", stop)
        self.assertIn("yeah", stop)
        self.assertIn("about", stop)
        self.assertIn("где", stop)
        self.assertNotIn("know", stop)
        self.assertIn("know", load_word_file("eng_commons_questionable.txt"))
        self.assertEqual(tokens("velvet is the love"), ["velvet", "is", "the", "love"])
        self.assertEqual(
            [word for word in tokens("velvet is the love") if word not in stop],
            ["velvet", "love"],
        )

    def test_tokens_keep_cyrillic_words(self):
        self.assertEqual(tokens("Любовь, любовь!"), ["любовь", "любовь"])

    def test_top_words_drop_function_words_and_count_lemmas(self):
        report = top_words(fake_nlp, "the love love velvet", {"the"})
        self.assertEqual(report, "love — 2\nvelvet — 1")


class PageParserTest(unittest.TestCase):
    def test_artist_page_ignores_other_artists(self):
        self.assertEqual(
            parse_song_filenames(ARTIST_PAGE),
            ["creep.html", "karma_police.html"],
        )

    def test_more_songs_body_matches_this_artist_only(self):
        self.assertEqual(
            more_songs_body(ARTIST_PAGE, "radiohead"),
            "folder_path=/songs/r/radiohead&name_song=index&imax=250",
        )
        self.assertIsNone(more_songs_body(ARTIST_PAGE, "beatles"))

    def test_more_songs_fragment(self):
        self.assertEqual(parse_more_filenames(MORE_PAGE), ["extra_song.html"])

    def test_song_lines_read_both_languages_without_tags(self):
        self.assertEqual(song_lines(SONG_PAGE, "en"), ["The love song", "love again"])
        self.assertEqual(song_lines(SONG_PAGE, "ru"), ["Любовь, любовь!", "снова любовь"])


class FetchTest(unittest.TestCase):
    def test_favourite_words_uses_one_session_and_song_urls(self):
        slug = "radiohead"
        pages = {
            artist_page_url(slug): FakeResponse(ARTIST_PAGE),
            "https://www.amalgama-lab.com/ajax/more_songs.php": FakeResponse(MORE_PAGE),
            song_url(slug, "creep.html"): FakeResponse(SONG_PAGE),
            song_url(slug, "karma_police.html"): FakeResponse(SONG_PAGE),
            song_url(slug, "extra_song.html"): FakeResponse("<div class='original'>love</div>"),
        }
        session = FakeSession(pages)
        report = favourite_words(session, fake_nlp, "Radiohead", {"the", "again"}, "en")
        self.assertEqual(report, "love — 5\nsong — 2")
        self.assertEqual(len(session.posts), 1)
        self.assertTrue(all(url.endswith(".html") and not url.endswith(".html/") for url in session.gets[1:]))

    def test_site_timeout_reaches_the_caller(self):
        class BoomSession(FakeSession):
            def get(self, url, timeout=None):
                raise requests.Timeout("slow")

        with self.assertRaises(requests.Timeout):
            favourite_words(BoomSession({}), fake_nlp, "Radiohead", set(), "en")

    def test_missing_artist_is_a_clear_error(self):
        session = FakeSession({})
        with self.assertRaises(ArtistNotFound):
            favourite_words(session, fake_nlp, "nobody", set(), "en")

    def test_songs_without_lyrics_raise(self):
        slug = "radiohead"
        pages = {
            artist_page_url(slug): FakeResponse("<li class='active'>x</li><ul><li><a href='creep.html'>c</a></li></ul>"),
            song_url(slug, "creep.html"): FakeResponse("<div class='original'></div>", 200),
        }
        with self.assertRaises(LyricsError):
            favourite_words(FakeSession(pages), fake_nlp, "Radiohead", set(), "en")


class TelegramTextTest(unittest.TestCase):
    def test_start_text_escapes_html_in_the_name(self):
        text = start_text("<b>")
        self.assertIn("Hello, &lt;b&gt;", text)
        self.assertNotIn("Hello, <b>", text)

    def test_message_is_cut_to_telegram_limit(self):
        fitted = fit_message("a" * 5000)
        self.assertLessEqual(utf16_len(fitted), 4096)
        self.assertTrue(fitted.endswith("\n…"))
        self.assertEqual(fit_message("ok"), "ok")

    def test_russian_switch_is_exact(self):
        self.assertTrue(is_russian_switch("Ru"))
        self.assertTrue(is_russian_switch("переводы"))
        self.assertFalse(is_russian_switch("Radiohead"))

    def test_requests_exception_type_is_available_for_handlers(self):
        self.assertTrue(issubclass(requests.Timeout, requests.RequestException))


if __name__ == "__main__":
    unittest.main()
