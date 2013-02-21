from google.appengine.ext.blobstore import BlobKey
from datetime import date, datetime, time
from google.appengine.ext import ndb
from google.appengine.ext import db
import logging
import uuid
from google.appengine.ext.ndb import Key, Cursor
from base import utils
from base.constants import PASSWORD
from base.http_response_exception import HttpResponseException
from base.utils import DateParser

NDB_PRIMITIVE_TYPES = [ndb.IntegerProperty, ndb.FloatProperty, ndb.BooleanProperty, ndb.JsonProperty, ndb.BlobProperty]
SIMPLE_TYPES = (int, long, float, bool, dict, basestring, list)
NDB_KEY_TYPES = (ndb.BlobKeyProperty, ndb.KeyProperty, db.ReferenceProperty)
NDB_DATE_TYPES = (ndb.DateProperty, ndb.DateTimeProperty, ndb.TimeProperty)
NDB_STRING_TYPES = [ndb.StringProperty, ndb.TextProperty]
DATE_TYPES = (date, datetime, time)
DATE_TIME_FORMAT = '%Y-%m-%d-%H:%S'


class BaseModel(ndb.Model):
	created = ndb.DateTimeProperty(auto_now_add=True)
	updated = ndb.DateTimeProperty(auto_now=True)
	max_fetch = 500

	# TODO - should eager = True by default?
	def to_json(self, eager = False):
		ignore_keys = ['password','updated','created']
		data = {}
		if self.key:
			data = {"id": self.key.id()}

		for key, prop in self._properties.iteritems():
			if key in ignore_keys:
				continue

			if type(prop) in NDB_KEY_TYPES:
				model = getattr(self, key)
				if type(prop) == ndb.BlobKeyProperty:
					if model is None:
						data[key] = None
					else:
						data[key] = model.__str__()
				else: # is an NDB key
					if prop._repeated:
						if eager:
							data[key] = [m.get().to_json(eager) for m in model]
						else:
							data[key] = [m.id() for m in model]
					elif model:
						if eager:
							model = model.get()
							data[key] = model.to_json(eager)
						else:
							data[key] = model.id()
					else:
						data[key] = None

			elif type(prop) == ndb.StructuredProperty:
				model = getattr(self, key)
				if not model:
					data[key] = None
					continue

				if prop._repeated:
					list = []

					for each in model:
						if each:
							list.append(each.to_json())

					data[key] = list

				else:
					data[key] = model.to_json()

			elif type(prop) in NDB_DATE_TYPES:
				if type(getattr(self, key)) in DATE_TYPES:
					if type(prop) == ndb.DateProperty:
						data[key] = DateParser.date(getattr(self, key))

					elif type(prop) == ndb.TimeProperty:
						data[key] = DateParser.time(getattr(self, key))

					elif type(prop) == ndb.DateTimeProperty:
						data[key] = DateParser.datetime(getattr(self, key))

			elif type(prop) in NDB_STRING_TYPES + NDB_PRIMITIVE_TYPES:
				data[key] = getattr(self, key)

			else:
				raise ValueError('cannot to_json key: %s prop: %s ' % (key, repr(prop)))

		return data

	@classmethod
	def from_json(cls, json, model = None):
		if not json:
			return cls()

		if model is None:
			model = cls()

		if 'id' in json:
			model.key = ndb.Key(cls, json['id'])
		else:
			model.key = ndb.Key(cls, str(uuid.uuid4()))

		for key, prop in model._properties.iteritems():
			if key not in json.keys():
				continue

			if key == 'created' or key == 'updated':
				continue

			value = None

			if key == 'password':
				if len(json[key]) < 1:
					raise HttpResponseException(PASSWORD)
				value = utils.md5_hash(json[key])  # TODO - have the client hash the password before sending it up?

			elif  type(prop) in NDB_KEY_TYPES:
				if json[key] is None:
					if prop._repeated:
						value = []
					else:
						value = None
				elif type(prop) == ndb.BlobKeyProperty:
					if prop._repeated:
						value = [BlobKey(k) for k in json[key]]
					else:
						value = BlobKey(json[key])
				else:
					cls_kind = prop._kind
					if cls_kind is None:
						cls_kind = cls
					if prop._repeated:
						value = [ndb.Key(cls_kind, k) for k in json[key]]
					else:
						value = ndb.Key(cls_kind, json[key])

			elif type(prop) in NDB_STRING_TYPES:
				if not prop._repeated:
					value = json[key]
					#Should allow strings to be null
					#json[key] is None or
					if json[key] is not None and not isinstance(json[key], basestring):
						value = ''

				else:
					repeated_list = getattr(model, key)
					if not repeated_list:
						repeated_list = []

					if not isinstance(json[key], list):
						json[key] = [json[key]]

					for each in json[key]:
						if each not in repeated_list:
							repeated_list.append(each)

					value = repeated_list
					# the original code sorted this list before saving it
					#sorted(repeated_list, key=lambda list_item: list_item.lower())

			elif type(prop) in NDB_DATE_TYPES:
				if type(json[key]) in DATE_TYPES:
					value = json[key]
				elif type(json[key]) == basestring or type(json[key]) == unicode:
					if type(prop) == ndb.DateProperty:
						value = utils.DateParser.date(json[key])
					elif type(prop) == ndb.DateTimeProperty:
						value = utils.DateParser.datetime(json[key])
					elif type(prop) == ndb.TimeProperty:
						value == utils.DateParser.time(json[key])
					else:
						value = None
				else:
					value = None

			elif type(prop) == ndb.StructuredProperty:
				if prop._repeated:
					repeated_list = getattr(model, key)
					if not repeated_list:
						repeated_list = []

					if not isinstance(json[key], list):
						json[key] = [json[key]]

					repeated_objs = {}
					if repeated_list:
						for st_model in repeated_list:
							repeated_objs[st_model.id] = st_model.to_dict()

					for each in json[key]:
						if not each:
							continue

						kes = each.keys()
						if 'id' not in kes:
							each['id'] = str(uuid.uuid4())
							st_model = prop._modelclass().from_json(each)
							repeated_objs[st_model.id] = st_model

						else:
							if each['id'] in repeated_objs:
								del repeated_objs[each['id']]

							st_model = prop._modelclass().from_json(each)
							repeated_objs[st_model.id] = st_model

						if st_model not in repeated_list:
							repeated_list.append(st_model)

					value = repeated_objs.values()

				else:
					value = prop._modelclass().from_json(json[key])

			elif type(json[key]) in SIMPLE_TYPES or type(prop) in NDB_PRIMITIVE_TYPES:
				if prop._repeated:
					if type(prop) == ndb.IntegerProperty:
						value = [int(item) for item in json[key]]
					elif type(prop) == ndb.FloatProperty:
						value = [float(item) for item in json[key]]
					elif type(prop) == ndb.BooleanProperty:
						value = [bool(item) for item in json[key]]
					else:
						value = json[key]
				else:
					if json[key] is None:
						value = None
					elif type(prop) == ndb.IntegerProperty:
						value = int(json[key])

					elif type(prop) == ndb.FloatProperty:
						value = float(json[key])

					elif type(prop) == ndb.BooleanProperty:
						value = bool(json[key])

					else:
						value = json[key]

			else:
				logging.info('invalid json key:' % key)

			setattr(model, key, value)

		return model

	def update_from_json(self, json):
		self.from_json(json, self)

	@classmethod
	def id_exists(cls, id, namespace = None):
		key = Key(cls._get_kind(), id, namespace=namespace)
		return key.get() is not None

	@classmethod
	def prop_exists(cls, prop, val, namespace = None):
		return not not cls.query(prop == val, namespace=namespace).fetch(1)

	@classmethod
	def get_single(cls, *args, **kwargs):
		results = cls.query(*args, **kwargs).fetch()
		if len(results) == 0:
			return None
		return results[0]

	@classmethod
	def get_page(cls, query=None, cursor=None, sort=None, amount=50):
		c = None
		if cursor:
			c = Cursor.from_websafe_string(cursor)
		if not query:
			query = cls.query()

		if sort:
			query = query.order(cls.generate_order_from_string(sort))

		data, next_cursor, more = query.fetch_page(amount, start_cursor=c)
		data = {
			cls._get_kind():data
		}
		if more:
			data['cursor'] = next_cursor.to_websafe_string()
		return data

	@classmethod
	def generate_order_from_string(cls, order_str):
		if not len(order_str):
			return None

		reverse = False
		order = None

		if order_str[0] == '-':
			reverse = True
			order_str = order_str[1:]
		for name, prop_type in cls._properties.iteritems():
			if prop_type._name == order_str:
				order = getattr(cls, name)

		if order is None:
			raise HttpResponseException("{0} not found on model {1}".format(order_str, cls._get_kind()))

		if reverse:
			return -order
		return order


class Crud:
	@staticmethod
	def create(model, data, unique_props=()):
		if isinstance(data, dict):
			if 'id' not in data:
				data['id'] = str(uuid.uuid4())
			if model.id_exists(data['id']):
				raise HttpResponseException('Entity with id `{0}` already exists'.format(data['id']))
			for unique_prop in unique_props:
				if model.prop_exists(unique_prop, data[unique_prop._name]):
					raise HttpResponseException('Entity already exists with {0} `{1}`'.format(unique_prop._name, data[unique_prop._name]))
			m = model.from_json(data)
			return m
		else:
			invalid_ids = []
			invalid_props = []
			for item in data:
				if model.id_exists(item['id']):
					invalid_ids.append(item['id'])
				for unique_prop in unique_props:
					if model.prop_exists(unique_prop, data[unique_prop._name]):
						invalid_props.append((unique_prop._name, data[unique_prop._name]))
			if len(invalid_ids):
				raise HttpResponseException(['Entity with id `{0}` already exists'.format(item['id']) for item in invalid_ids])
			if len(invalid_props):
				raise HttpResponseException(['Entity already exists with {0} `{1}`'.format(item[0], item[1]) for item in invalid_props])
			models = [model.from_json(m) for m in data]
			return models

	@staticmethod
	def update(model, data):
		if isinstance(data, dict):
			if 'id' not in data:
				raise HttpResponseException('POST requires id for each model received')
			item = model.get_by_id(data['id'])
			if item is None:
				raise HttpResponseException('Entity with id {0} doesn\'t exist'.format(data['id']))
			item.update_from_json(data)
			return item
		else:
			invalid_items = []
			valid_items = []
			for item in data:
				if 'id' not in item:
					raise HttpResponseException('POST requires id for each model received')

				m = model.get_by_id(item['id'])
				if m is None:
					invalid_items.append(item['id'])
				else:
					valid_items.append(m.update_from_json(item))
			if len(invalid_items):
				raise HttpResponseException(['Entity with id {0} already exists'.format(item['id']) for item in invalid_items])

			return valid_items

	@staticmethod
	def delete(model, ids_arr):
		if isinstance(ids_arr, (str,unicode)):
			item = model.get_by_id(ids_arr)
			if item is None:
				raise HttpResponseException("Entity with id {0} doesn't exist".format(ids_arr))
			return item
		else:
			invalid_ids = []
			valid_items = []
			for id in ids_arr:
				item = model.get_by_id(id)
				if item is None:
					invalid_ids.append(id)
				else:
					valid_items.append(item)
			if len(invalid_ids):
				raise HttpResponseException(['Entity with id {0} not found'.format(id) for id in invalid_ids])

			return valid_items