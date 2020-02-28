import time
import hashlib
import hmac
from base64 import b64encode

def epoch_time():
    return int(time.time() * 1000)

def get_signature(akid, method, time, password):
    message = bytes(akid + method + time, 'utf-8')
    key = bytes(password, 'utf-8')
    digester = hmac.new(key, message, hashlib.sha1)

    digest = digester.digest()
    signature = str(b64encode(digest), 'utf-8')

    return signature