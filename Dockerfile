FROM python:3.9-alpine3.13

LABEL maintainer="lomank200222@gmail.com"

ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /requirements.txt
COPY ./sharedmusic /sharedmusic
COPY ./scripts /scripts

WORKDIR /sharedmusic

RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    apk add --update --no-cache postgresql-client bash && \
    apk add --update --no-cache --virtual .tmp-deps \
        build-base postgresql-dev linux-headers \
        python3-dev freetype-dev libffi-dev && \
    /py/bin/pip install -r /requirements.txt && \
    apk del .tmp-deps && \
    adduser --disabled-password --no-create-home sharedmusic && \
    mkdir -p /vol/web/static && \
    mkdir -p /vol/web/media && \
    chown -R sharedmusic:sharedmusic /vol && \
    # Or you'll get permission denied error
    chown -R sharedmusic:sharedmusic /py/lib/python3.9/site-packages && \
    chmod -R +x /scripts

ENV PATH="/scripts:/py/bin:/py/lib:$PATH"

RUN python manage.py collectstatic --noinput

USER sharedmusic

CMD ["run.sh"]