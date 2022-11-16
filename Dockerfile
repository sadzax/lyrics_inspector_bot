FROM python:slim

RUN pip3 install -r requirements.txt && apt-get update -y && apt-get install -y &&

ENTRYPOINT ["python", "runner.py"]