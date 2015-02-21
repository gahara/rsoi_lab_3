import paths
from models import *
from mytools import *

from flask import *

import requests as myrequests
import json as pyjson

app = Flask(__name__)
app.config.update(dict(\
    SQLALCHEMY_DATABASE_URI=paths.DATABASE_PATH),\
    DEBUG=True\
)

@app.route('/logic/register', methods=['POST'])
def logic_register():
    if has_url_parameter('username') and has_url_parameter('password') and has_url_parameter('email') and has_url_parameter('phone'):
        uname = get_url_parameter('username')
        password = get_url_parameter('password')
        email = get_url_parameter('email')
        phone = get_url_parameter('phone')
        
        return from_myresponce(myrequests.post(\
            make_addr(paths.backends['session'], 'session/register'),\
            params = {'username': uname, 'password': password, 'email': email, 'phone': phone}\
        ))
    else:
        return err_400('Required parameters: username, password, email, phone')

@app.route('/logic/login', methods=['GET'])
def logic_login():
    username = get_url_parameter('username')
    password = get_url_parameter('password')
    
    return from_myresponce(myrequests.get(\
            make_addr(paths.backends['session'], 'session/login'),\
            params = {'username': username, 'password': password}\
    ))

@app.route('/logic/logout', methods=['POST'])
def logic_logout():
    sid = get_url_parameter('session_id')
    return from_myresponce(myrequests.post(\
            make_addr(paths.backends['session'], 'session/logout'),\
            params = {'session_id': sid}\
    ))

def logic_validate(): #tahes sessionid form url's param and validates it
    sid = get_url_parameter('session_id')
    return myrequests.get(make_addr(paths.backends['session'], 'session/check'), params = {'session_id': sid})

@app.route('/logic/validate', methods=['GET'])
def logic_validate_method():
    sid = get_url_parameter('session_id')
    return from_myresponce(logic_validate())

@app.route('/logic/users', methods=['GET'])
def logic_users():
    resp = logic_validate()
    if resp.status_code == 200:
        sid = get_url_parameter('session_id')
        return from_myresponce(myrequests.get(make_addr(paths.backends['session'], 'session/users'), params = {'session_id': sid}))
    else:
        return err_401()

@app.route('/logic/goods', methods=['GET'])
def logic_goods_get():
    return from_myresponce(myrequests.get(make_addr(paths.backends['goods'], 'goods')))
  
@app.route('/logic/goods', methods=['POST'])
def logic_goods_post():
    resp = logic_validate()
    if resp.status_code == 200:
        uid = resp.json()['user_id']
        if has_url_parameter('text') and has_url_parameter('description'):
            text = get_url_parameter('text')
            descr = get_url_parameter('description')
            return from_myresponce(myrequests.post(\
                make_addr(paths.backends['goods'], 'goods'),\
                params = {'user_id': uid},\
                data = pyjson.dumps({'text': text, 'description': descr}),\
                headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}\
            ))
        else:
            return err_400('Required parameters: text, description')
    else:
        return err_401()
  
@app.route('/logic/goods/<int:good_id>', methods=['GET', 'PUT', 'DELETE'])
def logic_good(good_id):
    if request.method == 'GET':
        return from_myresponce(myrequests.get(make_addr(paths.backends['goods'], 'goods/{0}'.format(good_id))))
    else:
        resp = logic_validate()
        if resp.status_code == 200:
            uid = resp.json()['user_id']
            pr = myrequests.get(make_addr(paths.backends['goods'], 'goods/{0}'.format(good_id)))
            if pr.status_code != 404:
                if (pr.json()['author_id'] == uid):
                    if request.method == 'PUT':
                        if has_url_parameter('text') and has_url_parameter('description'):
                            text = get_url_parameter('text')
                            descr = get_url_parameter('description')
                            return from_myresponce(myrequests.put(\
                                make_addr(paths.backends['goods'], 'goods/{0}'.format(good_id)),\
                                data = pyjson.dumps({'text': text, 'description': descr}),\
                                headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}\
                            ))
                        else:
                            return err_400('Required parameters: text, description')
                    else:
                        return from_myresponce(myrequests.delete(make_addr(paths.backends['goods'], 'goods/{0}'.format(good_id))))
                else:
                    return err_403()
            else:
                return err_404()
        else:
            return err_401()

@app.route('/logic/comments', methods=['GET'])
def logic_comments_get():
    if has_url_parameter('good_id') and has_url_parameter('limit') and has_url_parameter('res_per_page') and has_url_parameter('offset'):
        pid = get_url_parameter('good_id')
        rpp = get_url_parameter('res_per_page')
        cnt = get_url_parameter('limit')
        offset = get_url_parameter('offset')
        author_un = get_url_parameter('author_un')
    comments = None
    if author_un:
        userr = myrequests.get(make_addr(paths.backends['session'], '/session/users'), params = {'username': author_un})
        if userr.status_code != 404:
            user = userr.json()
            comments = myrequests.get(\
                make_addr(paths.backends['comments'], 'comments'),\
                params = {'good_id': pid, 'res_per_page': rpp, 'limit': cnt, 'offset': offset, 'user_id': user['user_id']}\
            )
        else:
            return err_404()
    else:
        comments = myrequests.get(\
            make_addr(paths.backends['comments'], 'comments'),\
            params = {'good_id': pid, 'res_per_page': rpp, 'limit': cnt, 'offset': offset}\
        )
    return ok_200(comments.json())

@app.route('/logic/comments', methods=['POST'])
def logic_comments_post():
    resp = logic_validate()
    if resp.status_code == 200:
        uid = resp.json()['user_id']
        if has_url_parameter('text') and has_url_parameter('good_id'):
            pid = get_url_parameter('good_id')
            text = get_url_parameter('text')
            return from_myresponce(myrequests.post(\
                make_addr(paths.backends['comments'], 'comments'),\
                params = {'user_id': uid, 'good_id': pid},\
                data = pyjson.dumps({'text': text}),\
                headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}\
            ))
        else:
            return err_400('Required parameters: text, good_id')
    else:
        return err_401()
              
@app.route('/logic/comments/<int:comment_id>', methods=['GET', 'PUT', 'DELETE'])
def logic_comment(comment_id):
    if request.method == 'GET':
        return from_myresponce(myrequests.get(make_addr(paths.backends['comments'], 'comments/{0}'.format(comment_id))))
    else:
        resp = logic_validate()
        if resp.status_code == 200:
            uid = resp.json()['user_id']
            cr = myrequests.get(make_addr(paths.backends['comments'], 'comments/{0}'.format(comment_id)))
            if cr.status_code != 404:
                if cr.json()['author_id'] == uid:
                    if request.method == 'PUT':
                        if has_url_parameter('text'):
                            text = get_url_parameter('text')
                            return from_myresponce(myrequests.put(\
                                make_addr(paths.backends['comments'], 'comments/{0}'.format(comment_id)),\
                                data = pyjson.dumps({'text': text}),\
                                headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}\
                            ))
                        else:
                            return err_400('Required parameters: text')
                    else:
                        return from_myresponce(myrequests.delete(make_addr(paths.backends['comments'], 'comments/{0}'.format(comment_id))))
                else:
                    return err_403()
            else:
                return err_404()
        else:
            return err_401()

#complex query
#get comments to all goods if the specified user
@app.route('/logic/good_comments_query', methods=['GET'])
def logic_good_comments_query():
    if has_url_parameter('user_id'):
        uid = get_url_parameter('user_id')
        goodsr = myrequests.get(make_addr(paths.backends['goods'], 'goods'), params = {'user_id': uid})
        goods = goodsr.json()['Goods']
        comments = []
        comr = myrequests.get(\
            make_addr(paths.backends['comments'], 'comments'),\
            data = pyjson.dumps({'good_ids': [p['id'] for p in goods]}),\
            headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}\
        )
        return from_myresponce(comr)
    else:
        return err_400('Required parameters: user_id')


 
def from_myresponce(myresp):
   if myresp.status_code == 200:
       return ok_200(myresp.json())
   elif myresp.status_code == 400:
       return err_400(myresp.json()['error'])
   elif myresp.status_code == 404:
       return err_404(myresp.json()['error'])
   elif myresp.status_code == 403:
       return err_403(myresp.json()['error'])
   elif myresp.status_code == 401:
       return err_401(myresp.json()['error'])
   else:
       return myresp
       
@app.errorhandler(200)
def ok_200(data = {}):
    return response_builder(data, 200)

@app.errorhandler(400)
def err_400(msg = 'Bad Request'):
    return response_builder({'error': msg}, 400)

@app.errorhandler(401)
def err_401(msg = 'Not authorized'):
    return response_builder({'error': msg}, 401)

@app.errorhandler(404)
def err_404(msg = 'Not found'):
    return response_builder({'error': msg}, 404)

@app.errorhandler(403)
def err_403(msg = 'Forbidden'):
    return response_builder({'error': msg}, 403)





### Other ###

if __name__ == '__main__':
    protocol, host, port = paths.backends['logic'].split(':')
    app.run(host = host[2:], port = int(port))