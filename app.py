#!flask/bin/python
from flask import Flask, jsonify, abort, make_response
from flask_restful import Api, Resource, reqparse
from flask_httpauth import HTTPBasicAuth
from util import Database

app = Flask(__name__, static_url_path="")
api = Api(app)
auth = HTTPBasicAuth()
db = Database()

@auth.get_password
def get_password(username):
    return db.getPassword(username)

@auth.error_handler
def unauthorized():
    # return 403 instead of 401 to prevent default browser dialog
    return make_response(jsonify({'message': 'Unauthorized access'}), 403)

class RecipeListAPI(Resource):
#    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('titel', type=str, required=True,
                                    help='No title provided',
                                    location='json')
        self.reqparse.add_argument('kategorie', type=str, required=True,
                                    help='No category provided',
                                    location='json')
        self.reqparse.add_argument('zutaten', type=str, required=True,
                                    help='No ingredients provided',
                                    location='json')
        self.reqparse.add_argument('beschreibung', type=str, required=True,
                                    help='No description provided',
                                    location='json')
        super(RecipeListAPI, self).__init__()

    def get(self):
        return db.getAllRecipes()

    def post(self):
        args = self.reqparse.parse_args()
        # TODO: insert new recipe

class RecipeAPI(Resource):
#     decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()

        super(RecipeAPI, self).__init__()

    def get(self, rezept_ID):
        result = db.getRecipe(rezept_ID)
        if result is not None:
            return result
        return make_response(jsonify({'error': 'Not found'}), 404)

    def put(self, rezept_ID):
        # TODO: update data in db
        return "stuff"

    def delete(self, rezept_ID):
        # TODO: delete row in db
        return "stuff"

api.add_resource(RecipeAPI, '/api/recipes/<int:rezept_ID>', endpoint='recipe')
api.add_resource(RecipeListAPI, '/api/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(debug=True, port=5425, host='0.0.0.0')
