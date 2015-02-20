import paths
from models import *
from mytools import *

from flask import *

app = Flask(__name__)
app.config.update(dict(\
    SQLALCHEMY_DATABASE_URI=paths.DATABASE_PATH),\
    DEBUG=True\
)

@app.route('/goods', methods=['GET'])
def get_goods():
    goods = None
    if has_url_parameter('user_id'):
        uid = get_url_parameter('user_id')
        goods = db_session.query(Good, User)\
            .filter(User.id == Good.author_id)\
            .filter(Good.author_id == uid)\
            .all()
    else:
        goods = db_session.query(Good, User)\
            .filter(User.id == Good.author_id)\
            .all() #attach userame and good
        
    resp = []
    for p, u in goods:
        r = p.to_dict_short()
        r.update({'username': u.username})
        resp += [r]
    return ok_200({'Goods' : resp})

@app.route('/goods', methods=['POST'])
def good_good():
    user_id = get_url_parameter('user_id')
    text = get_url_parameter('text')
    description = get_url_parameter('description')
    p = Good(user_id, description, text)
    db_session.add(p)
    db_session.commit()
    return ok_200({'good_id': p.id})

@app.route('/goods/<int:good_id>', methods=['GET'])
def get_good(good_id):
    p = Good.query.filter_by(id = good_id).first()
    return ok_200(p.to_dict()) if p else err_404() 

@app.route('/goods/<int:good_id>', methods=['PUT'])
def put_good(good_id):
    p = Good.query.filter_by(id = good_id).first()
    if p:
        text = get_url_parameter('text')
        description = get_url_parameter('description')
        p.text = text
        p.description = description
        db_session.commit()
        return ok_200()
    else:
        return err_404()

@app.route('/goods/<int:good_id>', methods=['DELETE'])
def del_good(good_id):
    p = Good.query.filter_by(id = good_id).first()
    if p:
        db_session.delete(p)
        db_session.commit()
        return ok_200()
    else:
        return err_404()

# Error handlers

@app.errorhandler(404)
def err_404(msg = 'Not found'):
    return response_builder({'error': msg}, 404)

@app.errorhandler(200)
def ok_200(data = {}):
    return response_builder(data, 200)


if __name__ == '__main__':
    protocol, host, port = paths.backends['goods'].split(':')
    app.run(host = host[2:], port = int(port))