import cgi
import os
from google.appengine.api import images, capabilities
import logging
from google.appengine.ext import blobstore
from base_handler import endpoint, get, post
from http_response_exception import HttpResponseException


@endpoint('/upload')
class UploadHandler:
	def __init__(self):
		self._uploads = None

	@get('/')
	def get_upload_url(self):
		self.response.headers.add_header("Content-Type", "application/json")
		try:
			return {
				'url': blobstore.create_upload_url('/upload')
			}
		except Exception:
			raise HttpResponseException("Error creating upload url")

	@post('/')
	def post_media(self):
		logging.info('upload post')
		try:
			upload_files = self.get_uploads()
			blob_info = upload_files[0]
			data = {
				'key': str(blob_info.key()),
				'nextUploadUrl': blobstore.create_upload_url('/upload')
			}

			if blob_info.content_type.split('/')[0] == 'image' and not os.environ['SERVER_SOFTWARE'].startswith('Dev'):
				if capabilities.CapabilitySet('images').is_enabled():
					imageUrl = images.get_serving_url(blob_info.key(), secure_url=True)
					if imageUrl:
						data['imageUrl'] = imageUrl

			self.response.headers['Content-Type'] = "application/json"
			return data
		except Exception, e:
			logging.info(e)
			raise HttpResponseException('Error uploading file')

	def get_uploads(self, field_name=None):
		"""Get uploads sent to this handler.

		Args:
			field_name: Only select uploads that were sent as a specific field.

		Returns:
			A list of BlobInfo records corresponding to each upload.
			Empty list if there are no blob-info records for field_name.
		"""
		if self._uploads is None:
			self._uploads = {}
			for key, value in self.request.params.items():
				if isinstance(value, cgi.FieldStorage):
					if 'blob-key' in value.type_options:
						self._uploads.setdefault(key, []).append(
							blobstore.parse_blob_info(value))

		if field_name:
			try:
				return list(self._uploads[field_name])
			except KeyError:
				return []
		else:
			results = []
			for uploads in self._uploads.itervalues():
				results += uploads
			return results
