import json
import datetime
from base.base_model import BaseModel
from base.utils import DateFormatter

class ModelEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, BaseModel):
			return obj.to_json()
		if isinstance(obj, datetime.datetime):
			return DateFormatter.datetime(obj)
		if isinstance(obj, datetime.date):
			return DateFormatter.date(obj)
		if isinstance(obj, datetime.time):
			return DateFormatter.time(obj)
		return json.JSONEncoder.default(self, obj)