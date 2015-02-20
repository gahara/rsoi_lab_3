from flask import *

def make_addr(addr, f): #adds to the addres line, like http://127.0.0.1:50000/frontend
    return '/'.join([addr, f]) 

def response_builder(r, s):
    resp = jsonify(r)
    resp.status_code = s
    return resp

def has_url_parameter(name):
    rjson = request.get_json()
    part = (name in request.args) or (name in request.form) or (name in request.headers)
    return ((name in rjson) or part) if rjson else part    

def get_url_parameter(name, request = request):
    rjson = request.get_json()
    if name in request.args:
        return request.args[name]
    elif name in request.form:
        return request.form[name]
    elif name in request.headers:
        return request.headers[name]
    elif rjson:
        if name in rjson:
            return rjson[name]
    else:
        return None
                                                                             


