import configargparse


parser = configargparse.get_argument_parser(name='default')

parser.add_argument('--log-level', type=str, help='Runtime log level', env_var='LOG_LEVEL')

parser.add_argument('--target-host', type=str, help='Target KA host',
                    env_var='TARGET_HOST')

parser.add_argument('--product-quantity', type=int, help='Product quantity to deplete from QPM',
                    env_var='PRODUCT_QUANTITY')

parser.add_argument('--unit-cost', type=int, help='Cost per unit',
                    env_var='UNIT_COST')

parser.add_argument('--item-total', type=int, help='Total items included in transaction',
                    env_var='ITEM_TOTAL')

parser.add_argument('--product-event-type', type=str, help='The type of event occurring in QPM',
                    env_var='PRODUCT_EVENT_TYPE')

parser.add_argument('--stage', type=str, help='Stage in which the event occurs',
                    env_var='STAGE')

parser.add_argument('--non-depleting', action='store_true', help='Will the event deplete product in QPM',
                    env_var='NON_DEPLETING')

parser.add_argument('--api-key', type=str, help='Chef API key path', env_var='API_KEY')

parser.add_argument('--username', type=str, help='Chef username', env_var='USERNAME')

parser.add_argument('--server-url', type=str, help='Chef server url', env_var='SERVER_URL')

parser.add_argument('--node-name', type=str, help='Node hostname', env_var='NODE_NAME')
