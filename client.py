# encoding=utf_8
import socket
import sys

client_sockfd = socket.socket()

if len(sys.argv) != 3:
    print "Please add address and port"
    sys.exit(1)
else:
    host = sys.argv[1]
    port = int(sys.argv[2])

try:
    print host, port
    client_sockfd.connect((host, port))
except OSError, e:
    sys.stderr.write("Error %d, %s" % (e.errno, e.strerror))
    sys.exit(1)

msg = client_sockfd.recv(1024)
print "Back: %s" % msg
