import urllib
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from base.base_handler import endpoint, get

@endpoint('/download', inherit_from=blobstore_handlers.BlobstoreDownloadHandler)
class DownloadHandler:
	@get('/<key>')
	def get_resource(self, key):
		resource = str(urllib.unquote(key))
		blob_info = None
		try:
			blob_info = blobstore.BlobInfo.get(resource)
		except Exception:
			raise Exception("Invalid blob key")

		if blob_info is None:
			raise Exception("Blob key not found")

		try:
			self.send_blob(blob_info)
		except Exception:
			raise Exception("Error downloading resource")