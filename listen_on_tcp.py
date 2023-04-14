#!/usr/bin/env python3

import sys
import socket
import select

TCP_IP = '192.168.2.4'
TCP_PORT = 8899
BUFFER_SIZE = 1024
param = []

print('Listening for client...')
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((TCP_IP,TCP_PORT))
server.listen(1)
rxset = [server]
txset = []

while True:
    rxfds, txfds, exfds = select.select(rxset, txset, rxset)
    for sock in rxfds:
        if sock is server:
            conn, addr = server.accept()
            conn.setblocking(0)
            rxset.append(conn)
            print('Connection from address:', addr)
        else:
            try:
                data = sock.recv(BUFFER_SIZE)
                if data == ";" :
                    print("Received all the data")
                    for x in param:
                        print(x)
                    param = []
                    rxset.remove(sock)
                    sock.close()
                else:
                    print("received data: ", data)
                    param.append(data)
            except:
                print("Connection closed by remote end")
                param = []
                rxset.remove(sock)
                sock.close()
