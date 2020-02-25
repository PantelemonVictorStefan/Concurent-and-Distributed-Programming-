
import socket
import sys
import ntpath
import time

TCP_IP = '127.0.0.1'
TCP_PORT = 5005
BUFFER_SIZE = 64000
FILE_PATH=""
FILE_NAME=""
UDP_IP = '127.0.0.1'
UDP_PORT = 6005
LOST_PACKAGES=0

def printInfo(transmissionTime, numberOfMessagesSent, numberOfBytesSent, lostPackages):
    print("Transmission Time: ",transmissionTime)
    print("Number of messages sent: ",numberOfMessagesSent)
    print("Number of bytes sent: ",numberOfBytesSent)
    print("Number of packages lost: ",lostPackages)

def handleConnection(conn):
    timestamp=time.time()
    messagesSent=0
    try:
        file=open(FILE_PATH,"rb")
    except Exception:
        print ("Error: unable to open file", FILE_PATH)
        conn.close()    
        return
    conn.settimeout(5)
    conn.send(bytes(FILE_NAME, 'utf-8'))
    conn.recv(BUFFER_SIZE)
    while 1:
        content=file.read(BUFFER_SIZE)
        if not content: break
        conn.send(content)
        messagesSent+=1
    file.close()
    conn.close()
    print("closed connection with server")
    timestamp=time.time()-timestamp
    printInfo(timestamp, messagesSent+1, (messagesSent+1)*BUFFER_SIZE,0)

def ConnectUsingTCP():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((TCP_IP, TCP_PORT))
    handleConnection(s)

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

def ConnectUsingUDP():
    timestamp=time.time()
    messagesSent=0
    try:
        file=open(FILE_PATH,"rb")
    except Exception:
        print ("Error: unable to open file", FILE_PATH)
        return
    myPort=7001
    sock = socket.socket(socket.AF_INET, # Internet
                        socket.SOCK_DGRAM) # UDP
    sock.sendto(bytes(str(myPort), 'utf-8'), (UDP_IP, UDP_PORT))
    newPort= sendMessageAndAwaitResponse(sock, bytes(str(myPort), 'utf-8'), (UDP_IP, UDP_PORT))
    newPort=int(newPort.decode('utf-8'))
    ack = sendMessageAndAwaitResponse(sock, bytes(FILE_NAME, 'utf-8'), (UDP_IP, newPort))
    while 1:
        content=file.read(BUFFER_SIZE)
        if not content: break
        ack = sendMessageAndAwaitResponse(sock, content, (UDP_IP, newPort))
        messagesSent+=1
    sendMessageAndAwaitResponse(sock, bytes("FIN", 'utf-8'), (UDP_IP, newPort))
    file.close()
    sock.close()
    print("closed connection with server")
    sock.close()
    timestamp=time.time()-timestamp
    printInfo(timestamp, messagesSent+1+LOST_PACKAGES, (messagesSent+1)*BUFFER_SIZE+BUFFER_SIZE*LOST_PACKAGES,LOST_PACKAGES)

def printHelp():
    print("Invalid command")
    print("Usage: python client.py (TCP || UDP) filename")

def processCommand():
    global FILE_PATH
    global FILE_NAME
    if len(sys.argv) != 3:
        printHelp()
        return 1
    protocol=sys.argv[1]
    FILE_PATH=sys.argv[2]
    FILE_NAME=ntpath.basename(FILE_PATH)
    if protocol.upper() == "TCP":
        print("Connecting to TCP Server")
        ConnectUsingTCP()
        return
    if protocol.upper() == "UDP":
        print("Connecting to UDP Server")
        ConnectUsingUDP()
        return
    printHelp()

processCommand()