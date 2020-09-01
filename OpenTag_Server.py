#!/usr/bin/env python3
import socket
import threading
import time
import os
import sys
import json

import logging
import struct

import subprocess

HEADER = 64

# Changes to false after first player connected is assigned admin to prevent other players from becoming admin
adminNotSet = True

# list of all connected clients, stored as Player objects
clients = []

# gunIDs available to assign to clients. GunIDs get removed from this list when it is assigned to a player, and added back when players disconnect.
gunIDs = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]

# Stops the server from accepting clients if the server has run out of gunIDs to assign.
connectionsAvailable = True

# global variable that stores the settings of the current game by being instantiated as a Game object.
currentGame = None

# tracks whether admin has sent game settings back to the server
adminSetUpComplete = False

# tracks whether a game is currently running
gameInProgress = False

# tracks whether a game has ended.
gameEnded = False

listen = True

SERVER = ''
PORT = 1234
server = {}


def dispatchResponse(payload):
    if isinstance(payload, list):
        return listToString(payload).encode("utf-8")
    return json.dumps(payload).encode("utf-8")

# turns a list of ints into a string so it can be sent over the socket


def listToString(list):
    returnString = ''

    for x in range(0, 20):
        returnString += str(list[x])
        returnString += ","

    if len(returnString) < 80:
        for x in range(0, (80-len(returnString))-1):
            returnString += ","

    return returnString

# Restarts the server and disconnects all connected clients. Resets all globals.


def restart():
    global clients
    global gunIDs
    global adminNotSet
    global connectionsAvailable
    global currentGame
    global adminSetUpComplete
    global gameInProgress
    global server
    global gameEnded
    global listen

    listen = False

    print("restart")
    byteList = [0]*20
    byteList[0] = 254

    for client in clients:
        client.conn.close()

    connectionsAvailable = False

    clients = []
    gunIDs = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
    adminNotSet = True
    connectionsAvailable = True
    currentGame = None
    adminSetUpComplete = False
    gameInProgress = False
    gameEnded = False
    listen = True

    print("[STARTING] server is starting...")
    start(SERVER, PORT, server)


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

    def setPlayerSettings(self, usernameSet, username, team, gunType, kills, deaths, score):
        self.username = username
        self.team = team
        self.gunType = gunType
        self.usernameSet = usernameSet
        self.kills = kills
        self.deaths = deaths
        self.score = score

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

    def addScore(self):
        self.score += 1


# ammo, lives, time, maxKills, and numOfTeams will all be ints, with max 255. If any of these are 0, then they will be unlimited (for numOfTeams, it will be ffa).
# Both time and maxKills cannot be 0, will be managed by app.
# numOfTeams cannot be greater than 8, unless ffa. numOfTeams also cannot be 1
# Time will be in minutes
class Game:
    def __init__(self, numOfTeams, ammo, lives, time, maxKills, location, gameType):
        self.ammo = ammo
        self.lives = lives
        self.time = time
        self.maxKills = maxKills
        self.numOfTeams = numOfTeams
        self.location = location
        self.gameType = gameType

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


# returns index of player with matching gunID
def findPlayerByGunID(gunID):
    global clients

    x = 0
    returnVar = -1
    while x < len(clients):
        if(clients[x].gunID == gunID):
            returnVar = x
        x += 1
    return returnVar

# returns index of player with matching addr


def findPlayer(addr):
    global clients

    x = 0
    returnVar = -1
    while x < len(clients):
        if(clients[x].address == addr):
            returnVar = x
        x += 1
    return returnVar


# removes player from list clients and sends message to all other clients to remove player from their lists if client disconnects from server
def removePlayer(conn, addr):
    global clients
    global connectionsAvailable
    global currentGame
    global handeleServerRestartPath
    global adminSetUpComplete
    global gameInProgress

    print(f"REMOVING PLAYER {addr}")

    conn.close()

    playerIndex = findPlayer(addr)
    if clients[playerIndex].admin:
        connectionsAvailable = False
        print("admin removed")
        restart()

    else:
        if clients[findPlayer(addr)].usernameSet:
            byteList = [0]*20
            byteList[0] = 4
            byteList[1] = clients[playerIndex].getGunID()
            gunIDs.append(clients[findPlayer(addr)].getGunID())
            clients.pop(playerIndex)
            for client in clients:
                conn.send(listToString(byteList).encode("utf-8"))

        else:
            print("regular player removed")
            gunIDs.append(clients[playerIndex].getGunID())
            clients.pop(playerIndex)


# parses message recieved from client. For more info, see server communication protocol document.
def parseMessage(conn, addr, msgRaw):

    global clients
    global connectionsAvailable
    global currentGame
    global handeleServerRestartPath
    global adminSetUpComplete
    global gameInProgress
    global gameEnded

    msg = bytearray(msgRaw)

    if msg[0] != 252:
        print(f"Message Receied: {msg}")

    if msg[0] == 0:

        currentGame = Game(msg[1], msg[2], msg[3],
                           msg[4], msg[5], msg[6], msg[7])
        adminSetUpComplete = True
        byteList = [0]*20
        byteList[0] = 2
        byteList[1] = currentGame.getNumOfTeams()
        byteList[2] = currentGame.getAmmo()
        byteList[3] = currentGame.getLives()
        byteList[4] = currentGame.getTime()
        byteList[5] = currentGame.getMaxKills()
        byteList[6] = currentGame.location
        byteList[7] = currentGame.gameType

        print(f"sending game setup: {byteList}")
        for client in clients:
            client.returnConn().send(listToString(byteList).encode("utf-8"))

    elif msg[0] == 1:
        usernameArray = bytearray([])
        byteList = [0]*20
        for x in range(1, 10):
            usernameArray.append(msg[x])
            byteList[x] = msg[x]
        username = usernameArray
        clients[findPlayer(addr)].setPlayerSettings(
            True, username, msg[11], msg[12], 0, 0, 0)

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

    elif msg[0] == 6:
        byteList = [0]*20
        byteList[0] = 9
        byteList[1] = msg[1]
        byteList[2] = msg[2]
        for client in clients:
            if not client.admin:
                client.returnConn().send(listToString(byteList).encode("utf-8"))

    elif msg[0] == 7:
        byteList = [0]*20
        byteList[0] = 10
        byteList[1] = msg[1]
        for client in clients:
            client.returnConn().send(listToString(byteList).encode("utf-8"))

    elif msg[0] == 8:
        byteList = [0]*20
        byteList[0] = 11
        byteList[1] = msg[1]
        for client in clients:
            client.returnConn().send(listToString(byteList).encode("utf-8"))

    elif msg[0] == 9:
        clients[findPlayerByGunID(msg[1])].addScore()
        byteList = [0]*20
        byteList[0] = 12
        byteList[1] = msg[1]
        for client in clients:
            client.returnConn().send(listToString(byteList).encode("utf-8"))

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


# listens for messages from clients
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
                print(
                    f"unable to remove forcibly disconnected player@ try recv {addr}")
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
                print(
                    f"unable to remove forcibly disconnected player@ if msgRaw {addr}")
            print(f"client forcibly disconnected @ if msgRaw {addr}")


# when client connects for first time, server will send these messages to make sure client is up to date with the information all oter clients have about the game
def sendStartingMessages(conn, addr):
    print("sending starting messages")
    global clients
    global connectionsAvailable
    global currentGame
    global handeleServerRestartPath
    global adminSetUpComplete
    global adminNotSet
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
    print(
        f"Sending {listToString(byteList)} to {clients[findPlayer(addr)].returnAddress()} ")
    conn.send(listToString(byteList).encode("utf-8"))

    if adminSetUpComplete:
        byteList = [0]*20
        byteList[0] = 2
        byteList[1] = currentGame.getNumOfTeams()
        byteList[2] = currentGame.getAmmo()
        byteList[3] = currentGame.getLives()
        byteList[4] = currentGame.getTime()
        byteList[5] = currentGame.getMaxKills()
        byteList[6] = currentGame.location
        byteList[7] = currentGame.gameType

        conn.send(listToString(byteList).encode("utf-8"))

    for client in clients:
        if client.usernameSet:
            byteList = [0]*20
            byteList[0] = 3
            for x in range(1, 10):
                byteList[x] = client.getUsername()[x-1]

            byteList[11] = client.getTeam()
            byteList[12] = client.getGunType()
            byteList[13] = client.getGunID()
            byteList[14] = client.deaths
            byteList[15] = client.kills
            byteList[16] = client.score
            conn.send(listToString(byteList).encode("utf-8"))

# listens for connection attempts and starts connections from clients


def start(IP, PORT, localServer):

    print(f"[LISTENING] Server is listening on {IP}:{PORT}")
    server = localServer
    global clients
    global connectionsAvailable
    global currentGame
    global handeleServerRestartPath
    global adminSetUpComplete
    global adminNotSet
    global gameInProgress
    global VERSION
    global listen

    while listen:
        continueExec = False
        if connectionsAvailable:
            try:
                conn, addr = server.accept()
                continueExec = True
            except:
                continueExec = False

        if continueExec:

            clients.append(Player(conn, addr))

            # Version check
            byteList = [0]*20
            byteList[0] = 253

            # version 1.3
            byteList[1] = 1  # 1
            byteList[2] = 3  # .3

            conn.send(listToString(byteList).encode("utf-8"))

            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
            print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 5}")


if __name__ == '__main__':
    PORT = 1234
    # Change SERVER to the computer's IPV4. You don't need to change this if the server is running on windows
    SERVER = str(input("Enter the server's IPV4: "))
    ADDR = (SERVER, PORT)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)
    print("[STARTING] server is starting...")
    server.listen()
    start(SERVER, PORT, server)
