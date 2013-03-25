import inspect
import json
import logging
import traceback
import sys
import webapp2
from base.base_model import Crud, BaseModel
from base.http_response_exception import HttpResponseException
from google.appengine.api import users
from base.media_types import MediaType

def gen_handler_class(sub, inherit_from=webapp2.RequestHandler):
	class BaseHandler(inherit_from, sub):
		def __init__(self, *args, **kwargs):
			if hasattr(inherit_from, '__init__'):
				inherit_from.__init__(self, *args, **kwargs)
			if hasattr(sub, '__init__'):
				sub.__init__(self, *args, **kwargs)
			self.handlers = []
			for name in dir(self):
				possible_method = getattr(self, name)
				if hasattr(possible_method, 'handler_path'):
					self.handlers.append(possible_method)

			def _sort(handler):
				count = len(handler.required_arg_keys)
				if not hasattr(handler, 'admin_required'):
					count += 10000
				return count
			self.handlers.sort(key=_sort, reverse=True)

		def dispatch(self):

			if self.request.method in ('PUT', 'POST'):
				self.data = {}
				if self.request.body != '' and self.request.content_type == 'application/json':
					self.data = json.loads(self.request.body)
			elif self.request.method == 'DELETE':
				self.data = self.request.get('id')
				if len(self.data) == 1:
					self.data = self.data[0]

			super(BaseHandler, self).dispatch()

		def handle_exception(self, exception, debug):
			logging.exception(exception)

			self.response.headers['ErrorMessage'] = exception.message
			if isinstance(exception, HttpResponseException):
				self.response.set_status(exception.error_code)
				self.write({
				'error': {
				'message':exception.message
				}
				}, raise_exception=True)
			else:
				self.response.set_status(500)
				self.write({
				'error': {
				'message':exception.message,
				'stacktrace':traceback.format_exc().splitlines()
				}
				}, raise_exception=True)

		def write(self, data, handler=None, raise_exception=False):
			data_type = self.request.headers.get('type')
			if data_type is None:
				if handler and hasattr(handler, 'default_content_type'):
					data_type = handler.default_content_type
				else:
					data_type = 'json'

			if not hasattr(MediaType, data_type):
				if raise_exception:
					raise HttpResponseException("Content type `{0}` not supported".format(data_type))
				else: data_type = 'json'

			if hasattr(handler, 'default_content_type') and data_type != handler.default_content_type\
			or hasattr(handler, 'extra__content_types') and data_type not in handler.extra_content_types:
				raise HttpResponseException("Content type `{0}` not allowed".format(data_type))

			self.response.out.write(getattr(MediaType, data_type)(data))

		def handle_request_filters(self, handler):
			if hasattr(self, 'admin_required') or hasattr(handler, 'admin_required'):
				user = users.get_current_user()
				if not users.is_current_user_admin():
					raise HttpResponseException('Requires admin priveleges', 403)

			if hasattr(self, 'request_filters'):
				for filter in self.request_filters:
					filter(self.request)
			if hasattr(handler, 'request_filters'):
				for filter in handler.request_filters:
					filter(self.request)

		def handle_response_filters(self, handler):
			if hasattr(self, 'response_filters'):
				for filter in self.response_filters:
					filter(self.response)
			if hasattr(handler, 'response_filters'):
				for filter in handler.response_filters:
					filter(self.response)

		def get(self, extra=None):
			handler_data = self.find_handler('get')
			self.handle_request_filters(handler_data.handler)

			needed_args = {}
			for key, val in handler_data.kwargs.iteritems():
				if key in handler_data.handler.required_arg_keys or key in handler_data.handler.optional_arg_keys:
					needed_args[key] = val
			result = handler_data.handler(**needed_args)

			self.handle_response_filters(handler_data)
			self.write(result, handler=handler_data.handler)

		def post(self, extra=None):
			handler_data = self.find_handler('post')
			self.handle_request_filters(handler_data.handler)
			args = []

			if hasattr(handler_data.handler, 'expected_type'):
				if isinstance(self.data, (list, tuple)) and not handler_data.handler.expected_type_allow_multiple:
					raise HttpResponseException("Cannot accept multiple items")

				unique_props = ()
				if handler_data.handler.expected_type_unique_props:
					unique_props = handler_data.handler.expected_type_unique_props
				data = Crud.create(handler_data.handler.expected_type, self.data, unique_props)
				args.insert(0, data)

			for k, v in handler_data.kwargs.iteritems():
				if k is None:
					del handler_data.kwargs[None]
					break

			needed_args = {}
			for key, val in handler_data.kwargs.iteritems():
				if key in handler_data.handler.required_arg_keys:
					needed_args[key] = val
			result = handler_data.handler(*args, **needed_args)

			self.handle_response_filters(handler_data)
			self.write(result)

		def put(self, extra=None):
			handler_data = self.find_handler('put')
			self.handle_request_filters(handler_data.handler)
			args = []

			if hasattr(handler_data.handler, 'expected_type'):
				if isinstance(self.data, (list, tuple)) and not handler_data.handler.expected_type_allow_multiple:
					raise HttpResponseException("Cannot accept multiple items")

				data = Crud.update(handler_data.handler.expected_type, self.data)
				args.insert(0, data)

			for k, v in handler_data.kwargs.iteritems():
				if k is None:
					del handler_data.kwargs[None]
					break

			needed_args = {}
			for key, val in handler_data.kwargs.iteritems():
				if key in handler_data.handler.required_arg_keys:
					needed_args[key] = val
			result = handler_data.handler(*args, **needed_args)

			self.handle_response_filters(handler_data)
			self.write(result)

		def delete(self, extra=None):
			handler_data = self.find_handler('delete')
			self.handle_request_filters(handler_data.handler)
			args = []

			if hasattr(handler_data.handler, 'expected_type'):
				if isinstance(self.data, (list, tuple)) and not handler_data.handler.expected_type_allow_multiple:
					raise HttpResponseException("Cannot accept multiple ids")

				data = Crud.delete(handler_data.handler.expected_type, self.data)
				if hasattr(handler_data.handler, 'expected_type_keys_only') and handler_data.handler.expected_type_keys_only:
					if isinstance(data, BaseModel):
						data = data.key
					else:
						data = [item.key for item in data]
				args.insert(0, data)

			needed_args = {}
			for key, val in handler_data.kwargs.iteritems():
				if key in handler_data.handler.required_arg_keys:
					needed_args[key] = val
			result = handler_data.handler(*args, **needed_args)

			self.handle_response_filters(handler_data)
			self.write(result)

		def find_handler(self, type):
			#process: looking for the best match
			#all params passed should be matched if possible
			#params will be url params, then form params, then json params
			#closest match is defined by the handler that first fits all required params (and highest amount), and then fits the most optional params.

			path = self.request.path.strip('/')
			path = path[len(self.base_path):]

			handler = None
			args = {}

			passed_in_params = {}
			for key, value in self.request.params.items():
				if key in passed_in_params:
					if not isinstance(passed_in_params[key], list):
						passed_in_params[key] = [passed_in_params[key]]
					passed_in_params[key].append(value)
				elif value != '':
					passed_in_params[key] = value
				else:
					passed_in_params[key] = None

			if hasattr(self, 'data') and isinstance(self.data, dict):
				for key, value in self.data.iteritems():
					if key in passed_in_params:
						if not isinstance(passed_in_params[key], list):
							passed_in_params[key] = [passed_in_params[key]]
						passed_in_params[key].append(value)
					else:
						passed_in_params[key] = value

			handler_required_args_received_len = 0
			for possible_handler in self.handlers:
				if type in possible_handler.handler_types:
					sub_path = possible_handler.handler_path
					match = sub_path.match(path)

					if match is not None:
						#potential handler, check required and optional params to see if match
						required_args_received = match.groupdict()
						all_args_received = dict(required_args_received.items() + passed_in_params.items())
						if any(key not in possible_handler.required_arg_keys for key in required_args_received.keys()):
							#url provides required args that aren't found in the method signature
							continue

						required_arg_keys = possible_handler.required_arg_keys
						if hasattr(possible_handler, 'expected_type'):
							required_arg_keys = required_arg_keys[1:]
						if any(arg not in all_args_received.keys() for arg in required_arg_keys):
							#method signature contains required argument that isn't found in the supplied args
							continue

						if not handler \
							or len(handler.required_arg_keys) - handler_required_args_received_len < len(possible_handler.required_arg_keys) - len(required_args_received) \
							or (len(handler.required_arg_keys) - handler_required_args_received_len == len(possible_handler.required_arg_keys) - len(required_args_received)
								and len(handler.optional_arg_keys) < len(possible_handler.optional_arg_keys)):
							args = all_args_received
							handler_required_args_received_len = len(required_args_received)
							handler = possible_handler

			if not handler:
				raise HttpResponseException("No handler found, or the method {0} is not allowed for this resource.".format(type.upper()), 405)

			return HandlerInfo(
				handler=handler,
				kwargs=args
			)

	return BaseHandler

class HandlerInfo:
	def __init__(self, handler, kwargs):
		self.handler = handler
		self.kwargs = kwargs

def endpoint(path=None, methods=('GET','PUT','POST','DELETE'), inherit_from=webapp2.RequestHandler):
	def _endpoint(sub_handler):
		setattr(sub_handler, 'base_path', path)

		route = webapp2.Route(path + '<extra:.*>', gen_handler_class(sub_handler, inherit_from=inherit_from), methods=methods)

		from base.main import app

		app.router.add(route)
		return sub_handler
	return _endpoint

def expects(model, multiple=True, keys_only=False, unique_props=()):
	def _expects(fn):
		fn.expected_type = model
		fn.expected_type_allow_multiple = multiple
		fn.expected_type_keys_only = keys_only
		fn.expected_type_unique_props = unique_props
		return fn
	return _expects

def get(path):
	return mark_method_as_subhandler('get', path)

def put(path):
	return mark_method_as_subhandler('put', path)

def post(path):
	return mark_method_as_subhandler('post', path)

def delete(path):
	return mark_method_as_subhandler('delete', path)

def mark_method_as_subhandler(type, path):
	def _mark(fn):
		mark(type, path, fn)
		return fn

	if hasattr(path, '__call__'):
		mark(type, '/', path)
		return path
	else:
		return _mark

def mark(type, path, fn):
	path = path.strip('/')
	fn.handler_path_str = path
	url_rgx, reverse_template, args_count, kwargs_count, variables = webapp2._parse_route_template(path, default_sufix='[^/]+')

	fn.handler_path = url_rgx
	if not hasattr(fn, 'handler_types'):
		fn.handler_types = []
	fn.handler_types.append(type)

	argspec = inspect.getargspec(fn)
	defaults = argspec.defaults
	if defaults is None:
		defaults = []

	fn.required_arg_keys = argspec.args[1:len(argspec.args) - len(defaults)]
	fn.optional_arg_keys = argspec.args[-len(defaults):]

def request_filter(filter_fn):
	def _request_filter(fn):
		if not hasattr(fn, 'request_filters'):
			fn.request_filters = []
		fn.request_filters.append(filter_fn)
		return fn
	return _request_filter

def response_filter(filter_fn):
	def _response_filter(fn):
		if not hasattr(fn, 'response_filters'):
			fn.response_filters = []
		fn.response_filters.append(filter_fn)
		return fn
	return _response_filter

def admin(fn):
	fn.admin_required = True
	return fn

def produces(default_content_type, *args):
	def _produces(fn):
		fn.default_content_type = default_content_type
		if args:
			fn.extra_content_types = args
		return fn
	return _produces
