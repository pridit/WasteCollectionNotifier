"""
Notify: send a push notification with local waste collections.
"""

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

    response = requests.get(parser.get('athomeapp', 'url'), headers=headers)

    if response.status_code == 200:
        collections = json.loads(response.content.decode('utf-8'))
        
        output = []
        tomorrow = datetime.now() + timedelta(days=1)
        
        for collection in collections.get('userrounds'):
            container = collection.get('containername')
            
            if container == 'Chargeable garden waste bin' and not args.garden:
                continue
            
            try:
                soonest = collection.get('nextcollectiondates', []).pop(0).get('datestring')
                pickup = datetime.strptime(soonest, '%d %m %Y %I:%M')
                
                if pickup.date() == tomorrow.date():
                    output.append(container)
            except IndexError:
                pass
                
        if output:
            print('{} waste collection(s) tomorrow ({})'.format(len(output), ', '.join(map(str, output))))
            
            notification(output)
            
def notification(collections):
    """
    Notify user of their collection day along with waste
    to be collected.
    :param collections: a list representing the waste collection items
    """
    data = {'token': parser.get('pushover', 'api_token'),
            'user': parser.get('pushover', 'user_key'),
            'message': '\r\n'.join(map(str, collections)),
            'title': 'Your collection day is tomorrow'}
    
    requests.post('https://api.pushover.net/1/messages.json', data)
    
if __name__ == '__main__':
    parser = ConfigParser()

    arguments = argparse.ArgumentParser()
    arguments.add_argument('-g', '--garden', help='specify whether to also check garden waste collection', action='store_true')

    args = arguments.parse_args()
    
    config_exists()
    get_collections()