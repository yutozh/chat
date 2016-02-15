# coding=utf-8
import MySQLdb
import sys
from config import *
reload(sys)
sys.setdefaultencoding("utf-8")


def getConn():
    conn = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, port=DB_PORT, charset='utf8', db="chat")
    return conn


class UserLoginDB(object):
    def __init__(self):
        conn = getConn()
        cur = conn.cursor()
        sql = '''create table if not exists user_login (
              id INT(8) NOT NULL PRIMARY KEY auto_increment,
              uid VARCHAR(32) NOT NULL UNIQUE,
              pwd VARCHAR (32))DEFAULT CHARSET=utf8;'''
        cur.execute(sql)
        conn.commit()
        cur.close()
        conn.close()

    def add(self, uid, pwd):
        conn = getConn()
        cur = conn.cursor()
        sql = 'INSERT INTO user_login VALUES ("", "%s", "%s");' % (uid, pwd)
        try:
            cur.execute(sql)
        except Exception, e:  # 用户名重复的异常
            print "User already exists!!!", e
        conn.commit()
        cur.close()
        conn.close()

    def delete(self, uid):
        conn = getConn()
        cur = conn.cursor()
        sql = 'DELETE FROM user_login WHERE uid="%s";' % uid
        try:
            cur.execute(sql)
        except Exception, e:  # delete异常
            print "delete error", e
        conn.commit()
        cur.close()
        conn.close()

    def update(self, uid, pwd):
        conn = getConn()
        cur = conn.cursor()
        sql = 'UPDATE user_login SET pwd="%s" WHERE uid="%s";' % (pwd, uid)
        try:
            cur.execute(sql)
        except Exception, e:
            print "update error!!!", e
        conn.commit()
        cur.close()
        conn.close()

    def search(self, uid, pwd):
        conn = getConn()
        cur = conn.cursor()
        sql = 'SELECT * FROM user_login WHERE uid="%s" AND pwd="%s";' % (uid, pwd)
        try:
            cur.execute(sql)
        except Exception, e:
            print "search error!!!", e
        res = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()
        if res:
            return "1"
        else:
            return "0"


class UserInfoDB(object):
    def __init__(self):
        conn = getConn()
        cur = conn.cursor()
        sql = '''create table if not exists user_info (
              id INT(8) NOT NULL PRIMARY KEY auto_increment,
              uid VARCHAR(32) NOT NULL UNIQUE,
              name VARCHAR(32)
              )DEFAULT CHARSET=utf8;'''
        cur.execute(sql)
        conn.commit()
        cur.close()
        conn.close()

    def add(self, uid, name):
        conn = getConn()
        cur = conn.cursor()
        sql = 'INSERT INTO user_info VALUES ("", "%s", "%s");' % (uid, name)
        try:
            cur.execute(sql)
        except Exception, e:  # 用户名重复的异常
            print "User already exists!!!", e
        conn.commit()
        cur.closae()
        conn.close()

    def delete(self, uid):
        conn = getConn()
        cur = conn.cursor()
        sql = 'DELETE FROM user_info WHERE uid="%s";' % uid
        try:
            cur.execute(sql)
        except Exception, e:  # delete异常
            print "delete error", e
        conn.commit()
        cur.close()
        conn.close()

    def update(self, uid, name):
        conn = getConn()
        cur = conn.cursor()
        sql = 'UPDATE user_info SET name="%s" WHERE uid="%s";' % (name, uid)
        try:
            cur.execute(sql)
        except Exception, e:
            print "update error!!!", e
        conn.commit()
        cur.close()
        conn.close()

    def search(self, uid):
        conn = getConn()
        cur = conn.cursor()
        sql = 'SELECT * FROM user_info WHERE uid="%s";' % uid
        try:
            cur.execute(sql)
        except Exception, e:
            print "search error!!!", e
        res = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()
        if res:
            return res
        else:
            return "0"

    def searchAll(self):
        conn = getConn()
        cur = conn.cursor()
        sql = 'SELECT * FROM user_info;'
        try:
            cur.execute(sql)
        except Exception, e:
            print "search error!!!", e
        res = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()
        if res:
            return res
        else:
            return "0"

# my_login = UserLoginDB()
# my_info = UserInfoDB()
# name = ["小红", "小白", "小黑", "小绿", "小紫"]
# for i in range(0, 5):
#     uid = "121314" + str(i)
#     pwd = str(i)*6
#     my_login.add(uid, pwd)
#     my_info.add(uid, name[i])
