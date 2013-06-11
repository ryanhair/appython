from base_handler import endpoint, get


@endpoint('/api')
class RestHandler:
	@get('/.*')
	def get_entities(self):
		print self.request.path