import urllib
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from base_handler import endpoint, get
from http_response_exception import HttpResponseException


@endpoint('/download', inherit_from=blobstore_handlers.BlobstoreDownloadHandler)
class DownloadHandler:
	@get('/<key>')
	def get_resource(self, key):
		resource = str(urllib.unquote(key))
		try:
			blob_info = blobstore.BlobInfo.get(resource)
		except Exception:
			raise HttpResponseException("Invalid blob key")

		if blob_info is None:
			raise HttpResponseException("Blob key not found")

		try:
			self.send_blob(blob_info)
		except Exception:
			raise HttpResponseException("Error downloading resource")