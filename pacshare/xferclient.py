import argparse
import logging
import os
import sys
import random
import re

from urllib.request import urlopen
from urllib.error import HTTPError
from urllib.parse import urlparse

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
        logging.debug('User pressed CTRL-C')
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


package_re = re.compile('(.*)\.pkg\.tar\.xz$')
def fetch_url(url, filename):
    status_widget = ProgressBarStatusWidget()
    pbar = progressbar.ProgressBar(widgets=[
        status_widget, '  ',
        progressbar.ETA(), '  ', progressbar.FileTransferSpeed(), ' ',
        progressbar.Bar(), ' ',
        progressbar.Percentage()], maxval=100)
    progressbar.ProgressBar._need_update = lambda self: True
    
    log_handler.pbar = pbar
    try:
        status_widget.format = '{0.resource_name} {0.server_from}'
        status_widget.resource_name = ''
        status_widget.server_from = ''
        
        def _fetch_url(url, error_level=logging.ERROR):
            try:
                logging.debug('Downloading {} to {}'.format(url, filename))
                pbar.update()
                open_url = urlopen(url)
                total_size = int(open_url.getheader('Content-Length') or '0')
                if total_size:
                    pbar.maxval = total_size
                
                block_size = 1024        
                with open(filename, 'wb') as file:
                    while True:
                        chunk = open_url.read(block_size)
                        if not chunk:
                            break
                        file.write(chunk)
                        pbar.update(pbar.currval + len(chunk))
                logging.debug('Download successfull.')
                pbar.finish()
                return True
            except HTTPError as e:
                logging.log(error_level, 'Downloading {} : {}'.format(url, e))
                return False
            except Exception:
                logging.exception('Downloading {}'.format(url))
                return False
        
        up = urlparse(url)
        path = up.path.split('/')[1:]
        status_widget.resource_name = path[-1]
        
        pbar.start()
        
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

