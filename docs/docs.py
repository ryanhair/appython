import json
import os
import webapp2


class DocHandler(webapp2.RequestHandler):
	def get(self):
		dataPath = os.path.join(os.path.dirname(__file__), 'docs.json')

		if not os.path.exists(dataPath):
			self.response.out.write("File not found")
			return

		data = open(dataPath).read()

		jsonp_callback = self.request.get('callback')

		self.response.headers['Content-Type'] = 'application/json'
		self.response.out.write('{0}({1})'.format(jsonp_callback, json.dumps(data)))


app = webapp2.WSGIApplication([
	('/admin/docs', DocHandler)
], debug=True)

if __name__ == '__main__':
	import json
	from google.appengine.ext.ndb import Property
	from base_model import BaseModel
	from include import handlers

	def get_subclasses(cls):
		subclasses = []

		for cls in cls.__subclasses__():
			if len(cls.__subclasses__()) > 0:
				subclasses.extend(get_subclasses(cls))
			else:
				subclasses.append(cls)

		return subclasses

	for path in handlers:
		parts = path.split('.')
		cls = path.split('.')[-1]
		import_path = '.'.join(parts[0:-1])

		__import__(import_path, fromlist=cls)

	# noinspection PyUnresolvedReferences
	from ..download import DownloadHandler
	# noinspection PyUnresolvedReferences
	from ..upload import UploadHandler

	models = {}
	for subclass in get_subclasses(BaseModel):
		subclass_dict = models[subclass.__name__] = {}

		#	handlers = getattr(subclass, '_handlers')
		#	print handlers

		for name, prop in vars(subclass).items():
			if isinstance(prop, Property):
				subclass_dict[name] = {
					"type": prop.__class__.__name__[:-8],
					"required": prop._required,
					"indexed": prop._indexed,
					"repeated": prop._repeated,
					"default": prop._default,
					"choices": prop._choices
				}

	# noinspection Restricted_Python_calls
	f = open('docs.json', 'w')
	f.write(json.dumps({
		'project': 'visionhubweb',
		'version': '0.0.0.1',
		'models': models
	}, indent=4))
	f.flush()
	f.close()