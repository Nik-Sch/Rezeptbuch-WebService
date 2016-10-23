#!flask/bin/python
from util import Database
from flask_restful import fields, marshal
import json

recipe_fields = {
    'titel': fields.String,
    'kategorie': fields.String,
    'zutaten': fields.String,
    'beschreibung': fields.String,
    'bild_Path': fields.String,
    'datum': fields.DateTime,
    'id': fields.Integer
}

db = Database()
f = open('output.txt', 'w')
recipes = db.getAllRecipes()
json.dump({'tasks': [marshal(recipe, recipe_fields) for recipe in recipes]}, f)
f.close()
