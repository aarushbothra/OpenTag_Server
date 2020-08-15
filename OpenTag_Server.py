import socket
import threading
import time
import os
import sys
#import psutil
import logging
import struct

import subprocess

HEADER = 64
PORT = 1234
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
VERSION = float(1.1)


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

adminNotSet = True

clients = []

gunIDs = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16]

connectionsAvailable = True

currentGame = None

adminSetUpComplete = False

gameInProgress = False

sendPlayerInfo = False

gameEnded = False

def listToString(list):
    returnString = ''

    for x in range(0,20):
        returnString += str(list[x])
        returnString += ","

    if len(returnString) < 80:
        for x in range(0,(80-len(returnString))-1):
            returnString += ","


    return returnString


def sendWithException(conn, byteList):
    try:
        conn.send(listToString(byteList).encode("utf-8"))
    except:
        print("unable to send")


def restart():
    global clients
    global gunIDs
    global adminNotSet
    global connectionsAvailable
    global currentGame
    global adminSetUpComplete
    global gameInProgress
    global sendPlayerInfo
    global server
    global gameEnded
    
   # sys.exit()

    print("restart")
    byteList = [0]*20
    byteList[0] = 254
    
    for client in clients:
        client.conn.close()

    connectionsAvailable = False
 

    server.close()
    print("server closed")
    clients = []
    gunIDs = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16]
    adminNotSet = True
    connectionsAvailable = True
    currentGame = None
    adminSetUpComplete = False
    gameInProgress = False
    sendPlayerInfo = False
    gameEnded = False

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)

    print("[STARTING] server is starting...")
    start()


class Player:
    global gunIDs

    usernameSet = False

    def __init__(self, conn, addr):
        self.conn = conn
        self.address = addr
        self.admin = False
        self.gunID = gunIDs[0]
        gunIDs.pop(0)

    def getGunID(self):
        return self.gunID

    def setAdmin(self, bool):
        self.admin = bool

    def setUsername(self, string):
        self.username = string

    def returnConn(self):
        return self.conn

    def returnAddress(self):
        return self.address

    def setPlayerSettings(self, usernameSet, username, team, gunType, kills, deaths):
        self.username = username
        self.team = team
        self.gunType = gunType
        self.usernameSet = usernameSet
        self.kills = kills
        self.deaths = deaths

    def getUsername(self):
        return self.username

    def getTeam(self):
        return self.team

    def getGunType(self):
        return self.gunType

    def addKill(self):
        self.kills += 1

    def addDeath(self):
        self.deaths += 1


#ammo, lives, time, maxKills, and numOfTeams will all be ints, with max 255. If any of these are 0, then they will be unlimited (for numOfTeams, it will be ffa).
#Both time and maxKills cannot be 0, will be managed by app.
#numOfTeams cannot be greater than 8, unless ffa. numOfTeams also cannot be 1
#Time will be in minutes
class Game:
    def __init__(self, numOfTeams, ammo, lives, time, maxKills, location):
        self.ammo = ammo
        self.lives = lives
        self.time = time
        self.maxKills = maxKills
        self.numOfTeams = numOfTeams
        self.location = location

    def getNumOfTeams(self):
        return self.numOfTeams

    def getAmmo(self):
        return self.ammo

    def getLives(self):
        return self.lives

    def getTime(self):
        return self.time

    def getMaxKills(self):
        return self.maxKills






def findPlayerByGunID(gunID):
    global clients

    x = 0
    returnVar = -1
    while x < len(clients):
        if(clients[x].gunID == gunID):
            returnVar = x
        x += 1
    return returnVar

def findPlayer(addr):
    global clients

    x = 0
    returnVar = -1
    while x < len(clients):
        if(clients[x].address == addr):
            returnVar = x
        x += 1
    return returnVar



def removePlayer(conn, addr):
    global clients
    global connectionsAvailable
    global currentGame
    global handeleServerRestartPath
    global adminSetUpComplete
    global sendPlayerInfo
    global gameInProgress

    print(f"REMOVING PLAYER {addr}")

    conn.close()

    playerIndex = findPlayer(addr)
    if clients[playerIndex].admin:
        connectionsAvailable = False
        print("admin removed")
        restart()
        
    
    else:
        if sendPlayerInfo:
            byteList = [0]*20
            byteList[0] = 4
            byteList[1] = clients[playerIndex].getGunID()
            gunIDs.append(clients[findPlayer(addr)].getGunID())
            clients.pop(playerIndex)
            for client in clients:
                sendWithException(client.returnConn(), byteList)

        
        else:
            print("regular player removed")
            gunIDs.append(clients[playerIndex].getGunID())
            clients.pop(playerIndex)




def parseMessage(conn, addr, msgRaw):

    global clients
    global connectionsAvailable
    global currentGame
    global handeleServerRestartPath
    global adminSetUpComplete
    global sendPlayerInfo
    global gameInProgress
    global gameEnded

    msg = bytearray(msgRaw)
    
    if msg[0] != 252:
        print(f"Message Receied: {msg}")

    if msg[0] == 0:

        currentGame = Game(msg[1], msg[2], msg[3], msg[4], msg[5], msg[6])
        adminSetUpComplete = True
        byteList = [0]*20
        byteList[0] = 2
        byteList[1] = currentGame.getNumOfTeams()
        byteList[2] = currentGame.getAmmo()
        byteList[3] = currentGame.getLives()
        byteList[4] = currentGame.getTime()
        byteList[5] = currentGame.getMaxKills()
        byteList[6] = currentGame.location

        print(f"sending game setup: {byteList}")
        for client in clients:
            client.returnConn().send(listToString(byteList).encode("utf-8"))

    elif msg[0] == 1:
        usernameArray = bytearray([])
        byteList = [0]*20
        for x in range(1,10):
            usernameArray.append(msg[x])
            byteList[x] = msg[x]
        username = usernameArray
        clients[findPlayer(addr)].setPlayerSettings(True, username, msg[11], msg[12], 0, 0)
        sendPlayerInfo = True

        byteList[0] = 3
        byteList[11] = msg[11]
        byteList[12] = msg[12]
        byteList[13] = clients[findPlayer(addr)].getGunID()

        for client in clients:
            client.returnConn().send(listToString(byteList).encode("utf-8"))

        if gameInProgress == True:
            byteList = [0]*20
            byteList[0] = 5
            conn.send(listToString(byteList).encode("utf-8"))

    elif msg[0] == 2:
        gameInProgress = True
        byteList = [0]*20
        byteList[0] = 5
        for client in clients:
            client.returnConn().send(listToString(byteList).encode("utf-8"))

    elif msg[0] == 3:
        byteList = [0]*20
        byteList[0] = 6
        byteList[1] = msg[1]
        byteList[2] = msg[2]
        for client in clients:
            client.returnConn().send(listToString(byteList).encode("utf-8"))

    elif msg[0] == 4:
        clients[findPlayerByGunID(msg[1])].addKill()
        clients[findPlayerByGunID(msg[2])].addDeath()
        byteList = [0]*20
        byteList[0] = 7
        byteList[1] = msg[1]
        byteList[2] = msg[2]
        for client in clients:
            client.returnConn().send(listToString(byteList).encode("utf-8"))

    elif msg[0] == 5:
        gameEnded = True
        print("game ended")
        byteList = [0]*20
        byteList[0] = 8
        for client in clients:
            client.returnConn().send(listToString(byteList).encode("utf-8"))
        restart()

    elif msg[0] == 253:
        if msg[1] == 0:
            removePlayer(conn, addr)
        else:
            sendStartingMessages(conn, addr)
            print("sending starting messages")

    elif msg[0] == 254:
        restart()

    elif msg[0] == 255:
        removePlayer(conn, addr)
        print(f"{addr} CONNECTION CLOSED")








def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")

    global clients
    global connectionsAvailable
    global adminNotSet
    global gunIDs
    global server
    



    connected = True

    while connected:
        byteList = [0]*20
        try:
            msgRaw = conn.recv(20)
        except:
            connected = False
            try:
                conn.close()
                removePlayer(conn, addr)
            except:
                print(f"unable to remove forcibly disconnected player@ try recv {addr}")
            print(f"client forcibly disconnected @ try recv {addr}")

            if len(gunIDs) > 0:
                connectionsAvailable = True
         
        if msgRaw:
            parseMessage(conn, addr, msgRaw)

        else:
            connected = False
            try:
                conn.close()
                removePlayer(conn, addr)
            except:
                print(f"unable to remove forcibly disconnected player@ if msgRaw {addr}")
            print(f"client forcibly disconnected @ if msgRaw {addr}")
            
            



def sendStartingMessages(conn, addr):
    print("sending starting messages")
    global clients
    global connectionsAvailable
    global currentGame
    global handeleServerRestartPath
    global adminSetUpComplete
    global adminNotSet
    global sendPlayerInfo
    global gameInProgress
    global VERSION

    if len(gunIDs) == 0:
       connectionsAvailable = False

    byteList = [0]*20
    byteList[0] = 1

    if adminNotSet:
       clients[findPlayer(addr)].setAdmin(True)

       byteList[0] = 0
       adminNotSet = False

    byteList[1] = clients[findPlayer(addr)].getGunID()
    print(f"Sending {listToString(byteList)} to {clients[findPlayer(addr)].returnAddress()} ")
    conn.send(listToString(byteList).encode("utf-8"))

    if adminSetUpComplete:
        byteList = [0]*20
        byteList[0] = 2
        byteList[1] = currentGame.getNumOfTeams()
        byteList[2] = currentGame.getAmmo()
        byteList[3] = currentGame.getLives()
        byteList[4] = currentGame.getTime()
        byteList[5] = currentGame.getMaxKills()

        conn.send(listToString(byteList).encode("utf-8"))
    
    if sendPlayerInfo:
        for client in clients:
              if client.usernameSet:
                   byteList = [0]*20
                   byteList[0] = 3

                   for x in range(1,10):
                       byteList[x] = client.getUsername()[x-1]

                   byteList[11] = client.getTeam()
                   byteList[12] = client.getGunType()
                   byteList[13] = client.getGunID()
                   byteList[14] = client.deaths
                   byteList[15] = client.kills

                   conn.send(listToString(byteList).encode("utf-8"))


def start():
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")

    global clients
    global connectionsAvailable
    global currentGame
    global handeleServerRestartPath
    global adminSetUpComplete
    global adminNotSet
    global sendPlayerInfo
    global gameInProgress
    global VERSION

    while connectionsAvailable and not gameInProgress:
        continueExec = False
        try:
            conn, addr = server.accept()
            continueExec = True
        except:
           # print("connection tried on something that isnt a socket @ start()")
            continueExec = False

        if continueExec:

            clients.append(Player(conn, addr))

            #Version check
            byteList = [0]*20
            byteList[0] = 253

            #version 1.0
            byteList[1] = 1 #1
            byteList[2] = 1 #.1

            conn.send(listToString(byteList).encode("utf-8"))


            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
            print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 5}")



print("[STARTING] server is starting...")
start()
