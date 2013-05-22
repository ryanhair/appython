import os
import unittest
from google.appengine.api import files
from google.appengine.api.blobstore import file_blob_storage, blobstore_stub
from google.appengine.api.files import file_service_stub
from google.appengine.api.search.simple_search_stub import SearchServiceStub
from google.appengine.ext import testbed
from webtest import TestApp
from ..main import app


class BaseTestbed(testbed.Testbed):
	blobstore_stub = None

	def init_blobstore_stub(self, enabled=True):
		blob_storage = file_blob_storage.FileBlobStorage('/tmp/testbed.blobstore',
			testbed.DEFAULT_APP_ID)
		blob_stub = blobstore_stub.BlobstoreServiceStub(blob_storage)
		file_stub = file_service_stub.FileServiceStub(blob_storage)
		self._register_stub('blobstore', blob_stub)
		self._register_stub('file', file_stub)
		self._register_stub('search', SearchServiceStub())


class BaseTest(unittest.TestCase):

	project = ''
	version = ''
	testbed = None

	def setUp(self, *args, **kwargs):
		self.show_browser = 'showbrowser' in os.environ and os.environ['showbrowser'] == 'True'
		self.app.reset()

	@classmethod
	def setUpClass(cls):
		cls.app = TestApp(app)

		cls.testbed = BaseTestbed()
		cls.testbed.activate()
		cls.testbed.init_all_stubs()

		cls.testbed.setup_env(
			USER_EMAIL='test@example.com',
			USER_ID='123',
			USER_IS_ADMIN='1',
			overwrite=True
		)

	@classmethod
	def tearDownClass(cls):
		cls.testbed.deactivate()

	#response = self.app.get(url, input, headers)
	#response = self.app.post(url, input, headers)
	#response = self.app.get(url, input, headers, expect_errors='error' in output)
	#response = self.app.put_json(url, params=input, headers=headers, expect_errors='error' in output)
	#response = self.app.post_json(url, params=input, headers=headers, expect_errors='error' in output)
	#response = self.app.delete_json(url, headers=headers, expect_errors='error' in output)

	def create_blob(self, contents, mime_type):
		#Since uploading blobs doesn't work in testing, create them this way.
		fn = files.blobstore.create(mime_type=mime_type,
			_blobinfo_uploaded_filename="foo.blt")
		with files.open(fn, 'a') as f:
			f.write(contents)
		files.finalize(fn)
		return files.blobstore.get_blob_key(fn)

	def get_blob(self, key):
		return self.testbed.blobstore_stub.storage.OpenBlob(key).read()