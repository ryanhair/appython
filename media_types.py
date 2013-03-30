import json
import os
from google.appengine.ext.webapp import template
from base.base_model import BaseModel
from base.json_model_encoder import ModelEncoder

class MediaType:
	@staticmethod
	def json(data):
		return json.dumps(data, cls=ModelEncoder)

	@staticmethod
	def html(info):
		path = os.path.join(os.path.dirname(__file__), '../templates/{0}'.format(info['template']))
		data = None
		if 'data' in info:
			data = info['data']
		return template.render(path, data)

	mappings = {
		'json':'application/json',
		'html':'text/html'
	}