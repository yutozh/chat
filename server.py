# encoding=utf-8
import socket
import sys

server_sockfd = socket.socket()

host = socket.gethostname()
port = 8088
server_sockfd.bind((host, port))

server_sockfd.listen(20)

while True:
    print host
    client_sockfd, addr = server_sockfd.accept()

    print "message comes from ", addr
    msg = "Hello , I'm server"
    client_sockfd.send(msg)
    client_sockfd.close()
