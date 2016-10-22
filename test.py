#!flask/bin/python
from util import Database
db = Database()
print('getting password for \'root\'\npwd is: ')
print(db.getPassword('root'))
