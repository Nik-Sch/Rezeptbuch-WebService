import os
from flask import Flask, request, jsonify, abort, make_response, redirect, url_for, send_from_directory
from flask_restful import Api, Resource, reqparse
from flask_httpauth import HTTPBasicAuth
from flask_compress import Compress
from util import Database
from werkzeug.utils import secure_filename
from requests.auth import HTTPDigestAuth
import requests
import hashlib
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
        self.reqparse.add_argument('bild_Path', type=str, required=False,
                                    location='json')
        super(RecipeListAPI, self).__init__()

    def get(self):
        return db.getAllRecipes(auth.username())

    
    def post(self):
        if not db.hasWriteAccess(auth.username()):
            return make_response(jsonify({'error': 405}), 405)
        args = self.reqparse.parse_args()
        result = db.insertRecipe(auth.username(), args['titel'], args['kategorie'], args['zutaten'], args['beschreibung'], "")
        if result is not None:
            return result
        return make_response(jsonify({'error': 'an error occured'}), 501)


class RecipeAPI(Resource):
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
        self.reqparse.add_argument('bild_Path', type=str, required=False,
                                   location='json')

        super(RecipeAPI, self).__init__()

    def get(self, rezept_ID):
        result = db.getRecipe(auth.username(), rezept_ID)
        if result is not None:
            return result
        return make_response(jsonify({'error': 'Not found'}), 404)

    def put(self, rezept_ID):
        if not db.hasWriteAccess(auth.username()):
            return make_response(jsonify({'error': 405}), 405)
        args = self.reqparse.parse_args()
        print(args)
        result = db.updateRecipe(rezept_ID, auth.username(), args['titel'], args['kategorie'], args['zutaten'], args['beschreibung'], args['bild_Path'])
        if result:
            return make_response('', 200)
        else:
            return make_response(jsonify({'error': 'No recipe updated'}), 404)
        return make_response(jsonify({'error': 'an error occured'}), 501)

    def delete(self, rezept_ID):
        if not db.hasWriteAccess(auth.username()):
            return make_response(jsonify({'error': 405}), 405)
        url = 'http://rezeptbuch/delete_recipe.php?recipe_id=' + str(rezept_ID)
        requests.get(url, auth=HTTPDigestAuth(
            auth.username(), get_password(auth.username())))
        # db.deleteRecipe(rezept_ID)
        return make_response("", 204)


class RecipeSyncAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        super(RecipeSyncAPI, self).__init__()

    def get(self, syncedTime):
        result = db.getUpdateRecipe(auth.username(), syncedTime)
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
        return db.getAllCategories(auth.username())

    def post(self):
        if not db.hasWriteAccess(auth.username()):
            return make_response(jsonify({'error': 405}), 405)
        args = self.reqparse.parse_args()
        result = db.insertCategory(auth.username(), args['name'])
        if result is not None:
            return result
        return make_response(jsonify({'error': 'an error occured'}), 501)


# # uploading image
IMAGE_FOLDER = './images/'

class ImageListAPI(Resource):
    decorators = [auth.login_required]

    def post(self):
        if not db.hasWriteAccess(auth.username()):
            return make_response(jsonify({'error': 405}), 405)
        if 'image' not in request.files:
            return make_response(jsonify({'error': 'No image'}), 400)
        file = request.files['image']
        if file:
            try:
                hash = hashlib.sha256()
                # with open(file, 'rb') as f:
                fb = file.read(65536)
                while len(fb) > 0:
                    hash.update(fb)
                    fb = file.read(65536)
                name = hash.hexdigest() + '.jpg'
                jpg = Image.open(file).convert('RGB')
                jpg.save(IMAGE_FOLDER + name)
                response = jsonify({'name': name})
                response.status_code = 201
                response.autocorrect_location_header = False
                return response
            except IOError as e:
                print(e)
                return make_response(jsonify({'error': 'File isn\'t an image'}), 400)

class ImageAPI(Resource):

    def get(self, name):
        return send_from_directory(IMAGE_FOLDER, name)

    @auth.login_required
    def delete(self, name):
        if (os.path.exists(IMAGE_FOLDER + name)):
            os.remove(IMAGE_FOLDER + name)
        return make_response(jsonify(), 200)




# @auth.login_required
# @app.route('/images/<name>', methods=['DELETE'])
# def delete_image(name):
        # if not db.hasWriteAccess(auth.username()):
        #     return make_response(jsonify({'error': 405}), 405)
#     if request.method == 'DELETE':
#         try:
#             os.remove(IMAGE_FOLDER + secure_filename(name))
#         except:
#             return make_response(jsonify({'error': 'no such image'}), 404)
#         response = jsonify()
#         response.status_code = 204
#         return response
#     return make_response(jsonify({'error': 'only delete'}), 403)

api.add_resource(RecipeAPI, '/recipes/<int:rezept_ID>', endpoint='recipe')
api.add_resource(RecipeListAPI, '/recipes', endpoint='recipes')
api.add_resource(RecipeSyncAPI, '/recipes/<string:syncedTime>', endpoint='recipesync')
api.add_resource(CategoryListAPI, '/categories', endpoint='categories')
api.add_resource(ImageListAPI, '/images', endpoint='images')
api.add_resource(ImageAPI, '/images/<string:name>', endpoint='image')

if __name__ == '__main__':
    app.run(debug=True, port=5425, host='0.0.0.0')
