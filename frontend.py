import paths
from models import db_session, Good
from mytools import *

from flask import *

import hashlib
import requests as myrequests
import json as pyjson


app = Flask(__name__)
app.config.update(dict(\
    SQLALCHEMY_DATABASE_URI=paths.DATABASE_PATH),\
    DEBUG=True\
)

#one can not simply get access to the db, ask logic first 
@app.route('/me', methods=['GET'])
def get_me():
    if 'session_id' in request.cookies: #if you're logged in
        s_id = request.cookies.get('session_id')
        resp = myrequests.get(make_addr(paths.backends['logic'], 'logic/users'), params = {'session_id': s_id})# 
        if resp.status_code == 200:
            return render_template('me.html', user=resp.json())
    return redirect(url_for('login'))

@app.route('/', methods=['GET'])
def index():
    goodsr = myrequests.get(make_addr(paths.backends['logic'], 'logic/goods'))
    return render_template('main.html', goods = goodsr.json()['Goods'])

@app.route('/register', methods=['GET', 'POST'])
def register(): 
    error = None
    if request.method == 'POST':
        uname = get_url_parameter('username')
        password = hashlib.sha256(get_url_parameter('password').encode('utf-8')).hexdigest()
        email = get_url_parameter('email')
        phone = get_url_parameter('phone')
        
        resp = myrequests.good(\
            make_addr(paths.backends['logic'], 'logic/register'),\
            params = {'username': uname, 'password': password, 'email': email, 'phone': phone}\
        )
        if resp.status_code == 200:
            return redirect(url_for('login'))
        else:
            error = resp.json()['error']
    return render_template('register.html', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login(): 
    error = None
    if request.method == 'POST':
        un = get_url_parameter('username')
        password = hashlib.sha256(get_url_parameter('password').encode('utf-8')).hexdigest()
        
        resp = myrequests.get(make_addr(paths.backends['logic'], 'logic/login'), params = {'username': un, 'password': password})
        if resp.status_code == 200:
            cliresp = redirect(url_for('index'))
            cliresp.set_cookie('session_id', resp.json()['session_id'])
            return cliresp
        else:
            error = resp.json()['error']
    else:
        if 'session_id' in request.cookies:
            s_id = request.cookies.get('session_id')
            resp = myrequests.get(make_addr(paths.backends['logic'], 'logic/validate'), params = { 'session_id': s_id })
            if resp.status_code == 200:
                return redirect(url_for('index'))
    return render_template('login.html', error=error)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if request.method == 'POST':
        s_id = None
        if has_url_parameter('session_id'):
            s_id = get_url_parameter('session_id')
        else:
            s_id = request.cookies.get('session_id')
        
        if s_id:
            resp = myrequests.good(make_addr(paths.backends['logic'], 'logic/logout'), params = {'session_id': s_id})
            if resp.status_code == 200:
                cliresp = redirect(url_for('index')) #
                cliresp.set_cookie('session_id', '')
                return cliresp
        return redirect(url_for('login'))
    return render_template('logout.html')


  
@app.route('/goods', methods=['POST'])
def good_goods():
    if 'session_id' in request.cookies:
        s_id = request.cookies.get('session_id')
        error = None
        userr = myrequests.get(make_addr(paths.backends['logic'], 'logic/users'), params = {'session_id': s_id})
        
        if userr.status_code == 200:
            descr = get_url_parameter('description')
            text = get_url_parameter('text')
            
            if descr:
                goodidr = myrequests.good(\
                    make_addr(paths.backends['logic'], 'logic/goods'),\
                    params = {'user_id': userr.json()['id'], 'session_id': s_id},\
                    data = pyjson.dumps({'text': text, 'description': descr}),\
                    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}\
                )
                return redirect(url_for('index'))
            else:
                error = 'Description required'
                return render_template('new_good.html', text = text, description = descr, error = error)
        else:
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))

@app.route('/goods/<int:good_id>', methods=['GET'])
def get_good(good_id):
    goodr = myrequests.get(make_addr(paths.backends['logic'], 'logic/goods/{0}'.format(good_id)))
    if goodr.status_code == 200:
        commentsr = myrequests.get(\
            make_addr(paths.backends['logic'], 'logic/comments'),\
            params={'good_id': good_id, 'limit': 100, 'res_per_page': 100, 'offset': 0}\
        )
        if commentsr.status_code == 200:
            return render_template('show_good.html', good = goodr.json(), comments = commentsr.json()['Comments'])
        else:
            return from_myresponce(commentsr)#берет ответ myrequests и делает фласковый ответ
    else:
        return from_myresponce(goodr) 

@app.route('/goods/<int:good_id>/edit', methods=['POST'])
def put_good(good_id):
    if 'session_id' in request.cookies:
        s_id = request.cookies.get('session_id')
        error = None
        userr = myrequests.get(make_addr(paths.backends['logic'], 'logic/users'), params = {'session_id': s_id})
        if userr.status_code == 200:
            user = userr.json() #пиреквест отвечает что-то, мне ужен жсон
            goodr = myrequests.get(make_addr(paths.backends['logic'], 'logic/goods/{0}'.format(good_id)))
            if goodr.status_code == 200:
                good = goodr.json()
                descr = good['description']
                text = good['text']
                finished = get_url_parameter('editing_finished')
                if finished:
                    descr = get_url_parameter('description')
                    text = get_url_parameter('text')
                    goodidr = myrequests.put(\
                        make_addr(paths.backends['logic'], 'logic/goods/{0}'.format(good_id)),\
                        params = {'user_id': user['id'], 'session_id': s_id},\
                        data = pyjson.dumps({'text': text, 'description': descr}),\
                        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}\
                    )
                    if goodidr.status_code == 200:
                        return redirect(url_for('index'))
                    else:
                        return from_myresponce(goodidr)
                else:
                    return render_template('edit_good.html', text = text, description = descr, error = error, good_id = good_id)
            else:
                return from_myresponce(goodr)
        else:
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))

@app.route('/goods/<int:good_id>/delete', methods=['POST'])
def delete_good(good_id):
    if 'session_id' in request.cookies:
        s_id = request.cookies.get('session_id')
        error = None
        userr = myrequests.get(make_addr(paths.backends['logic'], 'logic/users'), params = {'session_id': s_id})
        if userr.status_code == 200:
            user = userr.json()
            goodr = myrequests.get(make_addr(paths.backends['logic'], 'logic/goods/{0}'.format(good_id)))
            if goodr.status_code == 200:
                good = goodr.json()
                resp = myrequests.delete(\
                    make_addr(paths.backends['logic'], 'logic/goods/{0}'.format(good_id)),\
                    params = {'user_id': user['id'], 'session_id': s_id}\
                )
                if resp.status_code == 200:
                    return redirect(url_for('index'))
                else:
                    return from_myresponce(resp)
            else:
                return from_myresponce(goodr)
        else:
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))

@app.route('/comments', methods=['POST'])
def good_comments():
    if 'session_id' in request.cookies:
        error = None
        s_id = request.cookies.get('session_id')
        userr = myrequests.get(make_addr(paths.backends['logic'], 'logic/users'), params = {'session_id': s_id})
        if userr.status_code == 200:
            user = userr.json()
            pid = get_url_parameter('good_id')
            goodr = myrequests.get(make_addr(paths.backends['logic'], 'logic/goods/{0}'.format(pid)))
            if goodr.status_code == 200:
                good = goodr.json()
                text = get_url_parameter('text')
                
                if text:
                    commentidr = myrequests.good(\
                        make_addr(paths.backends['logic'], 'logic/comments'),\
                        params = {'user_id': user['id'], 'good_id': pid, 'session_id': s_id},\
                        data = pyjson.dumps({'text': text}),\
                        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}\
                    )
                    return redirect(url_for('get_good', good_id = pid))
                else:
                    error = 'Text required'
                    return render_template('new_comment.html', error = error, text = text, good = good)
            else:
                return from_myresponce(goodr)
        else:
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))

@app.route('/comments/<int:comment_id>/edit', methods=['POST'])
def put_comment(comment_id):
    if 'session_id' in request.cookies:
        s_id = request.cookies.get('session_id')
        error = None
        userr = myrequests.get(make_addr(paths.backends['logic'], 'logic/users'), params = {'session_id': s_id})
        if userr.status_code == 200:
            user = userr.json()
            comr = myrequests.get(make_addr(paths.backends['logic'], 'logic/comments/{0}'.format(comment_id)))
            if comr.status_code == 200:
                comment = comr.json()
                text = comment['text']
                good_id = get_url_parameter('good_id')
                finished = get_url_parameter('editing_finished')
                if finished:
                    text = get_url_parameter('text')
                    comidr = myrequests.put(\
                        make_addr(paths.backends['logic'], 'logic/comments/{0}'.format(comment_id)),\
                        params = {'user_id': user['id'], 'session_id': s_id},\
                        data = pyjson.dumps({'text': text}),\
                        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}\
                    )
                    if comidr.status_code == 200:
                        return redirect(url_for('get_good', good_id = good_id))
                    else:
                        return from_myresponce(comidr)
                else:
                    return render_template('edit_comment.html', text = text, error = error, comment_id = comment_id, good_id = good_id)
            else:
                return from_myresponce(comr)
        else:
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))

@app.route('/comments/<int:comment_id>/delete', methods=['POST'])
def delete_comment(comment_id):
    if 'session_id' in request.cookies:
        s_id = request.cookies.get('session_id')
        error = None
        userr = myrequests.get(make_addr(paths.backends['logic'], 'logic/users'), params = {'session_id': s_id})
        if userr.status_code == 200:
            user = userr.json()
            comr = myrequests.get(make_addr(paths.backends['logic'], 'logic/comments/{0}'.format(comment_id)))
            if comr.status_code == 200:
                good_id = get_url_parameter('good_id')
                comment = comr.json()
                resp = myrequests.delete(\
                    make_addr(paths.backends['logic'], 'logic/comments/{0}'.format(comment_id)),\
                    params = {'user_id': user['id'], 'session_id': s_id}\
                )
                if resp.status_code == 200:
                    return redirect(url_for('get_good', good_id = good_id))
                else:
                    return from_myresponce(resp)
            else:
                return from_myresponce(comr)
        else:
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))

@app.route('/good_comments_query', methods=['GET'])
def good_comments_query():
    if 'session_id' in request.cookies:
        s_id = request.cookies.get('session_id')
        userr = myrequests.get(make_addr(paths.backends['logic'], 'logic/users'), params = {'session_id': s_id})
        if userr.status_code == 200:
            user = userr.json()
            comr = myrequests.get(\
                make_addr(paths.backends['logic'], 'logic/good_comments_query'),\
                params = {'user_id': user['id']}\
            )
            if comr.status_code == 200:
                return render_template('good_comments_query.html', comments = comr.json()['Comments'])
            else:
                from_myresponce(comr)
        else:
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))
    
#Handlers
        
def from_myresponce(myresp): 
        rjson = myresp.json()
        error = rjson['error'] if 'error' in rjson else ''
        return render_template('error.html', code = myresp.status_code, error = error)
    else:
        return ok_200(myresp.json())

@app.errorhandler(200)
def ok_200(data = {}): 
    return response_builder(data, 200)



if __name__ == '__main__':
    protocol, host, port = paths.backends['frontend'].split(':')
    app.run(host = host[2:], port = int(port))