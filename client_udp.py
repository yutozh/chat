# coding=utf-8
import socket
import sys
import select
import signal


class Client(object):
    def __init__(self, ip):
        self.client_socket = socket.socket()
        self.client_socket.bind((ip, 6666))
        self.client_socket.settimeout(5)
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.server_host = "zyt-K52Jc"
        self.server_port = 8008
        self.socketlist = []
        self.BUF = 4096
        self.BACKLOG = 10
        signal.signal(signal.SIGTERM, self.sig_exit)
        signal.signal(signal.SIGINT, self.sig_exit)
        self.socketlist.append(self.client_socket)
        self.socketlist.append(sys.stdin)

        self.client_listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

        self.listen_port = 2333
        self.local_ip = ip
        self.client_listen_socket.bind((self.local_ip, self.listen_port))
        # self.client_listen_socket.listen(self.BACKLOG)
        self.socketlist.append(self.client_listen_socket)

        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_socket.bind((self.local_ip, 6777))
        self.user_save_dict = {}
        self.peerdict = {}    # 存 不是当前用户发来的消息
        self.current_peer = None

    def start(self):

        try:
            self.client_socket.connect((self.server_host, self.server_port))
        except socket.error:
            print "Can't connect!!!"
            sys.exit(1)

        print 'Connected to remote host. Start sending messages...\n'

        self.prompt(1)

        while True:
            read_sockets, write_sockets, error_sockets = select.select(self.socketlist, [], [])

            for sock in read_sockets:
                if sock == self.client_socket:
                    try:
                        data = sock.recv(self.BUF)
                        if not data:
                            print "\nDisconnected with server!!!"
                            sys.exit(1)
                        else:
                            # user_info = self.getUserInfo(self.user_save)
                            # sys.stdout.write(user_info)
                            self.changeUserInfo(data)
                            sys.stdout.write("有好友上线啦\n")
                            self.prompt()
                            sys.stdout.flush()
                    except socket.error:
                        print "Socket Error\n"
                        sys.exit(1)

                elif sock == self.client_listen_socket:
                    # try:
                    # peer_socket, peer_addr = sock.accept()
                    data, peer_addr = sock.recvfrom(self.BUF)
                    # self.socketlist.append(peer_socket)

                    if not self.peerdict.has_key(peer_addr[0]):
                        self.peerdict[peer_addr[0]] = []
                    if not data:
                        sock.close()
                        self.current_peer = None
                        self.getUserInfo()
                        self.prompt()
                        continue

                    if peer_addr[0] == self.current_peer:
                        self.prompt(2, "\n<%s>: %s" % (peer_addr[0], data))
                    else:
                        self.peerdict[peer_addr[0]].append(data)
                        # self.peerdict[peer_socket] = []
                        print str(peer_addr) + "给你发来消息\n"
                        self.prompt()

                    # except socket.error, e:
                    #     print "peer_socket error", e

                elif sock == sys.stdin:
                    msg = sys.stdin.readline()
                    self.inputJudge(msg)
                    # self.client_socket.send(msg)
                    self.prompt()
                # else:
                #     data = sock.recv(self.BUF)
                #     if not data:
                #         sock.close()
                #         self.socketlist.remove(sock)
                #         self.current_peer = None
                #         print "对方掉线了"
                #         self.getUserInfo()
                #         self.prompt()
                #         continue
                #     if sock == self.current_peer:
                #         self.prompt(2, "\n<%s>: %s" % (sock.getpeername(), data))
                #     else:
                #         self.peerdict[sock].append(data)

    def changeUserInfo(self, data):
        userlist = data.split('|')
        i = 1
        for user in userlist:
            if user:
                self.user_save_dict[str(i)] = user
                i += 1

    def getUserInfo(self):
        result = "当前在线用户：\n"
        for user_num, user_addr in self.user_save_dict.items():
            result += str(user_num) + ":" + str(user_addr) + "\n"

        result += "回复[序号]，即可与指定用户聊天～"

        print result

    def inputJudge(self, msg):
        msg = msg.replace('\n', "")
        if msg:
            if msg == "_c":
                self.getUserInfo()
            elif ('[' in msg) and (']' in msg):
                try:
                    user_num = msg[1]
                    aim_ip = self.user_save_dict[user_num]
                except TypeError, KeyError:
                    print "error_Type or Key"
                    exit()
                self.changeCurrentPeer(aim_ip)
            elif msg == "_b":
                # self.current_peer.close()
                # self.socketlist.remove(self.current_peer)
                self.prompt(2, "已退出该聊天")
                self.current_peer = None
                self.getUserInfo()
            else:
                if self.current_peer:
                    self.send_socket.sendto(msg, (str(self.current_peer), 2333))
                    # self.current_peer.send(msg)

    def changeCurrentPeer(self, aim_ip):
        if self.current_peer:
            self.current_peer = None

        self.current_peer = aim_ip
        if aim_ip in self.peerdict.keys():
            for words in self.peerdict[aim_ip]:
                    print "<%s>" % aim_ip + words + "\n"
            self.peerdict.pop(aim_ip)
        self.prompt(2, "现在可以和%s聊天了\n" % str(aim_ip))

#         if self.current_peer:
#             self.current_peer.close()
#             self.socketlist.remove(self.current_peer)
#             self.current_peer = None
#         for sock in self.socketlist:
#
#             if sock != sys.stdin and sock != self.client_listen_socket and sock != self.client_socket:
#                 if sock.getpeername()[0] == aim_ip:
#                     self.current_peer = sock
#                     for words in self.peerdict[sock]:
#                         print words + "\n"
#                     self.prompt(2, "(已响应%s的连接，可以开始聊天了)\n" % str(aim_ip))
#                     return
#         conn_socket = socket.socket()
#         conn_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
#         conn_socket.bind((self.local_ip, 6777))
# # *****************************************************
#         addr_conn = [aim_ip, self.listen_port]
#         addr_conn = tuple(addr_conn)
#
#         conn_socket.connect(addr_conn)
#         self.socketlist.append(conn_socket)
#
#         self.current_peer = conn_socket
#         self.prompt(2, "(已与%s连接上，可以开始聊天了)" % str(aim_ip))

    def prompt(self, flag=0, msg=""):
        if flag == 0:
            words = ""
        elif flag == 1:
            words = "(回复：_c 获得当前用户在线信息; _b 更换聊天对象; _o 打开对话列表)"
        elif flag == 2:
            words = msg
        else:
            print "flag error"
            exit()
        sys.stdout.write(words + "\n<You>:")
        sys.stdout.flush()

    def sig_exit(self, a, b):
        print "Bye"
        self.client_socket.close()
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print "Please add ip!!!"
        exit()
    else:
        try:
            # host = sys.argv[1]
            # port = int(sys.argv[2])
            ip = sys.argv[1]
        except TypeError, e:
            sys.stderr.write(e.message)
            exit(1)

        myclient = Client(ip)
        myclient.start()

