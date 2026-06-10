import hashlib
import os

def hash_password(password, salt=None):
    if salt is None:
        salt = os.urandom(16).hex()
    salted = password + salt
    return hashlib.sha256(salted.encode()).hexdigest(), salt

def verify_password(input_password, db_hash, db_salt):
    input_hash, _ = hash_password(input_password, db_salt)
    return input_hash == db_hash
