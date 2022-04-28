FROM nginxinc/nginx-unprivileged:1-alpine
LABEL maintainer="lomank200222@gmail.com"

COPY ./run.sh /run.sh

USER root

RUN touch /etc/nginx/conf.d/default.conf && \
    chown nginx:nginx /etc/nginx/conf.d && \
    chmod +x /run.sh

COPY ./default.conf /etc/nginx/conf.d/default.conf

USER nginx

CMD ["/run.sh"]
