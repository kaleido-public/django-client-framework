FROM alpine

RUN apk add --update \
    alpine-sdk \
    python3 py3-pip \
    nginx \
    nodejs npm \
    entr
COPY requirements.txt /requirements.txt
RUN pip3 install -r /requirements.txt
RUN npm install -g sass typedoc typescript
COPY nginx.conf /etc/nginx/nginx.conf
COPY entrypoint.bash /entrypoint.bash
WORKDIR /
RUN mkdir -p /run/nginx/
RUN nginx -t
