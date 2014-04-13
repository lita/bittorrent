from flask import session
import uuid

bt_sessions = dict()

btkey = 'bt-session-key'

def new():
    session[btkey] = uuid.uuid1()
    bt_sessions[session[btkey]] = dict()

def set(key, value):
    bt_sessions[session[btkey]][key] = value

def get(*a, **kw):
    return bt_sessions[session[btkey]].get(*a, **kw)

