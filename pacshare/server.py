import os
import shutil
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler

from pacshare import avahi


class PacShareHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Serve a GET request."""
        f = self.get_file()
        if f:
            shutil.copyfileobj(f, self.wfile)
            f.close()

    def get_file(self):
        #repo,os,arch

        cache_root = '/var/cache/pacman/pkg'

        cache_structure = 'flat'
        #cache_structure = 'Arch Mirror'

        path = self.path.strip('/')

        if cache_structure == 'Arch Mirror':
            pass
        elif cache_structure == 'flat':
            path = os.path.basename(path)
            #if path.endswith('.db'):
            #    cache_root = '/var/lib/pacman/sync'

        package_location = os.path.join(cache_root, path)

        f = None

        try:
            f = open(package_location, 'rb')
        except IOError:
            self.send_error(404, "File not found")
            return None

        self.send_response(200)
        self.send_header("Content-type", 'application/octet-stream')
        fs = os.fstat(f.fileno())
        self.send_header("Content-Length", str(fs[6]))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()
        return f

PORT = 16661
server_address = ('', PORT)
httpd = HTTPServer(server_address, PacShareHTTPRequestHandler)

avahi.entry_group_add_service('pacshare on {}'.format(socket.gethostname()),
                              '_pacshare._tcp', port=PORT)
httpd.serve_forever()

