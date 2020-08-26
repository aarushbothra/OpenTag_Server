# OpenTag Server

Make sure to set the server address and port properly in python file before running. To start server, just run OpenTag_Server.py on any machine running Python 3.7+.

If you are running on anything other than Windows, you have to set the server address manually to the IPV4 of the computer the server is running on. Default port is 1234.

## Dockerfile instructions

### Pulling the image

```
docker pull matthewzygowicz/open-tag-server
```

### Running the image

because we expose a port don't forget to map it back!

```
docker run -p 1234:1234 -t matthewzygowicz/open-tag-server
```
