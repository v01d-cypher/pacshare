import argparse
import logging
import os
import sys
import random
import re
import datetime
import shutil

from urllib.request import urlopen, Request
from urllib.error import HTTPError
from urllib.parse import urlparse

from webob.datetime_utils import parse_date, serialize_date, UTC
import progressbar

from pacshare import avahi

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('url', help='URL to download')
    parser.add_argument('filename', help='Filename to save as')
    
    args = parser.parse_args()
    global log_handler
    log_handler = StreamHandlerProgressBarClear(sys.stdout)
    log_handler.setFormatter(logging.Formatter('%(levelname)s:%(message)s'))
    root_log = logging.getLogger()
    root_log.addHandler(log_handler)
    root_log.setLevel(logging.DEBUG if args.verbose else logging.INFO)

    try:
        fetch_success = fetch_url(args.url, args.filename)
        if fetch_success:
            return 0
        else:
            return 2
    except KeyboardInterrupt as e:
        logging.error('Interrupt signal received')
        return 1
    except:
        logging.exception('')
        return 2

class StreamHandlerProgressBarClear(logging.StreamHandler):
    
    def emit(self, record):
        try:
            pbar = getattr(self, 'pbar', None)
            if pbar:
                pbar.fd.write((' ' * pbar.term_width) + '\r')
        except:
            self.handleError(record)
        super().emit(record)
        try:
            if pbar:
                pbar.update()
        except:
            self.handleError(record)

def get_pacshare_peers():
    logging.debug('Getting pacshare peers from avahi.')
    services = avahi.service_browser_get_cache('_pacshare._tcp')
    services = [service for service in services
                if not (service.flags & avahi.LookupResultFlags.LOCAL)]
    if services:
        logging.debug('Peers found: %s.', [service.name for service in services])
    else:
        logging.debug('No peers found.')
    for service in services:
        yield avahi.resolve_service(
            service.name, service.type, service.domain)


def http_date_to_datetime(s):
    return datetime.datetime.strptime(s, '%a, %d %b %Y %H:%M:%S %z')

package_re = re.compile('(.*)\.pkg\.tar\.xz$')
def fetch_url(url, filename):
    status_widget = ProgressBarStatusWidget()
    pbar = progressbar.ProgressBar(widgets=[status_widget], maxval=0)
    progressbar.ProgressBar._need_update = lambda self: True

    status_widget.format = '{0.resource_name} {0.server_from}'
    status_widget.resource_name = ''
    status_widget.server_from = ''
    pbar.start()
    log_handler.pbar = pbar
    
    try:
        last_modified = None
        if filename.endswith('.part'):
            old_file_path = filename[:-5]
            try:
                last_modified = datetime.datetime.fromtimestamp(
                    os.path.getmtime(old_file_path),
                    UTC)
            except OSError:
                pass # Most likly the file does not exist.
        
        def not_modified_use_old_file():
            logging.debug("{} not modified, using {}".format(url, old_file_path))
            shutil.copyfile(old_file_path, filename)
            status_widget.format = '{0.resource_name} {0.server_from} - Not modified.'
            pbar.finish()
            return True
        
        def _fetch_url(url, error_level=logging.ERROR):
            try:
                logging.debug('Downloading {} to {}'.format(url, filename))
                pbar.update()
                request = Request(url)
                if last_modified:
                    request.headers['If-Modified-Since'] = serialize_date(last_modified)
                response = urlopen(request)
                
                response_last_modified = parse_date(response.headers['last-modified'])
                if last_modified and last_modified >= response_last_modified:
                    response.close()
                    return not_modified_use_old_file()
                
                total_size = int(response.getheader('Content-Length') or '0')
                
                if total_size:
                    pbar.maxval = total_size
                    pbar.widgets = [status_widget, '  ',
                                    progressbar.ETA(), '  ', progressbar.FileTransferSpeed(), ' ',
                                    progressbar.Bar(), ' ',
                                    progressbar.Percentage()]
                    pbar.update
                else:
                    # what pbar widget do we need here?
                    pass
                
                block_size = 1024        
                with open(filename, 'wb') as file:
                    while True:
                        chunk = response.read(block_size)
                        if not chunk:
                            break
                        file.write(chunk)
                        pbar.update(pbar.currval + len(chunk))
                logging.debug('Download successfull.')
                pbar.finish()
                return True
            except HTTPError as e:
                if e.code == 304:
                    return not_modified_use_old_file()
                logging.log(error_level, 'Downloading {} : {}'.format(url, e))
                return False
            except Exception:
                logging.exception('Downloading {}'.format(url))
                return False
        
        up = urlparse(url)
        path = up.path.split('/')[1:]
        status_widget.resource_name = path[-1]
        
        package_name_match = package_re.match(path[-1])
        if package_name_match:
            logging.debug('Package detected.')
            status_widget.resource_name = package_name_match.group(1)
            status_widget.server_from = 'Getting pacshare peers.'
            pbar.update()
            for peer in get_pacshare_peers():
                status_widget.server_from = 'from {0.host_name}'.format(peer)
                fetch_success = _fetch_url(
                    'http://{}:{}/{}'.format(peer.address, peer.port,
                                             package_name_match.group(0)),
                    logging.DEBUG)
                if fetch_success:
                    return True
        
        status_widget.server_from = 'from {0.netloc}'.format(up)
        return _fetch_url(url)
    except:
        pbar.fd.write('\n')
        raise
    finally:
        log_handler.pbar = None


class ProgressBarStatusWidget(progressbar.Widget):
    def update(self, pbar):
        return self.format.format(self, pbar)

