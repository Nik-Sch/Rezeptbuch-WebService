FROM python:3.8-alpine

WORKDIR /usr/src/app

RUN apk add --no-cache --virtual .build-deps gcc musl-dev zlib-dev jpeg-dev libsodium libsodium-dev

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "./start.sh" ]