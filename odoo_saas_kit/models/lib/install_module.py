import logging
import time
from configparser import ConfigParser
_logger = logging.getLogger(__name__)

try:
    import erppeek
except ImportError as e:
    _logger.error("erppeek library not installed!!")
    
    
def install_modules(client, modules = []):
    modules_missed = []
    for each in modules:
        try:
            client.install(each)
            time.sleep(1)
        except Exception as e:
            modules_missed.append(each)
            _logger.error("Module %s couldn't be installed. Erro:- %r"%(each,str(e)))
        else:
            _logger.info("Module %s installed"%each)
    return (False if len(modules_missed) else True, modules_missed)

def connect_db(url , database , user_name , passwd , flag = True):
    count = 0
    client = ""
    while count < 5:
        try:
            _logger.info("Attempt %d %s."%(count,flag))
            client = erppeek.Client(server=str(url),db = database, user = user_name,password = passwd)
            break
        except Exception as e:
            _logger.error("Could not Connect. Error %s"%str(e))
            count += 1
            time.sleep(4)
    else:
        _logger.info("Maximum attempt made but couldn't connect")
        return False
    _logger.info("Connection built!! %s"%client)
    return client

def process_install(modules_list=None, odoo_url=None, database_name=None, odoo_username=None, odoo_password=None):
    response = dict()
    if modules_list:
        client = connect_db(odoo_url,database_name, odoo_username, odoo_password)
        if not client:
            response['modules_installation'] = False
            return response
        response['modules_installation'], response['modules_missed'] = install_modules(client, modules_list)
    return response

def get_port(path, version):
    parser = ConfigParser()
    parser.read(path)
    template_odoo_port = parser.get("options","template_odoo_lport_v"+version)
    return template_odoo_port


def main(kwargs):
    db = kwargs.get("db_name")
    modules = kwargs.get('modules')
    version = kwargs.get('version').split('.')[0]
    endpoint = "localhost"
    path = kwargs.get('config_path')+"/models/lib/saas.conf"
    saas_port = get_port(path, version)
    response =  process_install(odoo_url="http://{}:{}".format(endpoint, saas_port),odoo_username = kwargs.get("login") ,odoo_password = kwargs.get("password"), database_name = db ,modules_list = modules)
    return response
