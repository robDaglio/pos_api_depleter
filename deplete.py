########################################
# Script name: test_pos_api.py
# Author: Rob Daglio
# Description: This script tests product depletion for two api endpoints
# and reports the results as a chef attribute via the chef API
########################################


from sshtunnel import SSHTunnelForwarder, BaseSSHTunnelForwarderError
from datetime import datetime
from sys import exit

import requests
import pymysql
import time

from config import parser
from logger import Logger
from api import write_test_results

DELAY_COMP = 30
cfg, unknown = parser.parse_known_args()
logger = Logger(name=__name__, log_level=cfg.log_level, log_to_file=True,
                log_file_path='/logs').get_logger()


class KAdb:
    def __init__(self, ip):
        logger.debug(f'Creating database object at {ip}.')
        self.ip = '127.0.0.1' if ip == 'localhost' else ip

        self.mysql_db = ''
        self.mysql_user = ''
        self.mysql_pass = ''
        self.mysql_host = self.ip
        self.mysql_port = 3306

        self.cursor = None
        self.autocommit = True
        self.connection = None
        self.cursor_class = pymysql.cursors.DictCursor

        self.ssh_port = 22
        self.ssh_user = ''
        self.ssh_password = ''
        self.tunnel = self.create_ssh_tunnel()
        self.local_port = self.tunnel.local_bind_port

        self.connect()

    def create_ssh_tunnel(self):
        try:
            ssh_tunnel = SSHTunnelForwarder(
                (self.ip, self.ssh_port),
                ssh_username=self.ssh_user,
                ssh_password=self.ssh_password,
                remote_bind_address=(self.mysql_host, self.mysql_port)
            )
            ssh_tunnel.start()
            return ssh_tunnel
        except (BaseSSHTunnelForwarderError, Exception)as e:
            logger.exception(f'SSH Tunnel Failed: {e}.')
            exit()

    def connect(self):
        try:
            logger.debug(f'Initializing DB connection to {self.mysql_db}.')
            self.connection = pymysql.connect(
                host=self.mysql_host,
                port=self.local_port,
                user=self.mysql_user,
                passwd=self.mysql_pass,
                db=self.mysql_db,
                autocommit=self.autocommit,
                cursorclass=self.cursor_class
            )
        except (pymysql.OperationalError,
                pymysql.Error,
                Exception) as e:
            logger.exception(f'Unable to connect to database:\n{e}')
            exit()

    def execute_query(self, query):
        try:
            logger.debug(f'Executing query {query}.')
            self.cursor = self.connection.cursor()
            self.cursor.execute(query)
            result = self.cursor.fetchall()
            if result:
                return result
        except (
                pymysql.OperationalError,
                pymysql.Error,
                Exception
        ) as e:
            logger.exception(f'Query failed: {e}')

    def verify_depletion(self, value):
        query = f'SELECT * FROM posunmappeditems WHERE UnmappedCode=\'{value}\';'
        return self.execute_query(query)

    def cleanup(self):
        tables = [
            ''
        ]
        logger.debug('Cleaning up remnant table values.')
        for value in ['instore_TEST', 'kfcinstore_TEST']:
            for table in tables:
                query = f'DELETE FROM {table} WHERE UnmappedCode=\'{value}\';'
                logger.debug(f'Deleting {value} from {table}.')
                self.execute_query(query)
                self.connection.commit()
                time.sleep(3)

    def destroy(self):
        logger.debug('Destroying SSH tunnel and closing DB connection.')
        self.connection.close()
        self.tunnel.stop()


def get_time_and_date_strings():
    now = datetime.now()
    ntz = now.astimezone()

    local_now = f'{str(ntz)[-6]}{"".join(str(ntz).split("-")[-1])}'
    offset = local_now[0] + (local_now[2] if local_now[1] == '0' else local_now[1] + local_now[2])

    t = f'{str(now.strftime("%H:%M:%S:%f")[:-3])}{offset}'
    d = now.strftime('%Y-%m-%d')

    logger.debug(f'Time: {t} | Date: {d}')
    return d, t


def generate_xml_payload(endpoint):
    d, t = get_time_and_date_strings()
    non_depleting = 'false' if not cfg.non_depleting else 'true'
    test_id = f'{endpoint}_TEST'

    payload = f'''
    '''

    logger.debug(f'ID: {test_id} | Payload: {payload}')
    return payload


def send_request(endpoint):
    try:
        response = requests.get(endpoint)
        response.raise_for_status()
        return response
    except (
        requests.ConnectionError,
        requests.exceptions.ConnectionError,
        requests.exceptions.HTTPError,
        requests.exceptions.Timeout,
        requests.exceptions.TooManyRedirects,
        Exception
    ) as e:
        logger.exception(e)


def send_xml_payload(target_host, payload, endpoint):
    endpoints = {
        'instore': f'',
        'kfcinstore': f''
    }

    response = send_request(endpoints[endpoint])

    try:
        if not response:
            raise Exception('Request returned empty response.')
        else:
            if response.status_code != 200:
                raise Exception(f'Request failed with status code: {response.status_code}.')
            logger.debug(f'HTTP RESPONSE: {response.content}.')
        return True
    except Exception as e:
        logger.exception(e)
        return False


def deplete():
    logger.debug('Building XML payloads')
    for endpoint in ['instore', 'kfcinstore']:
        payload = generate_xml_payload(endpoint)

        logger.debug(f'Sending payload to {endpoint}')
        if not send_xml_payload(cfg.target_host, payload, endpoint):
            continue


def verify_results(ka_db_obj):
    query_results = dict()
    query_results['Last run'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for endpoint in ['instore', 'kfcinstore']:
        test_value = f'{endpoint}_TEST'
        query_result = bool(ka_db_obj.verify_depletion(test_value))

        time.sleep(DELAY_COMP)

        logger.debug(f'ENDPOINT: {endpoint} | PASSED: {query_result}')
        query_results[endpoint] = 'PASSED' if query_result else 'FAILED'

    return query_results


if __name__ == '__main__':
    ka_db = KAdb(cfg.target_host)

    # Make API calls to simulate product depletion
    deplete()
    time.sleep(DELAY_COMP)

    # Verify records have been created in DB
    results = verify_results(ka_db)

    # Create Chef api object and
    # export results to Chef attribute
    api = write_test_results.create_chef_api_object(cfg.server_url, cfg.api_key, cfg.username)
    write_test_results.write_attribute(results, api, cfg.node_name)

    # Remove test values from relevant tables
    # Delete db object and kill ssh tunnel
    ka_db.cleanup()
    ka_db.destroy()
