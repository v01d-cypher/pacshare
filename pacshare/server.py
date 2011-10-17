import os
import shutil

from http.server import HTTPServer, BaseHTTPRequestHandler

class PacShareHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Serve a GET request."""
        f = self.get_file()
        if f:
            shutil.copyfileobj(f, self.wfile)
            f.close()

    def get_file(self):
        package_cache = '/var/cache/pacman/pkg'
        package = self.path.strip('/')
        f = None

        try:
            f = open(os.path.join(package_cache, package), 'rb')
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


server_address = ('', 16661)
httpd = HTTPServer(server_address, PacShareHTTPRequestHandler)
httpd.serve_forever()
