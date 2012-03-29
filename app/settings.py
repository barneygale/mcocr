import os
import pickle
import sys

class Settings:
	_properties = {}
	_filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'settings.pickle')
	def __getitem__(self, name):
		return self._properties[name]
	def __setitem__(self, name, value):
		self._properties[name] = value
	def save(self):
		fd = open(self._filename, 'wb')
		pickle.dump(self._properties, fd)
		fd.close()
	def load(self):
		fd = open(self._filename, 'rb')
		self._properties = pickle.load(fd)
		fd.close()
	def create(self):
		self._properties = {
			'server_host':        '',
			'server_port':        8900,
			'server_limit':       100,
			'server_buffersize':  4096
		}
		if sys.platform == 'win32':
			mpath = os.environ['APPDATA']
		else:
			mpath = os.path.expanduser("~")
		
		self._properties['minecraftpath'] = os.path.join(mpath, '.minecraft')
		self._properties['screenshotspath'] = os.path.join(self._properties['minecraftpath'], 'screenshots')
		
