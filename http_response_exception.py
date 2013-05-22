import json


class HttpResponseException(Exception):
	def __init__(self, message, code=400):
		super(HttpResponseException, self).__init__()
		self.message = message
		self.error_code = code

	def to_json(self):
		return {
			'error': {
				'message': self.message
#				'stacktrace':traceback.format_exc().splitlines()
			}
		}

	def write(self, response):
		response.set_status(self.error_code)
		response.headers['ErrorMessage'] = self.message
		response.out.write(json.dumps(self.to_json()))