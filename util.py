import cymysql
import base64
import pysodium
import os
from flask_restful import fields, marshal
from dateutil import parser


class Database:
    __conn = 0

    __recipe_fields = {
        'titel': fields.String,
        'kategorie': fields.String,
        'zutaten': fields.String,
        'beschreibung': fields.String,
        'bild_Path': fields.String,
        'datum': fields.DateTime,
        'rezept_ID': fields.Integer
    }

    __category_fields = {
        '_ID': fields.Integer,
        'name': fields.String
    }

    def __init__(self):
        self.connect();

    def connect(self):
        pwdFile = open('favicon', 'r')
        pwd = pwdFile.read()
        pwdFile.close()
        # read is probably also reading the eof or something, so just use 10 chars
        self.__conn = cymysql.connect(host='localhost', user='rezepte', passwd=pwd[:10], db='rezept_verwaltung', charset='utf8')

    def getPassword(self, username):
        auth = Authentification(self.__conn)
        return auth.getPassword(username)

    def getAllRecipes(self):
        if not self.__conn._is_connect():
            self.connect();
        cur = self.__conn.cursor(cymysql.cursors.DictCursor)
        cur.execute("SELECT * FROM rezepte;")
        recipes = []
        for res in cur.fetchall():
            recipes.append(marshal(res, self.__recipe_fields))
        cur.execute("SELECT * FROM kategorie;")
        categories = []
        for res in cur.fetchall():
            categories.append(marshal(res, self.__category_fields))
        cur.execute("SELECT NOW()")
        res = cur.fetchone()
        time = res['NOW()'].strftime('%Y-%m-%d %H:%M:%S')
        return {'recipes': recipes, 'categories': categories, 'time': time}

    def getRecipe(self, rid):
        if not self.__conn._is_connect():
            self.connect();
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

    def getUpdateRecipe(self, lastSync):
        if not self.__conn._is_connect():
            self.connect();
        lasttime = parser.parse(lastSync)
        cur = self.__conn.cursor()
        cur.execute("SELECT UPDATE_TIME FROM information_schema.tables WHERE TABLE_SCHEMA = 'rezept_verwaltung' AND TABLE_NAME = 'rezepte'")
        res = cur.fetchone()
        updatetime = res[0]
        f = open("test.log", "w")
        f.write("update: " + updatetime.strftime("%Y-%m-%d %H:%M"))
        f.write("lastSync: " + lasttime.strftime("%Y-%m-%d %H:%M"))
        f.close()

        if (lasttime < updatetime):
            return self.getAllRecipes()

    def insertRecipe(self, title, category, ingredients, description, bild):
        if not self.__conn._is_connect():
            self.connect();
        cur = self.__conn.cursor(cymysql.cursors.DictCursor)
        if bild is not None:
            cur.execute("INSERT INTO rezepte(titel, kategorie, zutaten, beschreibung, bild_Path) VALUES (\"" + title + "\", " + str(category) + ", \"" + ingredients + "\", \"" + description + "\", \"images/" + bild + "\");")
        else:
            cur.execute("INSERT INTO rezepte(titel, kategorie, zutaten, beschreibung, bild_Path) VALUES (\"" + title + "\", " + str(category) + ", \"" + ingredients + "\", \"" + description + "\", \"\");")
        cur.execute("SELECT LAST_INSERT_ID() as _ID")
        _id = cur.fetchone()['_ID']
        self.updateSearchIndex(_id)
        cur.execute("SELECT * FROM rezepte WHERE rezept_ID = " + str(_id));
        res = cur.fetchone()
        return marshal(res, self.__recipe_fields)

    def updateSearchIndex(self, _id):
        if not self.__conn._is_connect():
            self.connect();
        cur = self.__conn.cursor(cymysql.cursors.DictCursor)
        cur.execute("DELETE FROM such_Index WHERE rezept_ID = " + str(_id))
        cur.execute("SELECT rezept_ID, titel, kategorie.name AS kategorie, zutaten FROM rezepte INNER JOIN kategorie ON kategorie._ID = rezepte.kategorie WHERE rezept_ID = " + str(_id))
        res = cur.fetchone()
        keys = res["titel"].split() + res["kategorie"].split() + res["zutaten"].split("<br>")
        for key in keys:
            cur.execute("INSERT INTO such_Index (begriff, rezept_ID) VALUES (\"" + key + "\", \"" + str(_id) + "\")")

    def deleteRecipe(self, _id):
        if not self.__conn._is_connect():
            self.connect();
        cur = self.__conn.cursor(cymysql.cursors.DictCursor)
        cur.execute("SELECT bild_Path FROM rezepte WHERE rezept_ID = " + str(_id))
        img = cur.fetchone()["bild_Path"]
        if (img is not None):
            try:
                os.remove("~http/Rezeptbuch/" + img)
            except FileNotFoundError:
                print("FNF")
        cur.execute("DELETE FROM such_Index WHERE rezept_ID = " + str(_id))
        cur.execute("DELETE FROM rezepte WHERE rezept_ID = " + str(_id))


    def getAllCategories(self):
        if not self.__conn._is_connect():
            self.connect();
        cur = self.__conn.cursor(cymysql.cursors.DictCursor)
        cur.execute("SELECT * FROM kategorie;")
        categories = []
        for res in cur.fetchall():
            categories.append(marshal(res, self.__category_fields))
        return {'categories' : categories}

    def insertCategory(self, name):
        if not self.__conn._is_connect():
            self.connect();
        cur = self.__conn.cursor(cymysql.cursors.DictCursor)
        cur.execute("INSERT INTO kategorie(name) VALUES (\"" + name + "\");");
        cur.execute("SELECT LAST_INSERT_ID() as _ID")
        return {'id' : cur.fetchone()['_ID']}

class Authentification:
    __conn = 0

    def __init__(self, connection):
        self.__conn = connection

    def connect(self):
        pwdFile = open('favicon', 'r')
        pwd = pwdFile.read()
        pwdFile.close()
        # read is probably also reading the eof or something, so just use 10 chars
        self.__conn = cymysql.connect(host='localhost', user='rezepte', passwd=pwd[:10], db='rezept_verwaltung', charset='utf8')

    def __encrypt(self, pwd, nonce, key):
        return base64.b64encode(pysodium.crypto_secretbox(pwd.encode(), nonce, key))

    def getPassword(self, username):
        if not self.__conn._is_connect():
            self.connect();
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
                return pysodium.crypto_secretbox_open(ciph, nonce, key).decode()
