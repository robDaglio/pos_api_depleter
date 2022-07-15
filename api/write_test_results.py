import chef
import os

import requests

from logger import Logger
from config import parser


cfg, unknown = parser.parse_known_args()
logger = Logger(name=__name__, log_level=cfg.log_level).get_logger()


def generate_key_file(api_key):
    logger.debug('Generating api key file.')

    key = ''''''

    try:
        with open(api_key, 'w') as f:
            f.write(key)
    except (IOError, EOFError, BufferError, Exception) as e:
        logger.exception(f'Unable to read key file.\n{e}')

    try:
        logger.debug(f'Modifying file permissions for {api_key}')
        os.chmod(api_key, 0o777)
    except Exception as e:
        logger.debug(f'Unable to write new permissions for {api_key}')
        logger.debug('API Object creation failed.')


def create_chef_api_object(server, api_key, username):
    generate_key_file(api_key)

    try:
        logger.debug('Creating API object.')
        chef_api_object = chef.ChefAPI(server, api_key, username)
        os.remove(api_key)
        return chef_api_object
    except (
        chef.exceptions.ChefServerError,
        FileNotFoundError,
        Exception
    ) as e:
        logger.exception(f'API object creation failed.\n{e}')


def write_attribute(results, api, node_name):
    try:
        logger.debug(f'Creating node object for {node_name}')
        node = chef.Node(node_name, api=api)

        logger.debug('Writing new attribute.')
        node.attributes['kb']['qpm']['tests'] = {}
        node.attributes['kb']['qpm']['tests']['pos_api_sales'] = results

        node.save()
    except (
        chef.exceptions.ChefServerError,
        requests.ConnectionError,
        requests.exceptions.ConnectionError,
        requests.exceptions.HTTPError,
        KeyError,
        Exception
    ) as e:
        logger.exception(f'Unable to write new attribute.\n{e}')

