FROM python:slim

WORKDIR /

COPY . /

ENTRYPOINT ["python", "test.py"]