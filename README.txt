# OpenTag Server

##First Time Setup

###Linux
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

###Downloading Server

'''
git clone https://github.com/APersonnn/OpenTag_Server.git
cd OpenTag_Server
git fetch --tags
git checkout $(git describe --tags $(git rev-list --tags --max-count=1))
'''

###Running Server

```
cd OpenTag_Server
python3 OpenTag_Server.py
```

###Updating Server

'''
cd OpenTag_Server
git fetch --tags
git checkout $(git describe --tags $(git rev-list --tags --max-count=1))
'''

##Docker

Check out goldsziggy/OpenTag_Server for a docker version!
