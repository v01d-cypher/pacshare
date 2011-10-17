import argparse
import logging
import os
import sys

from urllib.request import FancyURLopener

from pacshare.progressbar import ProgressBar

class MyURLOpener(FancyURLopener):
    def http_error_404(self, url, fp, errcode, errmsg, headers):
        print(url, errcode, errmsg)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('url', help='URL to download')
    parser.add_argument('filename', help='Filename to save as')
    
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    org_url = args.url
    package = os.path.basename(org_url)
    save_location = args.filename

    pb = ProgressBar(filename=package)


    url = 'http://localhost:16661/%s' % package
    try:
        logging.debug('Downloading {} to {}'.format(url, args.filename))
        MyURLOpener().retrieve(url, save_location, pb.update)
    except:
        try:
            logging.debug('Downloading {} to {}'.format(org_url, args.filename))
            MyURLOpener().retrieve(org_url, save_location, pb.update)
        except:
            pass
