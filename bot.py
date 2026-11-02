import html
import logging
from pathlib import Path

import spacy
import telebot

from lyrics import (
    ArtistNotFound,
    LyricsError,
    ROOT,
    artist_slug,
    favourite_words,
    load_stopwords,
    make_session,
)

TELEGRAM_LIMIT = 4096
RUS_SWITCH = {
    "ru", "rus", "russian", "translation", "translations", "trans", "tr",
    "ру", "рус", "русский", "руский", "русское", "россия",
    "по-русски", "по-ру", "порусски", "перевод", "переводы",
}
NON_TEXT = [
    "audio", "document", "photo", "sticker", "video", "video_note",
    "voice", "location", "contact", "animation",
]

logger = logging.getLogger("lyrics_inspector")


def utf16_len(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2


def fit_message(text: str, limit: int = TELEGRAM_LIMIT) -> str:
    if utf16_len(text) <= limit:
        return text
    suffix = "\n…"
    budget = limit - utf16_len(suffix)
    size = 0
    kept = []
    for char in text:
        char_len = utf16_len(char)
        if size + char_len > budget:
            break
        kept.append(char)
        size += char_len
    return "".join(kept) + suffix


def start_text(first_name: str) -> str:
    name = html.escape(first_name or "friend", quote=False)
    return (
        f"<b>Hello, {name}</b>\n\n"
        "You can switch to Russian translations by sending "
        "\"Ru\" or \"Translations\".\n"
        "(Переключиться на переводы можно сообщением "
        "\"переводы\" или \"рус\".)\n\n"
        "Send me the name of the artist:"
    )


def is_russian_switch(text: str) -> bool:
    return text.strip().lower() in RUS_SWITCH


def read_token() -> str:
    path = Path(ROOT) / "token.txt"
    if not path.is_file():
        raise SystemExit(f"missing {path}")
    token = path.read_text(encoding="utf-8").strip()
    if not token:
        raise SystemExit(f"empty {path}")
    return token


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    token = read_token()
    logger.info("loading spaCy models")
    nlp_en = spacy.load("en_core_web_sm")
    nlp_ru = spacy.load("ru_core_news_sm")
    stopwords = load_stopwords()
    bot = telebot.TeleBot(token)
    if not bot.delete_webhook():
        raise SystemExit("Telegram webhook was not removed; polling would stay silent")

    def reply_failure(message, exc: Exception) -> None:
        if isinstance(exc, ArtistNotFound):
            bot.reply_to(
                message,
                "Не нашёл такого исполнителя. Напишите имя латиницей, как на amalgama-lab.",
            )
            return
        if isinstance(exc, ValueError):
            bot.reply_to(message, "Нужно имя исполнителя, не пустая строка и не одни знаки.")
            return
        if isinstance(exc, LyricsError):
            bot.reply_to(message, "Страница нашлась, но собрать слова из текстов не получилось.")
            return
        logger.exception("inspect failed")
        bot.reply_to(message, "Сайт с текстами сейчас не отвечает. Попробуйте ещё раз позже.")

    def answer(message, kind: str) -> None:
        text = (message.text or "").strip()
        if not text:
            bot.reply_to(message, "Пришлите имя исполнителя обычным текстом.")
            return
        try:
            artist_slug_preview = artist_slug(text)
        except ValueError:
            bot.reply_to(message, "Нужно имя исполнителя, не пустая строка и не одни знаки.")
            return
        if kind == "ru":
            bot.reply_to(
                message,
                f"Вы выбрали {text}.\nИщу переводы, это обычно занимает пару минут.",
            )
        else:
            bot.reply_to(
                message,
                f"So, it's {text}.\nI look through the lyrics I can reach. This usually takes a couple of minutes.",
            )
        nlp = nlp_ru if kind == "ru" else nlp_en
        session = make_session()
        try:
            report = favourite_words(session, nlp, text, stopwords, kind)
        except Exception as exc:
            reply_failure(message, exc)
            return
        finally:
            session.close()
        if kind == "ru":
            body = f"Слова, которые чаще всего встречаются у {text}:\n\n{report}"
        else:
            body = f"Most common words for {text}:\n\n{report}"
        bot.reply_to(message, fit_message(body))
        logger.info("answered %s kind %s", artist_slug_preview, kind)

    @bot.message_handler(commands=["start", "help"])
    def start(message):
        first_name = ""
        if message.from_user is not None:
            first_name = message.from_user.first_name or ""
        bot.send_message(message.chat.id, start_text(first_name), parse_mode="HTML")

    @bot.message_handler(content_types=NON_TEXT)
    def non_text(message):
        bot.reply_to(message, "Пришлите имя исполнителя обычным текстом.")

    @bot.message_handler(content_types=["text"])
    def on_text(message):
        text = message.text or ""
        if is_russian_switch(text):
            prompt = bot.reply_to(
                message,
                "Мы переключились на переводы.\n"
                "Пришлите зарубежного исполнителя: пришлю самые частые слова русского перевода.",
            )
            bot.register_next_step_handler(prompt, lambda next_message: answer(next_message, "ru"))
            return
        answer(message, "en")

    logger.info("polling")
    bot.infinity_polling(timeout=20, long_polling_timeout=20)


if __name__ == "__main__":
    main()
