import argparse
import logging
import os
import sys
import random
import re

from urllib.request import urlopen
from urllib.error import HTTPError
from urllib.parse import urlparse

from progressbar import Bar, ETA, FileTransferSpeed, \
                        Percentage, ProgressBar

from pacshare import avahi


def get_progressbar(filename, maxval):
    widgets = ['{:30}'.format(filename), ETA(), '  ',
               FileTransferSpeed(), ' ', Bar(), ' ',
               Percentage()]
    pbar = ProgressBar(widgets=widgets, maxval=maxval)
    return pbar

def retrieve_data(open_url, save_location):
    total_size = int(open_url.getheader('Content-Length') or '0')
    pbar = get_progressbar(os.path.basename(open_url.geturl()), total_size)
    if total_size:
        pbar.start()
    else:
        logging.info('Downloading file ... (no progess available)')
    block_size = 4096

    try:
        with open(save_location, 'wb') as filename:
            while True:
                chunk = open_url.read(block_size)
                if not chunk:
                    break
                if pbar.start_time is not None:
                    pbar.update(pbar.currval + len(chunk))
                filename.write(chunk)
    finally:
        if pbar.start_time is not None:
            pbar.finish()


package_re = re.compile('.*/(.*\.pkg\.tar\.xz)$')
def gen_urls(url):
    up = urlparse(url)
    package_name_match = package_re.search(up.path)
    if package_name_match:
        logging.debug('Package detected. Atempting to fetch from peer pacshares.')
        services = avahi.service_browser_get_cache('_pacshare._tcp')
        # remove the duplicates due to multiple interfaces/protocals.
        services = list(dict((service.name, service) for service in services).values())
        random.shuffle(services)
        for service in services:
            if not (service.flags & avahi.LookupResultFlags.LOCAL):
                resolved_service = avahi.resolve_service(service.name, service.type, service.domain)
                
                logging.debug('Atempting fetch from {}'.format(resolved_service.host_name))
                yield 'http://{}:{}/{}'.format(
                    resolved_service.address, resolved_service.port,
                    package_name_match.group(1))
    yield url

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('url', help='URL to download')
    parser.add_argument('filename', help='Filename to save as')
    
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    
    try:
        for url in gen_urls(args.url):
            try:
                logging.debug('Downloading {} to {}'.format(url, args.filename))
                open_url = urlopen(url)
            except HTTPError as e:
                logging.debug('Error Downloading {} : {}'.format(url, e))
            except Exception:
                logging.exception('Downloading {}'.format(url))
            else:
                retrieve_data(open_url, args.filename)
                return 0
        logging.error('Could not retrieve file from any url.')
        return 1
    except KeyboardInterrupt as e:
        logging.debug('User pressed CTRL-C')
        return 1
