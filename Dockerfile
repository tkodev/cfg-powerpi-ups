FROM bitnami/python:3.10-debian-10

RUN apt-get install python3-smbus

RUN mkdir /app
ADD ./src /app
WORKDIR /app

CMD [ "python", "./app/ups.py" ]