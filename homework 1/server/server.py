#!/usr/bin/env python

import socket
import _thread
import sys
import ntpath
import time


TCP_IP = '127.0.0.1'
TCP_PORT = 5005
BUFFER_SIZE = 64000

FILE_PATH=""
FILE_NAME=""

UDP_IP = '127.0.0.1'
SESSIONS=dict()

LOST_PACKAGES=0

def printInfo(protocol, transmissionTime, numberOfMessagesRead, numberOfBytesRead, lostPackages):
    print("Protocol: ",protocol)
    print("Transmission Time: ",transmissionTime)
    print("Number of messages read: ",numberOfMessagesRead)
    print("Number of bytes read: ",numberOfBytesRead)
    print("Number of packages lost: ",lostPackages)

def initSessions():
    global SESSIONS
    for i in range(6006,7000):
        SESSIONS[i]=0
initSessions()

def getSessionPort():
    global SESSIONS
    keys=list(SESSIONS.keys())
    for key in keys:
        if SESSIONS[key]==0:
            SESSIONS[key]=1
        return key

def freeSession(port):
    global SESSIONS
    SESSIONS[port]=0
        


def handleClient(conn,addr):
    timestamp=time.time()
    messagesRead=0
    global LOST_PACKAGES
    print("Connection address:", addr)

    conn.settimeout(5)
    
    data = conn.recv(BUFFER_SIZE)
    if not data:
        conn.close()
        return
    conn.send(b"ACK")
    file=open(data,"wb")

    while 1:
        data = conn.recv(BUFFER_SIZE)
        if not data: break
        file.write(data)
        messagesRead+=1

    file.close()
    conn.close()
    print("closed connection with client")
    timestamp=time.time()-timestamp
    printInfo("TCP",timestamp, messagesRead+1, (messagesRead+1)*BUFFER_SIZE,LOST_PACKAGES)


def startTcpServer():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((TCP_IP, TCP_PORT))
    s.listen(1)
    print("Started TCP Server")
    print("Listening:")
    while True:
        (conn, addr) = s.accept()
        try:
            _thread.start_new_thread( handleClient, (conn, addr ) )
        except Exception as e:
            print ("Error: unable to start thread", e)

def sendMessageAndAwaitResponse(sock, message, addr, tries=0):
    global LOST_PACKAGES
    sock.settimeout(5)
    try:
        sock.sendto(message, addr)
        response=sock.recvfrom(BUFFER_SIZE)
        return response[0]
    except Exception as e:
        LOST_PACKAGES+=1
        if tries>=5:
            raise e
        sendMessageAndAwaitResponse(sock, message, addr, tries+1)

def handleUDPClient(address, port, myPort):
    global LOST_PACKAGES
    LOST_PACKAGES=0
    timestamp=time.time()
    messagesRead=1

    sock = socket.socket(socket.AF_INET, # Internet
                        socket.SOCK_DGRAM) # UDP
    sock.bind((UDP_IP, myPort))
    print("opened socket on port ", myPort)

    filename= sendMessageAndAwaitResponse(sock, bytes(str(myPort), 'utf-8'), (address, port))
    filename=filename.decode('utf-8')

    file=open(filename,"wb")

    while 1:

        data = sendMessageAndAwaitResponse(sock, bytes("ACK",'utf-8'), (address, port))
        if data == b"FIN": break
        file.write(data)
        messagesRead+=1
        
    sock.sendto(bytes("ACK",'utf-8'), (address, port))

    sock.close()
    freeSession(myPort)
    print("Closed connection with client",address, port)

    timestamp=time.time()-timestamp
    printInfo("UDP",timestamp, messagesRead, messagesRead*BUFFER_SIZE,0)


def startUdpServer():
    UDP_PORT = 6005

    sock = socket.socket(socket.AF_INET, # Internet
                        socket.SOCK_DGRAM) # UDP
    sock.bind((UDP_IP, UDP_PORT))
    print("Started UDP Server")
    print("Waiting for clients:")
    while True:
        (data, addr) = sock.recvfrom(1024) # buffer size is 1024 bytes
        print ("Client connected:", addr)
        try:
            _thread.start_new_thread( handleUDPClient, (addr[0], addr[1], getSessionPort()) )
        except Exception as e:
            print ("Error: unable to start thread", e)
        
_thread.start_new_thread( startTcpServer, ())

startUdpServer()