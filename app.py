import os
from flask import Flask, request, jsonify, abort, make_response, redirect, url_for
from flask_restful import Api, Resource, reqparse
from flask_httpauth import HTTPBasicAuth
from flask_compress import Compress
from util import Database
from werkzeug.utils import secure_filename
from PIL import Image

app = Flask(__name__, static_url_path="")
api = Api(app)
Compress(app)
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
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('titel', type=str, required=True,
                                    help='No title provided',
                                    location='json')
        self.reqparse.add_argument('kategorie', type=int, required=True,
                                    help='No category provided',
                                    location='json')
        self.reqparse.add_argument('zutaten', type=str, required=True,
                                    help='No ingredients provided',
                                    location='json')
        self.reqparse.add_argument('beschreibung', type=str, required=True,
                                    help='No description provided',
                                    location='json')
        self.reqparse.add_argument('bild', type=str, required=False,
                                    location='json')
        super(RecipeListAPI, self).__init__()

    def get(self):
        return db.getAllRecipes()

    def post(self):
        if (auth.username() == 'gast'):
            return make_response(jsonify({'error': 405}), 405);
        args = self.reqparse.parse_args()
        result = db.insertRecipe(args['titel'], args['kategorie'], args['zutaten'], args['beschreibung'], args['bild'])
        if result is not None:
            return result
        return make_response(jsonify({'error': 'an error occured'}), 501)

class RecipeAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()

        super(RecipeAPI, self).__init__()

    def get(self, rezept_ID):
        result = db.getRecipe(rezept_ID)
        if result is not None:
            return result
        return make_response(jsonify({'error': 'Not found'}), 404)

    def put(self, rezept_ID):
        if (auth.username() == 'gast'):
            return make_response(jsonify({'error': 405}), 405);
        # TODO: update data in db
        return "stuff"

    def delete(self, rezept_ID):
        if (auth.username() == 'gast'):
            return make_response(jsonify({'error': 405}), 405);
        db.deleteRecipe(rezept_ID)
        return make_response("", 204)

class RecipeSyncAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        super(RecipeSyncAPI, self).__init__()

    def get(self, syncedTime):
        result = db.getUpdateRecipe(syncedTime)
        if result is not None:
            return result

        # returning 418 (teapot) because volley android client has problems with redirections (304)
        return make_response(jsonify({'error': 'Not Modified'}), 418)

class CategoryListAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('name', type=str, required=True,
                                    help='No title provided',
                                    location='json')
        super(CategoryListAPI, self).__init__()

    def get(self):
        return db.getAllCategories()

    def post(self):
        if (auth.username() == 'gast'):
            return make_response(jsonify({'error': 405}), 405);
        args = self.reqparse.parse_args()
        result = db.insertCategory(args['name'])
        if result is not None:
            return result
        return make_response(jsonify({'error': 'an error occured'}), 501)

# uploading image
IMAGE_FOLDER = '/srv/http/Rezeptbuch/images/'

@app.route('/images', methods=['GET', 'POST'])
@auth.login_required
def upload_file():
    if (auth.username() == 'gast'):
        return make_response(jsonify({'error': 405}), 405);
    # show http form if no post
    if request.method == 'POST':
        if 'image' not in request.files:
            return make_response(jsonify({'error': 'No image'}), 400)
        file = request.files['image']
        if file.filename == '':
            return make_response(jsonify({'error': 'No filename'}), 400)
        if file:
            filename = secure_filename(file.filename)
            try:
                jpg = Image.open(file)
                jpg.save(IMAGE_FOLDER + filename, "JPEG")
                response = jsonify()
                response.status_code = 201
                response.autocorrect_location_header = False
                return response
            except IOError:
                return make_response(jsonify({'error': 'File isn\'t an image'}), 400)

    return '''
    <!doctype html>
    <title>Upload image</title>
    <form method=post enctype=multipart/form-data>
        <input type=file name=image>
        <input type=submit value=Upload>
    </form>
    '''

@auth.login_required
@app.route('/images/<name>', methods=['DELETE'])
def delete_image(name):
    if (auth.username() == 'gast'):
        return make_response(jsonify({'error': 405}), 405);
    if request.method == 'DELETE':
        try:
            os.remove(IMAGE_FOLDER + secure_filename(name))
        except:
            return make_response(jsonify({'error': 'no such image'}), 404)
        response = jsonify()
        response.status_code = 204
        return response
    return make_response(jsonify({'error': 'only delete'}), 403)

api.add_resource(RecipeAPI, '/recipes/<int:rezept_ID>', endpoint='recipe')
api.add_resource(RecipeListAPI, '/recipes', endpoint='recipes')
api.add_resource(CategoryListAPI, '/categories', endpoint='categories')
api.add_resource(RecipeSyncAPI, '/recipes/<string:syncedTime>', endpoint='recipesync')

if __name__ == '__main__':
    app.run(debug=True, port=5425, host='0.0.0.0')
