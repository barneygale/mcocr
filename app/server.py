import StringIO
import asyncore
import socket
import urlparse
import re
import settings as settings_herp
import os
import mimetypes
import time
import traceback
import docs
import http
mimetypes.init()

response_reasons = {
	200: 'OK',
	304: 'Not Modified',
	404: 'Not Found',
	500: 'Internal Server Error',
	501: 'Not Implemented'}


handlers = {}
for name in dir(docs):
	if name.endswith('Doc'):
		handlers[re.compile(getattr(docs, name).expression)] = getattr(docs, name)

class Server:
	def __init__(self):
		#Settings handler
		self.settings = settings_herp.Settings()
		try:
			self.settings.load()
		except:
			self.settings.create()
		

	def serve_forever(self):
		self.client_dispatcher = self.ConnectionDispatcher(self.settings)
		asyncore.loop(use_poll = False)

	#######
	#######
	
	#Dispatches incoming connections to a new handler.
	class ConnectionDispatcher(asyncore.dispatcher):
		id = 0
		current_id = 1
		def __init__(self, settings):
			asyncore.dispatcher.__init__(self)
			self.settings = settings
			self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
			self.set_reuse_addr()
			self.bind((settings['server_host'], settings['server_port']))
			self.listen(settings['server_limit'])

		def handle_accept(self):
			pair = self.accept()
			if pair is None:
				pass
			else:
				sock, addr = pair
				handler = Server.ConnectionHandler(sock)
				handler.settings = self.settings
				handler.id = self.current_id
				self.current_id += 1

	class ConnectionHandler(asyncore.dispatcher):
		rbuff = ""
		wbuff = ""

		def handle_read(self):
			self.rbuff += self.recv(self.settings['server_buffersize'])
			try:
				request = http.HTTPRequest()
				request.decode(self.rbuff)
				self.rbuff = ""
				for i in handlers.iteritems():
					m = i[0].match(request._data['path_path'])
					if m:
						i[1].handle_request(self, request, m.groupdict())
						return
			
				#Error state: no handlers recognise the URL!
				err = http.HTTPResponse(responsecode=501)
				print err.encode()
				self.do_write(err.encode())
			except http.BufferUnderflowException:
				print "Waiting for more data..."
		
		def do_write(self, data):
			self.wbuff += data
		def handle_write(self):
			if self.wbuff:
				sent = self.send(self.wbuff)
				print "Wrote %d bytes" % sent
				self.wbuff = self.wbuff[sent:]
				if len(self.wbuff) == 0:
					self.close()

		def writable(self):
			return len(self.wbuff) > 0

		def handle_error(self):
			err = http.HTTPResponse(responsecode=500, response=traceback.format_exc())
			self.do_write(err.encode())
