FROM node:20.16.0 AS fe_builder
COPY package.json .
COPY package-lock.json .
RUN CI=true npm install
COPY . .
RUN CI=true npm run build

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

COPY books_server/ .
COPY --from=fe_builder dist ./client

ENV S6_KEEP_ENV=1
ENV FOXTALES_LIBRARY_PATH="/config/Calibre Library"
ENV FOXTALES_CLIENT_DIR="/home/nightowl/client"
CMD ["./venv/bin/python", "app.py"]
