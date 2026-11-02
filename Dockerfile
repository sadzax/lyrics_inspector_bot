FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && python -m spacy download en_core_web_sm \
    && python -m spacy download ru_core_news_sm

COPY bot.py lyrics.py ./
COPY eng_commons.txt eng_commons_expanded.txt eng_commons_questionable.txt rus_commons.txt stuff_values.txt ./

CMD ["python", "bot.py"]
