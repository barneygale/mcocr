import time
import StringIO
import multiprocessing
import urlparse
import os
import mimetypes
mimetypes.init()

class BufferUnderflowException(Exception):
	pass

def http_date(*args):
	return time.strftime('%a, %d %b %Y %H:%M:%S %Z', time.gmtime(args[0] if args else None))

class BoundBuffer:
	def __init__(self, *args):
		self.buff = StringIO.StringIO((args[0] if args else ''))
	
	def read(self, bytes):
		if len(self.buff) < bytes:
			raise BufferUnderflowException()
		o, self.buff = self.buff[:bytes], self.buff[bytes:]
		return o

	def readline(self):
		o = self.buff.readline()
		if o[-2:] == '\r\n':
			return o[:-2]
		else:
			raise BufferUnderflowException()

class HTTPTraffic:
	_data = {
		'version': 1.1
	}
	def __init__(self, **kargs):
		self.set_defaults()
		self._data.update(kargs)
	def set_defaults(self):
		pass

class HTTPRequest(HTTPTraffic):
	def set_defaults(self):
		self._data.update({
			'method': 'GET',
			'path_path': '/',
			'path_query': '',
			'path_fragment': ''
		})
	def decode(self, text):
		buff = BoundBuffer(text)
		data = {}
			
		#First line: method, path, version
		line = buff.readline()
		data['method'], path, data['version'] = line.split(" ")
		path = urlparse.urlsplit(path)
		data['path_path'] = path.path.strip('/')
		data['path_fragment'] = path.fragment
		for a, b in urlparse.parse_qsl(path.query.lstrip("?")):
			data['path_query_'+a] = b
	
		#Read the headers
		while True:
			line = buff.readline()
			if line == "":
				break
			line = line.split(": ", 1)
			data['header_'+line[0]] = line[1]
	
		#Post data
		if data['method'].lower() == 'post' and 'Content-Length' in data['headers']:
			tmp = buff.read(int(data['headers']['Content-Length']))
			for a, b in urlparse.parse_qsl(tmp):
				data['postdata_'+a] = b
	
		self._data = data
	
	def encode(self):
		data = self._data
		
		#First line: method, path, version
		query = urllib.urlencode(data['path_query'])
		if query: query = "?" + query
		path = "%s%s%s" % (data['path_path'], query, data['path_fragment'])
		o = "%s %s %s\r\n" % (data['method'], path, data['version'])
		
		for k, v in data.iteritems():
			if k.startswith('header_'):
				o += "%s: %s\r\n" % (k[len('header_'):], v)
		o += "\r\n"

		if data['method'].lower() == "post":
			postdata = {}
			for k, v in data.iteritems():
				if k.startswith('postdata_'):
					postdata[k[len('postdata_'):]] = v
			o += urllib.urlencode(postdata)
		
		return o

class HTTPResponse(HTTPTraffic):
	_response_strings = {
		200: 'OK',
		304: 'Not Modified',
		404: 'Not Found',
		500: 'Internal Server Error',
		501: 'Not Implemented'
	}
	
	def set_defaults(self):
		self._data.update({
			'responsecode': 200,
			'response': '',
			'header_Content-type': 'text/plain',
			'header_Server': 'barneybot3000',
			'header_Date': http_date(),
		})

	def decode(self, text):
		buff = BoundBuffer(text)
		data = {'headers': {}}
	
		#First line: version, response code. response string ignored.
		data['version'], data['responsecode'] = buff.readline().split(" ", 2)[:2]
		data['version'] = float(data['version'])
		data['responsecode'] = int(data['responsecode'])

		#Read the headers
		while True:
			line = buff.readline()
			if line == "":
				break
			line = line.split(": ", 1)
			data['header_'+line[0]] = line[1]
	
		#Read the body
		if 'header_Content-Length' in data:
			data['response'] = buff.read(int(data['header_Content-Length']))
		elif 'header_Transfer-Encoding' in data and data['header_Transfer-Encoding'] == 'chunked':
			data['chunks'] = []
			while True:
				l = int(buff.readline(), 16)
				if l == 0:
					break
				data['chunks'].append(buff.read(l))
				buff.read(2)
			data['response'] = ''.join(chunks)
		self._data = data

	def encode(self):
		data = self._data
		o = "HTTP/%s %s %s\r\n" % (data['version'], data['responsecode'], self._response_strings[data['responsecode']])
		
		if data['response'] == '' and data['responsecode']/100 in (5,4):
			data['response'] =  '%s: %s' % (data['responsecode'], self._response_strings[data['responsecode']])
			data['header_Content-type'] = 'text/plain'
		
		if 'response' in data:
			data['header_Content-Length'] = len(data['response'])
		
		data['header_Date'] = http_date()
		for k, v in data.iteritems():
			if k.startswith('header_'):
				o += "%s: %s\r\n" % (k[len('header_'):], v)
		o += "\r\n"
		
		if 'response' in data:
			o += data['response']
		
		return o

class FileResponse(HTTPResponse):
	def __init__(self, path, *args):
		self.set_defaults()
		if not os.path.isfile(path):
			self._data['responsecode'] = 404
			return
		mtime = http_date(os.path.getmtime(path))
		if args and args[0] == mtime:
			self._data['responsecode'] = 304
			return
	
		fd = open(path, 'rb')
		
		self._data['header_Content-type'] = mimetypes.types_map['.'+path.split('.')[-1]]
		self._data['header_Last-Modified'] = mtime
		self._data['response'] = fd.read()
		
		fd.close()

class LongrunningResponse(HTTPResponse):
	def set_defaults(self):
		self._data.update({
			'header_Transfer-Encoding': 'chunked',
			'chunks': multiprocessing.Queue()
		})
	def encode_header(self):
		data = self._data
		
		o = "%s %s %s\r\n" % (data['version'], data['responsecode'], self._response_strings[data['responsecode']])	

		for k, v in data.iteritems():
			if k.startswith('header_'):
				o += "%s: %s\r\n" % (k[len('header_'):], v)
		o += "\r\n"

	def encode_chunks(self):
		try:
			while True:
				chunk = self._data['chunks'].get_nowait()
				yield "%x\r\n%s\r\n" % (len(chunk), chunk)
		except Queue.Empty:
			pass

	def add_chunk(self, text):
		self._data['chunks'].put(text)
