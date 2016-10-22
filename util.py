import cymysql
import base64
import pysodium

class Database:
    __conn = 0

    def __init__(self):
        pwdFile = open('favicon', 'r')
        pwd = pwdFile.read()
        pwdFile.close()
        print(pwd)
        # read is probably also reading the eof or something, so just use 10 chars
        self.__conn = cymysql.connect(host='localhost', user='rezepte', passwd=pwd[:10], db='rezept_verwaltung', charset='utf8')

    def getPassword(self, username):
        auth = Authentification(self.__conn)
        return auth.getPassword(username)


class Authentification:
    __conn = 0

    def __init__(self, connection):
        self.__conn = connection

    def __encrypt(self, pwd, nonce, key):
        return base64.b64encode(pysodium.crypto_secretbox(pwd.encode(), nonce, key))

    def getPassword(self, username):
        cur = self.__conn.cursor()
        cur.execute("SELECT user, encrypted FROM user;")
        for res in cur.fetchall():
            if res[0] == username:
                keyFile = open('logo', 'r')
                key = base64.b64decode(keyFile.read())
                keyFile.close()
                decoded = base64.b64decode(res[1])
                nonce = decoded[:pysodium.crypto_secretbox_NONCEBYTES]
                ciph = decoded[pysodium.crypto_secretbox_NONCEBYTES:]
                return pysodium.crypto_secretbox_open(ciph, nonce, key)
