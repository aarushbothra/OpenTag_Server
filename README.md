# OpenTag Server Setup Instructions

## Linux
First check if python is already installed
```
python3 -V
```
It should say
```
python 3.7.x
```
Anything higher than this is fine too. You can skip to the next part. If you have something lower than this, or no python at all here's how to get 3.7:

https://tecadmin.net/install-python-3-7-on-ubuntu-linuxmint/

Downloading Server

```
git clone https://github.com/APersonnn/OpenTag_Server.git
cd ~/OpenTag_Server
git fetch --tags
git checkout $(git describe --tags $(git rev-list --tags --max-count=1))
```

Running Server

```
cd ~/OpenTag_Server
python3 OpenTag_Server.py
```

Updating Server

```
cd ~/OpenTag_Server
git fetch --tags
git checkout $(git describe --tags $(git rev-list --tags --max-count=1))
```

## Windows

Get Python from here:

https://www.python.org/downloads/

After that, download the repo. Right click on OpenTag_Server.py, go to Open With, and click Python 3.8.

## Docker

Check out goldsziggy/OpenTag_Server for a docker version!

## Connecting from the app

Once you know the server runs, close it. You now need to portforward the server if you wish to access it from the internet. I'm not going to go over it because it is slightly different for every router model, but just know that if you didn't edit the port in OpenTag_Server.py, the port is 1234.

After that, we need the public IP of our server. On a device with a browser connected to the same network as the server, type "whats my ip" into google. This is the IP you will type into the app when not connected to the same network as the server! You should now be good to go. Have fun!
