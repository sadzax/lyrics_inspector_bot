FROM python:3-slim

WORKDIR /

COPY . /

RUN pip3 install -r requirements.txt && apt-get update -y && apt-get install -y

ENTRYPOINT ["python3", "bot.py"]

EXPOSE 3000