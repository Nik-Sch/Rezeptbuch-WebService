#!flask/bin/python3
from flask import Flask
import authentification
import pysodium
import base64

app = Flask(__name__)

@app.route('/')
def index():
    key = str(pysodium.randombytes(pysodium.crypto_secretbox_KEYBYTES))
    enc = authentification.encrypt("Apfelkuchen", key)
    dec = authentification.decrypt(enc, key)
    return enc.decode() + '\n' + dec.decode()

if __name__ == '__main__':
    app.run(debug=True, port=5425, host='0.0.0.0')
