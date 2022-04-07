FROM python:slim

WORKDIR /

COPY . /

RUN pip3 install -r requirements.txt && apt-get update -y && apt-get install -y && python3 -r requirements_spacy.txt

ENTRYPOINT ["python3", "runner.py"]