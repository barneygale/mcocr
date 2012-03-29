from app import server
import asyncore
import os

server.basedir = os.path.dirname(os.path.realpath(__file__))

if __name__ == "__main__":
	try:
		server = server.Server()
		server.settings['basedir'] = os.path.dirname(os.path.realpath(__file__))
		server.serve_forever()
	    
	except:
	    raise
	    os.system("kill %s" % str(os.getpid()))
    
