import os
import argparse
import logging
import socket
import mimetypes

from webob.dec import wsgify
from webob import Response
import webob.exc

from pycman.config import PacmanConfig
from pacshare import avahi

class FileIterable(object):
    def __init__(self, filename):
        self.filename = filename
    def __iter__(self):
        return FileIterator(self.filename)

class FileIterator(object):
    chunk_size = 4096
    def __init__(self, filename):
        self.filename = filename
        self.fileobj = open(self.filename, 'rb')
    def __iter__(self):
        return self
    def __next__(self):
        chunk = self.fileobj.read(self.chunk_size)
        if not chunk:
            raise StopIteration
        return chunk

class WsgiApplication(object):
    def __init__(self, config):
        self.config = config
    
    @wsgify
    def __call__(self, request):
        path = request.path.rstrip('/').split('/')[1:]
        if len(path) > 1:
            return webob.exc.HTTPNotFound()
        
        cachedirs = self.config.options.get(
            'CacheDir',
            ['/var/cache/pacman/pkg']) # Older versions of pycman.config did not have a default for CacheDir
        
        for cachedir in cachedirs:
            filepath = os.path.join(cachedir, path[0])
            if os.path.exists(filepath):
                res = Response()
                type, encoding = mimetypes.guess_type(filepath)
                # We'll ignore encoding, even though we shouldn't really
                res.content_type = type or 'application/octet-stream'
                res.app_iter = FileIterable(filepath)
                res.content_length = os.path.getsize(filepath)
                res.last_modified = os.path.getmtime(filepath)
                res.conditional_response = True
                return res
        
        return webob.exc.HTTPNotFound()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', help='Host for server to listen on.',
                        default='')
    parser.add_argument('--port', help='Port for server to listen on.',
                        default=8330)
    parser.add_argument('--pacman-config', help='Config file for pacman.',
                        default='/etc/pacman.conf')
    args = parser.parse_args()
    # TODO config file for server, logging, and alpm options.
    
    logging.basicConfig(level=logging.DEBUG)
    
    try:
        # TODO - check for changes in this file, and reload
        config = PacmanConfig(conf=args.pacman_config)
        wsgi_app = WsgiApplication(config)
        
        from wsgiref.simple_server import make_server
        httpd = make_server(args.host, args.port, wsgi_app)
        
        avahi.entry_group_add_service('pacshare on {}'.format(socket.gethostname()),
                                      '_pacshare._tcp', port=args.port, host=args.host)
        logging.info('Starting server.')
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt as e:
            logging.info('Keyboard Interrupt')
        finally:
            logging.info('Server stoped.')
    except:
        logging.exception('')

