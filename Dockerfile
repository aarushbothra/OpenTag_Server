FROM python:3.7-alpine3.12

WORKDIR /app

COPY OpenTag_Server.py ./

ENTRYPOINT [ "python", "OpenTag_Server.py" ]