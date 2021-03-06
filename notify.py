"""
Notify: send a push notification with local waste collections.
"""

import os
import json
import requests
import argparse

from datetime import datetime, timedelta
from configparser import ConfigParser

def config_exists():
    """
    Ensure that the configuration file exists.
    :return: nothing
    """
    with open('config.ini') as file:
        parser.read_file(file)

def get_collections():
    """
    Make the HTTP request and parses the resulting JSON
    to determine whether there is an impending collection.
    """
    headers = {'Content-Type': 'application/json',
               'X-country': 'gb',
               'X-email': parser.get('athomeapp', 'email')}

    response = requests.get(parser.get('athomeapp', 'url'), headers=headers, verify=False)

    if response.status_code == 200:
        collections = json.loads(response.content.decode('utf-8'))

        ready = []
        ignored = []

        tomorrow = datetime.now() + timedelta(days=1)

        for collection in collections.get('userrounds'):
            container = collection.get('containername')

            if container == 'Chargeable garden waste bin' and not args.garden:
                ignored.append(container)
                continue

            if container in legacy and not args.old:
                ignored.append(container)
                continue

            try:
                soonest = collection.get('nextcollectiondates', []).pop(0).get('datestring')
                pickup = datetime.strptime(soonest, '%d %m %Y %I:%M')

                if pickup.date() == tomorrow.date():
                    ready.append(container)
            except IndexError:
                # Empty array
                pass
            except AttributeError:
                # 'None' (suspended collections?)
                pass

        if ready:
            print('{} collection(s) tomorrow ({})'.format(len(ready), ', '.join(map(str, ready))))

            if ignored:
                print('{} ignored ({})'.format(len(ignored), ', '.join(map(str, ignored))))

            notification(ready)

def notification(collections):
    """
    Notify user of their collection day along with waste
    to be collected.
    :param collections: a list representing the waste collection items
    :return: nothing
    """
    data = {'token': parser.get('pushover', 'api_token'),
            'user': parser.get('pushover', 'user_key'),
            'message': '\r\n'.join(map(str, collections)),
            'title': 'Your collection day is tomorrow'}

    requests.post('https://api.pushover.net/1/messages.json', data)

if __name__ == '__main__':
    parser = ConfigParser(os.environ)

    arguments = argparse.ArgumentParser()
    arguments.add_argument('-g', '--garden', help='include garden waste collection', action='store_true')
    arguments.add_argument('-o', '--old', help='include old collections (small boxes)', action='store_true')

    args = arguments.parse_args()

    legacy = [
        'Glass box', 'Paper & Cardboard', 'Plastic and Cans'
    ]

    config_exists()
    get_collections()