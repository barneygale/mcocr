import os
import http

class IndexDoc:
	expression = '^$'
	@classmethod
	def handle_request(self, handler, request, tokens):
		request._data['path_path'] = 'static/index.html'
		StaticDoc.handle_request(handler, request, {'filename': 'index.html'})
		
class ImageDoc:
	expression = '^image/(?P<filename>.*)$'
	@classmethod
	def handle_request(self, handler, request, tokens):
		path = os.path.join(handler.settings['screenshotspath'], tokens['filename'])
		if 'header_If-Modified-Since' in request._data:
			response = http.FileResponse(path, request._data['header_If-Modified-Since'])
		else:
			response = http.FileResponse(path)
		handler.do_write(response.encode())
		
class StaticDoc:
	expression = '^static/(?P<filename>.*)$'
	@classmethod
	def handle_request(self, handler, request, tokens):
		path = os.path.join(handler.settings['basedir'], 'static', tokens['filename'])
		if 'header_If-Modified-Since' in request._data:
			response = http.FileResponse(path, request._data['header_If-Modified-Since'])
		else:
			response = http.FileResponse(path)
		handler.do_write(response.encode())

class AJAXDoc:
	expression = '^ajax$'

class UpdatesDoc:
	expression = '^updates'
