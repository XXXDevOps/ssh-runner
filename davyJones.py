import geventwebsocket
from gevent import monkey
monkey.patch_all()
from flask import Flask, Response, request, jsonify, render_template
from flask_restful import Api
from flask_sockets import Sockets
from gevent import pywsgi
import threading
from geventwebsocket.handler import WebSocketHandler
import logging
from fabric import Connection
import uuid
import connection_data
import webshell
import time
import json

setting = {
	'log': {
		'level': 'debug'
	}
}
logger = logging.getLogger()
logger.setLevel(getattr(logging, setting.get("log").get("level", "debug").upper()))
GLOBAL_EXITED_VAR = False





app = Flask(__name__)
api = Api(app)
flk_ws = Flask(__name__+"_ws")
#init websocket
socket = Sockets(flk_ws)





#api.add_resource(handlers.scriptrunner.RemoteScript, '/v1/remote')

import connectors



@app.errorhandler(KeyError)
def special_exception_handler(error):
	return jsonify({"error": str(error)}), 501


@app.route("/v1/runtime/remote", methods=['GET'])
def runtime_remote():
	#params = request.json
	uid = request.environ['REQUEST_UUID']
	params = request.values.to_dict()
	host = params['host']
	params['hosts'] = [host]
	del params['host']
	c = connectors.ConnecterInteractive(**params)
	c.open()
	c.run_async()
	connection_data.REQUEST_DICT[uid] = c
	return Response(
		c.read_result_until_done()
	)


@app.route("/v1/remote", methods=['POST'])
def remote():
	params = request.json
	c = connectors.ConnecterScriptRunner(**params)
	c.open()
	r = c.run()
	c.close()
	return jsonify(r)


@app.route("/v1/remote/cmd", methods=['POST'])
def cmd():
	params = request.json
	cmd = params.pop("cmd")
	if not cmd:
		raise KeyError("you need specify argument 'cmd'")
	c = connectors.ConnecterScriptRunner(**params)
	c.open()
	r = c.run(cmd=cmd, if_script=False)
	c.close()
	return jsonify(r)



@socket.route('/terminal/<host>/<port>/<user>')
def term_in(ws, host, port, user):
	uid = uuid.uuid4().hex
	pkey = ws.receive()
	if pkey == 'connect':
		pkey = None
	else:
		logging.info("[%s]receive." % uid)
	c = webshell.Connect(host, user=user, port=int(port), pkey=pkey)
	c.open()
	logging.info("[%s]ssh tunnel created." % uid)
	connection_data.REQUEST_DICT[uid] = c
	connection_data.SSH_RUNTIME_DICT[uid] = ws
	t = threading.Thread(target=start_ssh_backend_recv_thread, args=(uid,))
	t.setDaemon(True)
	t.start()
	logging.info("[%s]ssh tunnel start to receive standard input ." % uid)
	while not ws.closed:
		msg = ws.receive()
		if str(msg).startswith('{"resize"'):
			resize = json.loads(msg)['resize']
			c.chan.resize_pty(*resize)
		else:
			try:
				c.chan.sendall(str(msg))
			except Exception as err:
				logging.warning("[%s]send command failed %r" % (uid, err))
				break
	c.close()
	logging.info("[%s]ssh tunnel closed." % uid)
	del connection_data.REQUEST_DICT[uid]
	connection_data.SSH_RUNTIME_DICT.pop(uid)
	logging.info("[%s]ssh web socket is exited." % uid)


def start_ws_thread():
	def tmp_fun():
		ws_server = pywsgi.WSGIServer(("0.0.0.0", 5100), flk_ws, handler_class=WebSocketHandler)
		ws_server.serve_forever()
	t = threading.Thread(target=tmp_fun)
	t.setDaemon(True)
	t.start()
	logging.info("[websocket_threading] start running")



def start_ssh_backend_recv_thread(uid):
	ws = connection_data.SSH_RUNTIME_DICT[uid]
	c = connection_data.REQUEST_DICT[uid]
	logging.info("[%s]ssh stdout threading generated." % uid)
	for msg in c.reciever():
		try:
			ws.send(msg.decode('utf-8'))
		except geventwebsocket.exceptions.WebSocketError:
			logging.info("[%s]web socket disconnect." % uid)
			break
	logging.info("[%s]ssh backend recv thread exited." % uid)


####rewrite WSGIREQUESTHANDLER to add request uuid
from werkzeug.serving import WSGIRequestHandler, DechunkedInput
from werkzeug.urls import url_parse, url_unquote
from werkzeug._compat import PY2, WIN, reraise, wsgi_encoding_dance
import sys
class CustomRequestHandler(WSGIRequestHandler):

	def connection_dropped(self, error, environ=None):
		uid = environ.get('REQUEST_UUID', None)
		if uid and uid :
			a = connection_data.REQUEST_DICT.pop(uid, None)
			if a:
				del a
				print("interrupt %s" % uid)

	def make_environ(self):
		request_url = url_parse(self.path)

		def shutdown_server():
			self.server.shutdown_signal = True

		url_scheme = self.server.ssl_context is None and 'http' or 'https'
		path_info = url_unquote(request_url.path)

		environ = {
			'REQUEST_UUID': uuid.uuid4().hex,
			'wsgi.version': (1, 0),
			'wsgi.url_scheme': url_scheme,
			'wsgi.input': self.rfile,
			'wsgi.errors': sys.stderr,
			'wsgi.multithread': self.server.multithread,
			'wsgi.multiprocess': self.server.multiprocess,
			'wsgi.run_once': False,
			'werkzeug.server.shutdown': shutdown_server,
			'SERVER_SOFTWARE': self.server_version,
			'REQUEST_METHOD': self.command,
			'SCRIPT_NAME': '',
			'PATH_INFO': wsgi_encoding_dance(path_info),
			'QUERY_STRING': wsgi_encoding_dance(request_url.query),
			'REMOTE_ADDR': self.address_string(),
			'REMOTE_PORT': self.port_integer(),
			'SERVER_NAME': self.server.server_address[0],
			'SERVER_PORT': str(self.server.server_address[1]),
			'SERVER_PROTOCOL': self.request_version
		}

		for key, value in self.headers.items():
			key = key.upper().replace('-', '_')
			if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
				key = 'HTTP_' + key
			environ[key] = value

		if environ.get('HTTP_TRANSFER_ENCODING', '').strip().lower() == 'chunked':
			environ['wsgi.input_terminated'] = True
			environ['wsgi.input'] = DechunkedInput(environ['wsgi.input'])

		if request_url.scheme and request_url.netloc:
			environ['HTTP_HOST'] = request_url.netloc

		return environ

# @app.before_request
# def before_request():
# 	uid = uuid.uuid4().hex
# 	request.headers["SCRIPT-RUN-ID"] = uid


def main():
	start_ws_thread()
	#start_wsio_thread()
	app.run(host="0.0.0.0", threaded=True, port=5000, debug=False, request_handler=CustomRequestHandler)


if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		GLOBAL_EXITED_VAR = True
