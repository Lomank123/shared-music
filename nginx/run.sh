#!/bin/sh

set -e

sed -i -e 's/$PORT/'"$PORT"'/g' /etc/nginx/conf.d/default.conf
nginx -g 'daemon off;'