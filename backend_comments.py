import paths
from models import *
from mytools import *

from flask import *

app = Flask(__name__)
app.config.update(dict(\
    SQLALCHEMY_DATABASE_URI=paths.DATABASE_PATH),\
    DEBUG=True\
)

@app.route('/comments', methods=['GET'])
def get_comments():
    g_id = get_url_parameter('good_id')
    g_ids = get_url_parameter('good_ids')
    rpp = get_url_parameter('res_per_page')
    cnt = get_url_parameter('limit')
    offset = get_url_parameter('offset')
    csq = None
    
    if has_url_parameter('user_id'):        
        u_id = get_url_parameter('user_id')
        csq = db_session.query(Comment, User)\
            .filter(User.id == Comment.author_id)\
            .filter(Comment.author_id == u_id)
    else:
        csq = db_session.query(Comment, User)\
            .filter(User.id == Comment.author_id)
    
    if g_id:
        csq = csq.filter(Comment.good_id == g_id)
    else:
        csq = csq.filter(Comment.good_id.in_(g_ids))
    
    if cnt and offset:
        csq = csq.offset(offset).limit(cnt)
    cs = csq.all()
    
    retv = []
    results_per_page = int(rpp) if rpp else None
    for i, cu in enumerate(cs):
        c, u = cu
        crepr = c.to_dict()
        if results_per_page:
            page = int(i / results_per_page)
            crepr.update({'page': page})
        crepr.update({'username': u.username})
        retv += [crepr]
    return ok_200({'Comments': retv})

@app.route('/comments/<int:comment_id>', methods=['GET'])
def get_comment(comment_id):
    c = Comment.query.filter_by(id = comment_id).first()
    return ok_200(c.to_dict()) if c else err_404()

@app.route('/comments', methods=['POST'])
def good_comment():
    g_id = get_url_parameter('good_id')
    u_id = get_url_parameter('user_id')
    text = get_url_parameter('text')
    c = Comment(u_id, g_id, text)
    db_session.add(c)
    db_session.commit()
    return ok_200({'comment_id': c.id})



@app.route('/comments/<int:comment_id>', methods=['PUT'])
def put_comment(comment_id):
    text = get_url_parameter('text')
    c = Comment.query.filter_by(id = comment_id).first()
    if c:
        if not c.isdeleted:
            c.text = text
            db_session.commit()
            return ok_200()
        else:
            return err_403('Comment was deleted')
    else:
        return err_404()

@app.route('/comments/<int:comment_id>', methods=['DELETE'])
def del_comment(comment_id):
    text = get_url_parameter('text')
    c = Comment.query.filter_by(id = comment_id).first()
    if c:
        c.delete()
        db_session.commit()
        return ok_200()
    else:
        return err_404()

# Error handlers

@app.errorhandler(404)
def err_404(msg = 'Not found'):
    return response_builder({'error': msg}, 404)

@app.errorhandler(403)
def err_403(msg = 'Forbidden'):
    return response_builder({'error': msg}, 403)

@app.errorhandler(200)
def ok_200(data = {}):
    return response_builder(data, 200)


if __name__ == '__main__':
    protocol, host, port = paths.backends['comments'].split(':')
    app.run(host = host[2:], port = int(port))