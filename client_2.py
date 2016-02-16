# encoding=utf-8
from Tkinter import *
import threading
import socket
import select
import Queue
import time
import sys
import json
reload(sys)
sys.setdefaultencoding('utf-8')

serverip = "182.254.146.38"
localip = "192.168.0.103"


class ClientGUI(object):
    listFriend = {}
    localip = ""
    myname = ""
    myid = ""

    def __init__(self, master, queue, ip, id):

        self.master = master
        self.queue = queue
        ClientGUI.localip = ip
        ClientGUI.myid = id
        self.master.geometry("200x600+200+100")
        self.master.resizable(width=True, height=True)

        Label(self.master, text="我的联系人列表", fg="white", bg="blue", height="2", font="2").pack(fill=X)
        self.var = StringVar()
        self.li = Listbox(self.master, listvariable=self.var, fg="green", width="30", font="2")
        self.li.bind("<Double-ButtonRelease-1>", self.newChat)

        scrl = Scrollbar(self.master)
        scrl.pack(side=RIGHT, fill=Y)
        self.li.configure(yscrollcommand=scrl.set)  # 将list和scroll绑在一起
        self.li.pack(side=LEFT, fill=BOTH)
        scrl["command"] = self.li.yview  # 下拉时可以带动LIST下拉

        self.chatdict = {}  # 存放每个聊天窗口对应的ChatGUI对象，KEY为ip
        # self.listFriend = []  # 好友列表的缓存
        self.msgqueue = {}  # 消息队列字典，KEY为id
        self.listFriendname = []  # 好友昵称列表
        self.listFriendip = []
        self.listFriendid = []
    # 处理后台传来的消息

    def processIncoming(self):
        while self.queue.qsize():
            try:
                msg = self.queue.get(0)
                # 好友列表变更
                if msg[0] == 0:
                    alluser_dict = json.loads(msg[1])

                    if len(ClientGUI.listFriend) == 0:
                        flag = 1
                    else:
                        flag = 0

                    if ClientGUI.listFriend != alluser_dict:
                        ClientGUI.listFriend = alluser_dict
                        self.listFriendname = []
                        self.listFriendip = []

                        # =================================
                        ClientGUI.myname = ClientGUI.listFriend[ClientGUI.myid]["name"]
                        if flag == 1:
                            for i in ClientGUI.listFriend.keys():
                                self.msgqueue[i] = Queue.Queue()  # 只在第一次刷新时创建消息队列
                        for i in ClientGUI.listFriend.keys():
                            self.listFriendid.append(i)
                        for i in ClientGUI.listFriend.values():
                            self.listFriendname.append(i["name"])
                            self.listFriendip.append(i["ip"])

                        self.var.set(tuple(self.listFriendname))
                # 新消息
                elif msg[0] == 1:
                    remote_addr = msg[1]
                    remote_data = msg[2]

                    msg_id = remote_data["id"]         # 消息来源id
                    msg_content = remote_data["msg"]   # 消息内容

                    # self.msgqueue[remote_addr].put(remote_data)
                    self.msgqueue[msg_id].put(msg_content)
            except Queue.Empty:
                pass

    def newChat(self, event):
        num = int(self.li.curselection()[0])  # 索引
        # num = self.li.get(self.li.curselection())
        ip = self.listFriendip[num]
        name = self.listFriendname[num]
        id = self.listFriendid[num]
        chat = chatGUI(id, name, self.msgqueue[id])
        # self.chatdict[ip] = chat

    def getMyName(self):
        self.master.wm_title("Client %s" % ClientGUI.myname)


class chatGUI(object):
    def __init__(self, id, name, queue):
        self.newDialog = Tk()
        self.newDialog.wm_title("与 %s 交谈中..." % name)
        self.newDialog.geometry("600x600+450+100")
        self.t_show = Text(self.newDialog, width=62, height=15, bg="lightgreen", font=2)

        self.t_show.pack(pady=20)
        self.t_input = Text(self.newDialog, width=62, height=8, font=2)

        self.newDialog.update()
        self.bt_send = Button(self.newDialog, width=10, height=3, text="发送", bg="purple", fg="white", font=2, command=self.toSend)
        self.bt_clear = Button(self.newDialog, width=10, height=3, text="清空", bg="purple", fg="white", font=2, command=self.toClear)

        self.t_input.pack(pady=0)
        self.bt_send.pack(side=RIGHT, pady=5)
        self.bt_clear.pack(side=RIGHT, pady=5)

        self.peerid = id
        self.peeraddr = ClientGUI.listFriend[self.peerid]["ip"]  # ip

        # ======开始打洞=======
        self.digHole()

        self.running = True
        self.queue = queue  # 消息队列
        self.periodicCall()  # 周期循环处理

        self.newDialog.mainloop()  # 主事件监听

    # 向显示框中添加消息
    def addMessage(self, addr, data, color="white"):
        res = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + addr + '\n' + data
        self.t_show.insert(END, res, color)
        self.newDialog.update()

    # 发送消息
    def toSend(self):
        message = self.t_input.get('0.0', END)
        message.replace("\n", "")
        if message != "":
            data = {"id": ClientGUI.myid, "msg": message}

            self.t_input.delete(0.0, END)
            self.addMessage("ME", data["msg"], 'green')
            if self.peeraddr == "x":
                # 目的ip为x,即对方离线
                data["id"] = ClientGUI.myid + "|" + self.peerid
                data = json.dumps(data)
                print "sended"
                ClientConn.send_socket_default.sendto(data, (serverip, 8666))  # 离线留言发送至服务器
            else:
                data = json.dumps(data)

                ClientConn.send_socket.sendto(data, tuple(self.peeraddr))
                # ClientConn.send_socket.sendto(data, (str(self.peerip), 2333))

    # 清空输入框
    def toClear(self):
        self.t_input.delete(0.0, END)

    # 周期循环处理控制函数
    def periodicCall(self):
        self.t_show.after(200, self.periodicCall)
        self.processIncoming()
        if not self.running:
            self.newDialog.destroy()

    # 周期循环处理执行函数，不断处理消息队列的消息
    def processIncoming(self):
        queue = self.queue
        self.peeraddr = ClientGUI.listFriend[self.peerid]["ip"]  # 不断刷新ip，监控是否上线
        while queue.qsize():
            try:
                msg = queue.get(0)
                if msg:
                    peername = ClientGUI.listFriend[self.peerid]["name"]
                    self.addMessage(peername, msg)
            except Queue.Empty:
                pass

    def digHole(self):
        # 用户不在线，无需打洞
        if self.peeraddr == "x":
            print "True x"
            return True
        try:
            ClientConn.send_socket.sendto("hello", tuple(self.peeraddr))
            ClientConn.send_socket.sendto(ClientGUI.myid + "|" + str(self.peeraddr), (serverip, 8866))
            print tuple(self.peeraddr), "ok"
        except socket.error, e:
            print "Hole error", e
            return False
        # 打洞完成
        return True


class ClientConn(object):
    # 使用统一的后台发送数据端口
    send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # 离线留言端口
    send_socket_default = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def __init__(self, id, token, master):
        self.local_ip = localip
        self.server_host = serverip
        self.server_port = 8008
        self.listen_port = 2333
        self.hole_port = 8866
        self.BUF = 4096
        self.BACKLOG = 10
        self.token = token

        self.client_socket = socket.socket()
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.client_socket.bind((self.local_ip, 6666))
        self.client_socket.settimeout(5)

        self.socketlist = []

        # signal.signal(signal.SIGTERM, self.sig_exit)
        # signal.signal(signal.SIGINT, self.sig_exit)
        self.socketlist.append(self.client_socket)

        # 用来发送的socket绑定
        # ====================
        ClientConn.send_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # ClientConn.send_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        ClientConn.send_socket.bind((self.local_ip, self.listen_port))  # 发送端口与接受消息端口相同

        self.client_listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # self.client_listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.client_listen_socket.bind((self.local_ip, self.listen_port))

        self.socketlist.append(self.client_listen_socket)

        ClientConn.send_socket_default.bind((self.local_ip, 6888))

        self.master = master  # 主界面
        self.queue = Queue.Queue()  # 消息队列
        self.gui = ClientGUI(master, self.queue, self.local_ip, id)  # 主界面对应对象
        self.running = True

        # 新线程，跑后台程序，通过消息队列返回结果
        self.thread1 = threading.Thread(target=self.clientStart, args=(id,))
        self.thread1.start()

        # 周期循环调用控制函数
        self.periodicCall()

    # 周期性调用GUI中的函数，去处理queue的变化
    def periodicCall(self):
        self.master.after(200, self.periodicCall)
        self.gui.processIncoming()
        self.gui.getMyName()
        if not self.running:
            self.master.destroy()

    # 后台实现函数，两个socket,一个与服务器保持链接(TCP)，另一个监听接受消息端口（UDP）
    def clientStart(self, id):
        try:
            self.client_socket.connect((self.server_host, self.server_port))
            self.client_socket.send(self.token)
            # 上线后，通知打洞请求端口，自爆家门（ip+port）
            ClientConn.send_socket.sendto("u"+str(id), (self.server_host, self.hole_port))
        except socket.error:
            return -1, "Cann't connect!!!"

        t_1 = threading.Thread(target=self.cs, args=(self.client_socket, ))
        t_1.start()
        t_2 = threading.Thread(target=self.cl, args=(self.client_listen_socket, ))
        t_2.start()
        # while self.running:
        #
        #     read_sockets, write_sockets, error_sockets = select.select(self.socketlist, [], [])
        #     res = ""
        #     for sock in read_sockets:
        #         if sock == self.client_socket:
        #             try:
        #                 data = sock.recv(self.BUF)
        #                 if not data:
        #                     res = (-2, "Disconnect with server!!!")
        #                 elif data == "test":
        #                     continue
        #                 else:
        #                     res = (0, data)
        #             except socket.error:
        #                 res = (-3, "Disconnect with server!!!")
        #         elif sock == self.client_listen_socket:
        #             print "ooooooo"
        #             data, peer_addr = sock.recvfrom(self.BUF)
        #             print data
        #             if not data:
        #                 sock.close()
        #                 continue
        #             if data == "hello":
        #                 continue
        #             if data.startswith("$"):
        #                 print "$$$$$$$$"
        #                 hole_aim_addr = data[1:]
        #                 hole_aim_addr = tuple(eval(hole_aim_addr))
        #                 ClientConn.send_socket.sendto("hello", hole_aim_addr)
        #                 continue
        #             data = json.loads(data)   # 解析含有id的data
        #             res = (1, peer_addr[0], data)
        #         self.queue.put(res)

    def cs(self, sock):
        while True:
            try:
                data = sock.recv(self.BUF)
                if not data:
                    res = (-2, "Disconnect with server!!!")
                elif data == "test":
                    continue
                else:
                    res = (0, data)
            except socket.error:
                res = (-3, "Disconnect with server!!!")
            self.queue.put(res)

    def cl(self, sock):
        while True:
            print "ooooooo"
            data, peer_addr = sock.recvfrom(self.BUF)
            print data
            if not data:
                sock.close()
                continue
            if data == "hello":
                continue
            if data.startswith("$"):
                print "$$$$$$$$"
                hole_aim_addr = data[1:]
                hole_aim_addr = tuple(eval(hole_aim_addr))
                ClientConn.send_socket.sendto("hello", hole_aim_addr)
                continue
            data = json.loads(data)   # 解析含有id的data
            res = (1, peer_addr[0], data)
            self.queue.put(res)


class loginGUI(object):
    def __init__(self):
        self.login = Tk()
        self.login.title("用户登录")
        self.login.geometry("240x200+550+250")
        self.l_id = Label(self.login, width="8", height="3", text="帐号")
        self.l_pwd = Label(self.login, width="8", height="3", text="密码")
        self.l_alert = Label(self.login, width="18", height="3", fg="red")

        self.en_id = Entry(self.login, width="22",)
        self.en_pwd = Entry(self.login, width="22", show="*")

        self.bt_login = Button(self.login, width="8", text="登录", bg="green", fg="white", font=2, command=self.tologin)
        self.l_id.grid(row=0, column=0)
        self.l_pwd.grid(row=1, column=0)
        self.en_id.grid(row=0, column=1)
        self.en_pwd.grid(row=1, column=1)
        self.bt_login.grid(row=2, column=0, columnspan=2, padx=60)
        self.l_alert.grid(row=3, column=0, columnspan=2)

        self.localip = localip
        self.token = ""
        self.server_host = serverip
        self.server_port = 8888
        self.BUF = 4096
        self.login.mainloop()

    def tologin(self):
        id = self.en_id.get()
        pwd = self.en_pwd.get()

        login_dict = {"uid": id, "pwd": pwd}
        conn_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn_socket.bind((self.localip, 1234))
        conn_socket.settimeout(1)
        try:
            print (self.server_host, self.server_port)
            conn_socket.connect((self.server_host, self.server_port))
        except socket.error, e:
            print e
            self.l_alert["text"] = "连接服务器出错"
            conn_socket.close()
            exit(1)

        conn_socket.send(json.dumps(login_dict))
        res = conn_socket.recv(self.BUF)
        if res == "0":
            self.l_alert["text"] = "用户名或密码错误"
            conn_socket.close()
        else:
            self.token = res
            conn_socket.close()
            self.login.destroy()
            root = Tk()

            ClientConn(id, self.token, root)
            root.mainloop()

    def gettoken(self):
        return self.token

mylogin = loginGUI()

