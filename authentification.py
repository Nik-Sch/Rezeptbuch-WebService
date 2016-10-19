import pysodium
import base64
import MySQLdb

nonce = str(pysodium.randombytes(pysodium.crypto_secretbox_NONCEBYTES))

def encrypt(pwd, key):
    return base64.b64encode(pysodium.crypto_secretbox(pwd.encode(), nonce, key))

def decrypt(encrypted, key):
    decoded = base64.b64decode(encrypted)
    return pysodium.crypto_secretbox_open(decoded, nonce, key)
