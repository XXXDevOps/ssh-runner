from flask_restful import Resource
from flask import request
import connectors
import connection_data


class RemoteScript(Resource):

	def get(self):
		return {'hello': 'world'}

	def post(self):
		json_data = request.get_json()
		c = connectors.ConnecterScriptRunner(**json_data)
		uid = request.environ['REQUEST_UUID']
		connection_data.REQUEST_DICT[uid] = c
		out, err = c.run()
		return {
				'stdout': out,
				'stderr': err,
				'time': c.run_time
		}