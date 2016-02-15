# encoding=utf-8
import socket
import sys
reload(sys)
sys.setdefaultencoding('utf-8')


try:
    ip = str(sys.argv[1])
    port = int(sys.argv[2])
except Exception, e:
    print "argv error"
    sys.exit(1)

test = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    test.sendto("test", (ip, port))
except socket.error, e:
    print e

test.close()

