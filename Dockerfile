FROM linuxserver/calibre:8.10.0

RUN useradd --user-group --system --create-home --no-log-init nightowl
RUN mkdir /home/nightowl/defaultLibrary
COPY volume/defaultLibrary /home/nightowl/defaultLibrary
RUN mkdir /config/Calibre Library
RUN chown nightowl: -R /config
RUN chown nightowl: -R /home/nightowl
USER nightowl
WORKDIR /home/nightowl

COPY books_server/requirements.txt .
RUN python -m venv venv
RUN ./venv/bin/pip install -r requirements.txt

COPY dist ./client
COPY books_server/ .

ENV S6_KEEP_ENV=1
CMD ["./venv/bin/python", "app.py"]
