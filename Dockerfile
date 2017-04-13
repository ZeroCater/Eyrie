FROM python:3.5.2
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
RUN adduser --disabled-password --gecos "" worker
WORKDIR /code

RUN apt-get update
RUN apt-get install libgeos-dev liblapack-dev libatlas-base-dev --yes

ADD requirements.dev.txt /code/
ADD requirements.txt /code/
RUN pip install --src=/pip-install -r requirements.dev.txt
ADD . /code/
