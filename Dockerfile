FROM python:3.7-buster AS builder

ENV PYTHONUNBUFFERED 1

ADD requirements.txt requirements.txt
RUN pip3 install --prefix=/install -Ur requirements.txt


FROM python:3.7-buster

ENV PYTHONUNBUFFERED 1
COPY --from=builder /install /install

COPY app app

ENV IOT_DIR /data
ENV PORT 8080

ENV PATH "/install/bin:${PATH}"
ENV PYTHONPATH "/install/lib/python3.7/site-packages"

EXPOSE $PORT
CMD gunicorn --bind 0.0.0.0:${PORT} --access-logfile=- app.main:server