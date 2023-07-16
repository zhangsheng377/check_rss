import logging

from flask import Flask, render_template, request, make_response
from gevent.pywsgi import WSGIServer

from UTILS.utils import check_rss
from UTILS.db_sheets import insert_rsses

port = 22224
app = Flask(__name__, template_folder='site')

logging.getLogger().setLevel(logging.INFO)


@app.route('/')
def index():
    return render_template('index.html', title='监控rss', check_elements=['uuid', 'title'],
                           need_download=['not_download', 'need_download'])


@app.route('/subscribe_rss', methods=['POST'])
def subscribe_rss():
    rss_url = request.values.get('rss_url')
    check_element = request.form.get('check_element')
    need_download = request.form.get('need_download')
    if check_rss(rss_url):
        if insert_rsses(document={'_id': rss_url, 'last_uuid': '', 'last_title': '', 'feed_title': '',
                                  'check_element': check_element, 'need_download': need_download}):
            logging.info(f"insert_rsses success: {rss_url}")
            return "插入数据库成功"
        else:
            logging.warning(f"insert_rsses false: {rss_url}")
            return "插入数据库失败"
    else:
        return "rss_url解析失败"


@app.route('/get_my_rss', methods=['POST', 'GET'])
def get_my_rss():
    with open('/mnt/nfs/download/myrss/myrss.xml', 'r') as f:
        s = f.read()
    return str(s), 200, {'Content-Type': 'text/xml; charset=utf-8'}


if __name__ == '__main__':
    # app.run(host='0.0.0.0', port=port, debug=True)
    server = WSGIServer(("0.0.0.0", port), app)
    logging.info("Server started")
    server.serve_forever()
