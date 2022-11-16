FROM python

RUN pip3 install -r requirements.txt && apt-get update -y && apt-get install -y && python -r requirements_spacy.txt

ENTRYPOINT ["python", "bot.py"]