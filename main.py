import webapp2
from include import handlers

app = webapp2.WSGIApplication()
for path in handlers:
	parts = path.split('.')
	cls = path.split('.')[-1]
	import_path = '.'.join(parts[0:-1])

	__import__(import_path, fromlist=cls)

from download import DownloadHandler
from upload import UploadHandler