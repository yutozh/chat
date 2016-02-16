# coding=utf-8
import socket
import select
import sys
import signal
import json
import time
import userDB
import hashlib
from threading import *


class Server(object):
    def __init__(self):
        self.ip = "10.105.3.129"

        self.port = 8008
        self.loginport = 8888
        self.default_listen_port = 8666
        self.default_send_port = 8686
        self.hole_listen_port = 8866  # 监听打洞请求的端口
        self.hole_sent_port = 8866     # 打洞请求发送端口
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_login_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_default_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_default_sent_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_hole_listen = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_hole_sent = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # self.host = socket.gethostname()   # 获得主机名，zyt-K52Jc
        self.host = self.ip
        self.BACKLOG = 10  # 最大Listen连接数
        self.RECV_BUF = 4096  # 单次发送数据量
        self.socketlist = []  # 列表，包括了监听socket和各客户端连接的socket
        self.userdict = {}  # 所有用户,key是id，value是ip和昵称
        self.onlineuserdict = {}  # 只包括连接上的id：ip
        self.tokendict = {}
        self.alluser = {}

        self.defaultlist = {}

        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)  # 重用端口，不会出现Address used
        self.server_socket.bind((self.host, self.port))  # 绑定到指定端口

        self.server_login_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_login_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.server_login_socket.bind((self.host, self.loginport))

        self.server_default_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_default_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.server_default_socket.bind((self.host, self.default_listen_port))

        self.server_hole_sent.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_hole_sent.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.server_hole_sent.bind((self.host, self.hole_sent_port))

        self.server_hole_listen.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_hole_listen.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.server_hole_listen.bind((self.host, self.hole_listen_port))

        self.server_default_sent_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_default_sent_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.server_default_sent_socket.bind((self.host, self.default_send_port))

        self.server_socket.listen(self.BACKLOG)  # 开始监听
        self.server_login_socket.listen(self.BACKLOG)
        self.socketlist.append(self.server_socket)
        self.socketlist.append(self.server_login_socket)
        self.socketlist.append(self.server_default_socket)
        self.socketlist.append(self.server_hole_listen)

        signal.signal(signal.SIGTERM, self.sig_exit)
        signal.signal(signal.SIGINT, self.sig_exit)

        self.t1 = Thread(target=self.updateuser, args=())
        self.t2 = Thread(target=self.testonline, args=())
        self.t1.start()
        self.t2.start()

    def updateuser(self):
        while True:
            my_info_db = userDB.UserInfoDB()
            self.alluser = my_info_db.searchAll()
            time.sleep(5)

    def testonline(self):
        while True:
            # self.broadcast(self.server_socket, "test")
            self.sendstatus()
            time.sleep(15)

    def start(self):

        print "Server start at : " + self.host + ":" + str(self.port)

        while True:
            read_sockets, write_sockets, error_sockets = select.select(self.socketlist, [], [])  # 异步输入
            for sock in read_sockets:
                if sock == self.server_socket:
                    client_socket, client_addr = sock.accept()  # 获得请求的客户端信息

                    try:
                        # 验证登录
                        login_token = client_socket.recv(self.RECV_BUF)

                        for i in self.tokendict.keys():
                            print i
                        uid = login_token.split("|")[1]
                    except Exception, e:
                        print "token error", e
                        continue

                    if login_token != self.tokendict[str(uid)]:
                        client_socket.close()
                        continue

                    # 成功则保留socket
                    self.socketlist.append(client_socket)  # 连接的客户端socket添加到列表中

                    print "Client: [%s:%s] is connected!\n" % client_addr

                    # for i in self.alluser:
                    #     self.userdict[i[1]] = {}
                    #     if i[1] in self.onlineuserdict.keys():   # i[1]是ID号
                    #         self.userdict[i[1]]["ip"] = self.onlineuserdict[i[1]]
                    #     else:
                    #         self.userdict[i[1]]["ip"] = "x"
                    #     self.userdict[i[1]]["name"] = i[2]
                    #
                    # back_info = json.dumps(self.userdict)
                    # self.broadcast(sock, back_info)
                    self.sendstatus()

                    if uid in self.defaultlist.keys():
                        for id, connent in self.defaultlist[uid].items():
                            for i in connent:
                                data = {"id": id, "msg": i}
                                data = json.dumps(data)
                                self.server_default_sent_socket.sendto(data, (client_addr[0], 2333))
                        self.defaultlist[uid] = {}

                elif sock == self.server_login_socket:
                    client_login_socket, client_login_addr = sock.accept()
                    try:
                        login = client_login_socket.recv(self.RECV_BUF)
                        login = json.loads(login)
                        user_id = login["uid"]
                        user_pwd = login["pwd"]
                    except Exception, e:
                        print "login key error"
                        continue
                    my_login_db = userDB.UserLoginDB()
                    res = my_login_db.search(user_id, user_pwd)
                    if res == "1":         # 0000000000000000000000
                        # 加密获得token
                        sha = hashlib.sha1()
                        sha.update(str(time.time()) + str(user_id))
                        token = sha.hexdigest() + "|" + str(user_id)
                        self.tokendict[str(user_id)] = token

                        client_login_socket.send(token)

                        client_login_socket.close()
                    else:
                        client_login_socket.send("0")
                        client_login_socket.close()
                        continue

                elif sock == self.server_default_socket:
                    data, peer_addr = sock.recvfrom(self.RECV_BUF)
                    try:
                        data = json.loads(data)
                        from_id = data["id"].split("|")[0]
                        aim_id = data["id"].split("|")[1]  # 离线消息目标用户id
                    except Exception, e:
                        print "default_socket error", e
                        continue
                    if aim_id not in self.defaultlist.keys():
                        self.defaultlist[aim_id] = {}
                    if len(self.defaultlist[aim_id]) == 0:
                        self.defaultlist[aim_id][from_id] = []
                    self.defaultlist[aim_id][from_id].append(data["msg"])  # 把消息放进该用户对应的目的ip下

                elif sock == self.server_hole_listen:
                    hole_aim_addr, request_addr = sock.recvfrom(self.RECV_BUF)

                    print hole_aim_addr, request_addr
                    try:
                        if hole_aim_addr:
                            if hole_aim_addr.startswith("u"):
                                init_id = hole_aim_addr[1:]

                                # 此时request_addr为客户端的外网ip+port
                                # 将此ip返回给客户端作为打洞地址，可实现打洞
                                self.onlineuserdict[init_id] = request_addr
                                continue
                            hole_aim_addr = tuple(eval(hole_aim_addr))

                            self.server_hole_sent.sendto("$" + str(request_addr), hole_aim_addr)
                            print "sss", hole_aim_addr
                    except Exception, e:
                        print "hole_listen error", e
                        continue

    def sendstatus(self):
        for i in self.alluser:
            uid = str(i[1])
            self.userdict[uid] = {}
            if i[1] in self.onlineuserdict.keys():   # i[1]是ID号
                self.userdict[uid]["ip"] = self.onlineuserdict[uid]
            else:
                self.userdict[uid]["ip"] = "x"
            self.userdict[uid]["name"] = i[2]

        back_info = json.dumps(self.userdict)
        self.broadcast(self.server_socket, back_info)

    def broadcast(self, sock, msg):
        for each_sock in self.socketlist:
            if each_sock != self.server_socket and each_sock != self.server_login_socket and \
                    each_sock != self.server_default_socket and each_sock != self.server_hole_listen\
                    and sock != each_sock:
                try:
                    each_sock.send(msg)
                except socket.error:
                    self.socketlist.remove(each_sock)
                    print "有用户退出了"
                    each_sock.close()
                    continue

    def sig_exit(self, a, b):
        for sock in self.socketlist:
            sock.close()
        print "Bye~\n"
        sys.exit(0)

if __name__ == "__main__":
    myserver = Server()
    myserver.start()
