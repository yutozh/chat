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
        # signal.signal(signal.SIGTERM, self.sig_exit)
        # signal.signal(signal.SIGINT, self.sig_exit)
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

    def listenServer(self):
        try:
            self.client_socket.connect((self.server_host, self.server_port))
        except socket.error:
            return -1, "Cann't connect!!!"

        while True:
            read_sockets, write_sockets, error_sockets = select.select(self.socketlist, [], [])

            for sock in read_sockets:
                if sock == self.client_socket:
                    try:
                        data = sock.recv(self.BUF)
                        if not data:
                            return -2, "Disconnect with server!!!"
                        else:
                            return 0, data
                    except socket.error:
                        return -3, "Disconnect with server!!!"

                elif sock == self.client_listen_socket:
                    data, peer_addr = sock.recvfrom(self.BUF)

                    if not self.peerdict.has_key(peer_addr[0]):
                        self.peerdict[peer_addr[0]] = []
                    if not data:
                        sock.close()
                        self.current_peer = None
                        continue

                    if peer_addr[0] == self.current_peer:
                        return 1, peer_addr[0], data
                    else:
                        self.peerdict[peer_addr[0]].append(data)
                        return 2

    def toSend(self, msg):
        if self.current_peer:
            self.send_socket.sendto(msg, (str(self.current_peer), 2333))

    def changeUserInfo(self, data):
        userlist = data.split('|')
        i = 1
        for user in userlist:
            if user:
                self.user_save_dict[str(i)] = user
                i += 1

    # def getUserInfo(self):
    #     result = "当前在线用户：\n"
    #     for user_num, user_addr in self.user_save_dict.items():
    #         result += str(user_num) + ":" + str(user_addr) + "\n"
    #
    #     result += "回复[序号]，即可与指定用户聊天～"
    #
    #     print result

    def changeCurrentPeer(self, aim_ip):
        if self.current_peer:
            self.current_peer = None

        self.current_peer = aim_ip
        if aim_ip in self.peerdict.keys():
            for words in self.peerdict[aim_ip]:
                    print "<%s>" % aim_ip + words + "\n"
            self.peerdict.pop(aim_ip)

    def sig_exit(self, a, b):
        print "Bye"
        self.client_socket.close()
        sys.exit(1)


