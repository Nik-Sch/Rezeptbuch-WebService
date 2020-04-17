import pymysql
import base64
import pysodium
import os
from flask_restful import fields, marshal
from dateutil import parser


class Database:

    __recipe_fields = {
        'titel': fields.String,
        'kategorie': fields.Integer,
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
        self.connect()

    def connect(self, username = None):
        conn = pymysql.connect(host=os.environ['MYSQL_HOST'],
                               user=os.environ['MYSQL_USER'],
                               passwd=os.environ['MYSQL_PASSWORD'],
                               db=os.environ['MYSQL_DATABASE'],
                               charset='utf8mb4',
                               cursorclass=pymysql.cursors.DictCursor)
        if username != None:
            cur = conn.cursor()
            cur.execute("SELECT _ID, read_only, user FROM user;")
            userId = -1
            for res in cur.fetchall():
                if res['user'] == username:
                    userId = res['_ID']
                    break
                if res['read_only'] == username:
                    userId = res['_ID']
                    break
            return conn, userId
        else:
            return conn

    def getAllRecipes(self, username):
        conn, userId = self.connect(username)
        try:
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM rezepte WHERE user_id = {userId};")
            recipes = []
            for res in cur.fetchall():
                recipes.append(marshal(res, self.__recipe_fields))
            cur.execute(f"SELECT * FROM kategorie WHERE user_id = {userId};")
            categories = []
            for res in cur.fetchall():
                categories.append(marshal(res, self.__category_fields))
            cur.execute("SELECT NOW()")
            res = cur.fetchone()
            time = res['NOW()'].strftime('%Y-%m-%d %H:%M:%S')
            return {'recipes': recipes, 'categories': categories, 'time': time}
        finally:
            conn.close()

    def getRecipe(self, username, rid):
        conn, userId = self.connect(username)
        try:
            cur = conn.cursor()
            cur.execute(
                f"SELECT * FROM rezepte WHERE rezept_ID={str(rid)} and user_id = {userId}")
            recipe = 0
            for res in cur.fetchall():
                recipe = marshal(res, self.__recipe_fields)
            if recipe != 0:
                return {'recipe': recipe}
            else:
                return None
        finally:
            conn.close()

    def getUpdateRecipe(self, username, lastSync):
        conn = self.connect()
        try:
            cur = conn.cursor()
            lasttime = parser.parse(lastSync)
            cur.execute(
                "SELECT UPDATE_TIME FROM information_schema.tables WHERE TABLE_SCHEMA = 'rezept_verwaltung' AND TABLE_NAME = 'rezepte'")
            res = cur.fetchone()
        finally:
            conn.close()
        updatetime = res['UPDATE_TIME']
        if (lasttime < updatetime):
            return self.getAllRecipes(username)

    def insertRecipe(self, username, title, category, ingredients, description, bild):
        conn, userId = self.connect(username)
        try:
            cur = conn.cursor()
            if not bild:
                bild = ""
            query = f"INSERT INTO rezepte(titel, kategorie, zutaten, beschreibung, bild_Path, user_id) VALUES ('{title}', {str(category)}, '{ingredients}', '{description}', '{bild}', '{userId}');"
            cur.execute(query)
            # print(query)
            cur.execute("SELECT LAST_INSERT_ID() as _ID")
            _id = cur.fetchone()['_ID']
            self.updateSearchIndex(cur, _id)
            cur.execute("SELECT * FROM rezepte WHERE rezept_ID = " + str(_id))
            res = cur.fetchone()
            return marshal(res, self.__recipe_fields)
        finally:
            conn.commit()
            conn.close()

    def updateRecipe(self, id, username, title, category, ingredients, description, bild):
        conn, userId = self.connect(username)
        try:
            cur = conn.cursor()
            if not bild:
                bild = ""
            query = f"UPDATE `rezepte` SET `titel` = '{title}', `kategorie` = '{str(category)}', `zutaten` = '{ingredients}', `beschreibung` = '{description}', `bild_Path` = '{bild}', `user_id` = '{userId}'  WHERE `rezepte`.`rezept_ID` = {str(id)}"
            return cur.execute(query) == 1
        finally:
            conn.commit()
            conn.close()

    def updateSearchIndex(self, cur, _id):
        cur.execute("DELETE FROM such_Index WHERE rezept_ID = " + str(_id))
        cur.execute(
            f"SELECT rezept_ID, titel, kategorie.name AS kategorie, zutaten FROM rezepte INNER JOIN kategorie ON kategorie._ID = rezepte.kategorie WHERE rezept_ID = {str(_id)}")
        res = cur.fetchone()
        keys = res["titel"].split() + res["kategorie"].split() + \
            res["zutaten"].split("<br>")
        for key in keys:
            cur.execute(
                f"INSERT INTO such_Index (begriff, rezept_ID) VALUES ('{key}', '{str(_id)}')")

    # def deleteRecipe(self, username, _id):
        # TODO ?
        # self.ensureConnection()
        # cur = self.__conn.cursor(pymysql.cursors.DictCursor)
        # userId = self.__userId[username]
        # cur.execute(f"SELECT bild_Path FROM rezepte WHERE rezept_ID = {str(_id)}")
        # try:
        #     img = cur.fetchone()["bild_Path"]
        #     if (img is not None):
        #         try:
        #             os.remove("~http/Rezeptbuch/" + img)
        #         except FileNotFoundError:
        #             print("FNF")
        # except:
        #     print("caught image exception")
        # cur.execute("DELETE FROM such_Index WHERE rezept_ID = " + str(_id))
        # cur.execute("DELETE FROM rezepte WHERE rezept_ID = " + str(_id))

    def getAllCategories(self, username):
        conn, userId = self.connect(username)
        try:
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM kategorie WHERE user_id = {userId};")
            categories = []
            for res in cur.fetchall():
                categories.append(marshal(res, self.__category_fields))
            return {'categories': categories}
        finally:
            conn.close()

    def insertCategory(self, username, name):
        conn, userId = self.connect(username)
        try:
            cur = conn.cursor()
            query = f"INSERT INTO kategorie(name, user_id) VALUES ('{name}', {userId});"
            print(query)
            cur.execute(query)
            cur.execute("SELECT LAST_INSERT_ID() as _ID")
            return {'id': cur.fetchone()['_ID']}
        finally:
            conn.commit()
            conn.close()


# authentification

    def __encrypt(self, pwd, nonce, key):
        return base64.b64encode(pysodium.crypto_secretbox(pwd.encode(), nonce, key))

    def __decrypt(self, encrypted):
        keyFile = open('logo', 'r')
        key = base64.b64decode(keyFile.read())
        keyFile.close()
        decoded = base64.b64decode(encrypted)
        nonce = decoded[:pysodium.crypto_secretbox_NONCEBYTES]
        ciph = decoded[pysodium.crypto_secretbox_NONCEBYTES:]
        return pysodium.crypto_secretbox_open(ciph, nonce, key).decode()

    def getPassword(self, username):
        conn = self.connect()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT user, encrypted, read_only, read_only_encrypted FROM user;")
            for res in cur.fetchall():
                if res['user'] == username:
                    return self.__decrypt(res['encrypted'])
                if res['read_only'] == username:
                    return self.__decrypt(res['read_only_encrypted'])
        finally:
            conn.close()

    def hasWriteAccess(self, username):
        conn = self.connect()
        try:
            cur = conn.cursor()
            cur.execute("SELECT user FROM user;")
            for res in cur.fetchall():
                if res['user'] == username:
                    return True
            return False
        finally:
            conn.close()
