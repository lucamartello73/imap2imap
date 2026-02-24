FROM python:3.12-alpine

RUN apk add --no-cache tzdata

COPY requirements.txt /opt
RUN pip install --no-cache -r /opt/requirements.txt

COPY imap2imap.py /imap2imap/
COPY railway_start.py /imap2imap/

WORKDIR /imap2imap

ENV PYTHONPATH /imap2imap

USER nobody

CMD ["python", "-u", "railway_start.py"]
