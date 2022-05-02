FROM nginxinc/nginx-unprivileged:1-alpine
LABEL maintainer="lomank200222@gmail.com"

COPY ./run.sh /run.sh

USER root

RUN touch /etc/nginx/conf.d/default.conf && \
    chown nginx:nginx /etc/nginx/conf.d && \
    touch /etc/ssl/sharedmusic.crt && \
    touch /etc/ssl/sharedmusic.key && \
    chown nginx:nginx /etc/ssl && \
    chmod +x /run.sh

COPY ./default.conf /etc/nginx/conf.d/default.conf
# Copying SSL certificate
COPY ./sharedmusic.crt /etc/ssl/sharedmusic.crt
COPY ./sharedmusic.key /etc/ssl/sharedmusic.key

USER nginx

CMD ["/run.sh"]
