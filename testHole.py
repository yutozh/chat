# encoding=utf-8
import socket
import json
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

# 从服务器上主动发送消息给客户来测试
try:
    ip = str(sys.argv[1])
    port = int(sys.argv[2])
except Exception, e:
    print "argv error"
    sys.exit(1)

test = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
test.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
test.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
try:
    test.bind(("10.105.3.129", 8866))
    data = {"id": "1213141", "msg": "hahaha"}
    data = json.dumps(data)
    test.sendto(data, (ip, port))
except socket.error, e:
    print e


