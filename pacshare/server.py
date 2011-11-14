import argparse
import logging

from webob.dec import wsgify
from webob import Response
import webob.exc

import pyalpm
from pycman import config

class Application(object):
    def __init__(self, config_file='/etc/pacman.conf'):
        # TODO - check for changes in this file, and reload
        config.init_with_config(config_file)
    
    @wsgify
    def __call__(self, request):
        path = request.path.rstrip('/').split('/')[1:]
        lenpath = len(path)
        
        dbs = dict(((db.name, db) for db in pyalpm.get_syncdbs()))
        if lenpath == 0:
            return self.list(dbs.keys())
        
        try:
            db = dbs[path[0]]
        except KeyError:
            return webob.exc.HTTPNotFound()
        
        if lenpath==1:
            return self.list(('os',))
        
        if lenpath==2:
            return self.list((pyalpm.options.arch,))
        
        if lenpath==4:
            if path[3] == '{}.db'.format(path[0]):
                return Response('db!')
        
        return webob.exc.HTTPNotFound()
    
    def list(self, items):
        r = Response()
        r.text = ''.join('<a href="{0}/">{0}</a><br/>\n'.format(item)
                         for item in items)
        return r
    

def main():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    
    # TODO config file
    logging.basicConfig(level=logging.DEBUG)
    
    from wsgiref.simple_server import make_server
    
    app = Application()    
    httpd = make_server('', 8000, app)
    
    logging.info('Starting server.')
    
    try:
        httpd.serve_forever()
    finally:
        logging.info('Stoping server.')
