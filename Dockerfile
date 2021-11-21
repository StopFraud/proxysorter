FROM python:3

ADD proxysorter.py /

RUN pip install --upgrade pip && \
    pip install pika requests pyyaml

CMD [ "python", "./proxysorter.py"]
