import cymysql
import base64
import pysodium
from  flask_restful import fields, marshal


class Database:
    __conn = 0

    __recipe_fields = {
        'titel': fields.String,
        'kategorie': fields.String,
        'zutaten': fields.String,
        'beschreibung': fields.String,
        'bild_Path': fields.String,
        'datum': fields.DateTime,
        'rezept_ID': fields.Url('recipe')
    }

    def __init__(self):
        pwdFile = open('favicon', 'r')
        pwd = pwdFile.read()
        pwdFile.close()
        # read is probably also reading the eof or something, so just use 10 chars
        self.__conn = cymysql.connect(host='localhost', user='rezepte', passwd=pwd[:10], db='rezept_verwaltung', charset='utf8')

    def getPassword(self, username):
        auth = Authentification(self.__conn)
        return auth.getPassword(username)

    def getAllRecipes(self):
        cur = self.__conn.cursor(cymysql.cursors.DictCursor)
        cur.execute("SELECT * FROM rezepte;")
        recipes = []
        for res in cur.fetchall():
            recipes.append(marshal(res, self.__recipe_fields))
        return {'recipes': recipes}

    def getRecipe(self, rid):
        cur = self.__conn.cursor(cymysql.cursors.DictCursor)
        print(rid)
        cur.execute("SELECT * FROM rezepte WHERE rezept_ID=" + str(rid));
        recipe = 0
        for res in cur.fetchall():
            recipe = marshal(res, self.__recipe_fields)
        if recipe != 0:
            return {'recipe': recipe}
        else:
            return None

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
