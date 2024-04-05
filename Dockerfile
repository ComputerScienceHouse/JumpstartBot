FROM python:3.7-slim-buster
MAINTAINER Beckett Jenen <beckettjenen@gmail.com>

RUN mkdir /opt/jumpstart-slackbot

COPY requirements.txt /opt/jumpstart-slackbot

WORKDIR /opt/jumpstart-slackbot

RUN pip install -r requirements.txt

COPY . /opt/jumpstart-slackbot

RUN ln -sf /usr/share/zoneinfo/America/New_York /etc/localtime

CMD ["flask", "run", "-u", "-h", "0.0.0.0", "-p", "5000"]
