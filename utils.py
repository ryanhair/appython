import hashlib
import datetime


def md5_hash(password):
	return str(hashlib.md5(password).hexdigest())


class DateParser:
	@staticmethod
	def date(date_str):
		if isinstance(date_str, datetime.date):
			return date_str
		try:
			pieces = date_str.split('-')
			year = int(pieces[0])
			month = int(pieces[1])
			day = int(pieces[2])
			return datetime.date(year, month, day)
		except Exception:
			raise Exception('Error parsing date string "{0}", required format is "yyyy-mm-dd"'.format(date_str))

	@staticmethod
	def time(time_str):
		if isinstance(time_str, datetime.time):
			return time_str
		try:
			pieces = time_str.split(':')
			hours = int(pieces[0])
			minutes = int(pieces[1])
			seconds = int(pieces[2])
			return datetime.time(hours, minutes, seconds)
		except Exception:
			raise Exception('Error parsing time string "{0}", required format is "hh:mm:ss"'.format(time_str))

	@staticmethod
	def datetime(datetime_str):
		if isinstance(datetime_str, datetime.datetime):
			return datetime_str
		try:
			pieces = datetime_str.split(' ')
			date = DateParser.date(pieces[0])
			time = DateParser.time(pieces[1])
			return datetime.datetime.combine(date, time)
		except Exception:
			raise Exception(
				'Error parsing datetime string "{0}", required format is "yyyy-mm-dd hh:mm:ss"'.format(datetime_str))


class DateFormatter:
	date_format = '%Y-%m-%d'
	time_format = '%H:%M:%S'

	@staticmethod
	def date(date):
		if not isinstance(date, datetime.date):
			raise Exception("Not a date")
		return date.strftime(DateFormatter.date_format)

	@staticmethod
	def time(time):
		if not isinstance(time, datetime.time):
			raise Exception("Not a time")
		return time.strftime(DateFormatter.time_format)

	@staticmethod
	def datetime(dt):
		if not isinstance(dt, datetime.datetime):
			raise Exception("Not a datetime")
		return dt.strftime("{0} {1}".format(DateFormatter.date_format, DateFormatter.time_format))