FROM python:slim

WORKDIR /

COPY . /

RUN pip3 install -r requirements.txt && apt-get update -y && apt-get install -y

CMD [ "python3", "-m" , "spacy", "download", "en_core_web_sm"]

ENTRYPOINT ["python", "runner.py"]