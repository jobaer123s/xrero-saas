import xmlrpc.client
import docker
import os,subprocess,shutil
import logging
from configparser import ConfigParser
import paramiko

nginx_vhost = "/var/lib/odoo/Odoo-SAAS-Data/docker_vhosts/"
data_dir = "/var/lib/odoo/Odoo-SAAS-Data/"
client_admin_passwd = "Yb32vfyRsMa7HDaG"
template_port = 8888
_logger = logging.getLogger(__name__)
oversion = "17"
class container(object):

    def __init__(self):
        self.dclient = None

    def get_client(self,host = "localhost"):
        _logger.info("=====>>> %r"%host)
        try:
            if host == "localhost":
                self.dclient = docker.from_env()
            else:
                self.dclient = docker.DockerClient("tcp://%s:2375"%host)
        except Exception as e:
            _logger.error("Not able to get a docker client!!")
            return False
        return True

    def get_container(self,id):
        try:
            return self.dclient.containers.get(id)
        except docker.errors.NotFound as error:
            _logger.error("Error while getting container %r"%error)
            return False


def drop_db(db,url):
    dbs = []
    sock_db = xmlrpc.client.ServerProxy('{}/xmlrpc/db'.format(url))
    try:
        _logger.info("In Check_connectivity script at line {}".format(43))
        dbs = sock_db.list()
    except Exception as e:
        _logger.warn("Error in Check_connectivity script in sock_db.list() at line {}".format(46))
        sock_db = xmlrpc.client.ServerProxy('{}/xmlrpc/db'.format(url))
        if db in sock_db.list():
            _logger.error("URL couldn't be reached but DB does exist")
            return False
        _logger.error("URL couldn't be reached but DB already deleted")
        return True
    if db not in dbs:
        _logger.error("Database %r doesn't exist"%db)
        return True
    try:
        sock_db.drop(client_admin_passwd, db)
    except Exception as e:
        if db in sock_db.list():
            _logger.error("Error droping DB %r:- %r"%(db,e))
            _logger.error("Database %r Still exists."%db)
            return False
        else:
            _logger.info("DB %r Deleted!!"%db)
            return True
    return True
    #result = sock_db.duplicate_database(admin_passwd, source_db, new_db)

def drop_container(container_id,host = "localhost"):

    dock = container()
    try:
        dock.get_client(host)
    except Exception as e:
        _logger.info("EROOROR %r"%e)
    cont = dock.get_container(container_id)
    if not cont:
        _logger.error("%r Container doesn't exist"%container_id)
        return True
    try:
        cont.remove(force=True)
    except docker.errors.APIError as error:
        _logger.error("Error while Removing operaton %r"%(error))
        return False
    return True

def delete_nginx_vhost(domain):
    if not os.path.exists('{}/{}.conf'.format(nginx_vhost,domain)):
        return True
    try:
        os.remove('{}/{}.conf'.format(nginx_vhost,domain))
        return reload_nginx()
    except FileNotFoundError as error:
        _logger.error("%r vhost file doesn't exist"%domain)
    except Exception as error:
        _logger.error("Error deleting %r vhost %r"%(domain,error))
    return False

def delete_remote_data_dir(domain,ssh_obj):
    path = '{}/{}'.format(data_dir,domain)
    _logger.info("Data dir is %s"%path) 
    sftp = ssh_obj.open_sftp()
    if "odoo-server.conf" in sftp.listdir(path):#os.path.exists(path+"/odoo-server.conf"):
        try:
            ver = oversion + ".0"
            if ver in sftp.listdir(path+"/data-dir/addons/"):#os.path.exists(path+"/data-dir/addons/12.0"): 
                _logger.info("Permissions of Odoo addons/%s"%ver)
                sftp.chmod(path+"/data-dir/addons/"+ver,0o700)
            execute_on_remote_shell(ssh_obj,"rm -rf %s"%path)
            return True
        except Exception as error:
            _logger.error("Error deleting %r data dir %r"%(domain,error))
    else:
        return True
    return False

def delete_data_dir(domain):
    path = '{}/{}'.format(data_dir,domain)
    _logger.info("$$$$$ %r "%path)
    if os.path.exists(path+"/odoo-server.conf"):
        try:
            ver = oversion + ".0"
            if os.path.exists(path+"/data-dir/addons/"+ver):
                _logger.info("Permissions of Odoo addons/%s"%ver)
                os.chmod(path+"/data-dir/addons/"+ver,0o700)
            shutil.rmtree(path)
            return True
        except Exception as error:
            _logger.error("Error deleting %r data dir %r"%(domain,error))
    else:
        return True
    return False


def reload_nginx():
    if not execute_on_shell("sudo nginx -t"):
        _logger.error("Error in nginx config!!.Syntax test Failed")
        return False
    if not execute_on_shell("sudo nginx -s reload"):
        _logger.error("Error reloading Nginx")
        return False
    return True

def execute_on_shell(cmd):
    try:
        _logger.info("Saas Module Going to execute command ----    %r", cmd)
        res = subprocess.check_output(cmd,stderr=subprocess.STDOUT,shell=True)
        _logger.info("Saas Module successfully the command ----")
        _logger.info("-----------COMMAND RESULT--------%r", res)
        return True
    except Exception as e:
        _logger.error("Failed to execute the command      {}     {}".format(e, cmd))
        return False

def update_values(config_path):
    global nginx_vhost, data_dir, client_admin_passwd, template_port
    result = {
            'status': True,
            'message': 'Success'
        }
    try:
        parser = ConfigParser()
        parser.read(config_path + "/models/lib/saas.conf")
        nginx_vhost = parser.get("options","odoo_saas_data")+"/docker_vhosts"
        data_dir = parser.get("options","odoo_saas_data")
        client_admin_passwd = parser.get("options","template_master")
        template_port = parser.get("options","template_odoo_port_v"+str(oversion))
    except Exception as e:
        _logger.error('Missing key in saas.conf file.. {}'.format(e))
        result['status'] = False
        result['message'] = e
    return result

def login_remote(context):
    try:
        ssh_obj = paramiko.SSHClient()
        ssh_obj.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_obj.connect(hostname=context['host'], username=context['user'], password=context['password'],port=context['port'])
        return ssh_obj
    except Exception as e:
        _logger.error("Couldn't connect remote %r"%e)
        return False

def execute_on_remote_shell(ssh_obj,command):
    _logger.info('Saas Command to execut on Remote shell --- %r'%command)
    try:
        ssh_stdin, ssh_stdout, ssh_stderr = ssh_obj.exec_command(command)
        _logger.info(ssh_stdout.readlines())
        _logger.info('Saas Successfully executed command on Remote shell ---')
        return True
    except Exception as e:
        _logger.error("Saas Error while executing Command on Remote")
        _logger.error("++++++++++ERROR++++%r",e)
        return False

def main(domain, port, host_server, config_path, container_id=None, db_server=None, from_drop_container=None, from_drop_db=None, version = "17"):
    server_type = host_server['server_type']
    _logger.info("____%r++++++"%domain)
    _logger.info("____%r++++++"%container_id)
    _logger.info("____%r++++++"%port)
    _logger.info("____%r++++++"%host_server)
    _logger.info("____%r++++++"%db_server)
    global oversion
    oversion = version.split('.')[0]
    response = {"db_drop":False,"drop_container": False,'delete_data_dir':False,'delete_nginx_vhost':False }
    res = update_values(config_path)
    if not res.get('status'):
        response['status'] = res.get('message')
        return response
    isitlocal = True
    if server_type != "self":
        isitlocal = False
        if not login_remote(host_server):
            response['status'] = "Couldn't Connect to %s. Please check the connectivity"%host_server['host']
            return response
    if from_drop_db:        
        #response["db_drop"] = drop_db(domain,"http://{}:{}".format("localhost" if isitlocal else host_server['host'], template_port))
        response["db_drop"] = drop_db(domain,"http://{}:{}".format("localhost", template_port))
        return response
    _logger.info("ISITLOCAL %r"%isitlocal)
    if from_drop_container:
        if isitlocal:
            response['drop_container'] = drop_container(container_id)
        else:
            response['drop_container'] = drop_container(container_id , host_server['host'])
    if response['drop_container']:
        response['delete_nginx_vhost'] = delete_nginx_vhost(domain)
    if response['delete_nginx_vhost']:
        if not isitlocal:
            ssh_obj = login_remote(host_server)
            response['delete_data_dir'] = delete_remote_data_dir(domain,ssh_obj)
        else:
            response['delete_data_dir'] = delete_data_dir(domain)
    _logger.info(response)
    return response


def main_plan(domain , host_server = None,  config_path = None):

    server_type = host_server['server_type']
    _logger.info("____%r++++++"%domain)
    _logger.info("____%r++++++"%host_server)

    response = {"db_drop":False}
    res = update_values(config_path)
    if not res.get('status'):
        response['status'] = res.get('message')
        return response
    isitlocal = True
    if server_type != "self":
        isitlocal = False
        if not login_remote(host_server):
            response['status'] = "Couldn't Connect to %s. Please check the connectivity"%host_server['host']
            return response


    response["db_drop"] = drop_db(domain,"http://{}:{}".format("localhost", template_port))
    _logger.info("ISITLOCAL %r"%isitlocal)
    if response['db_drop']:
        response["drop_db"] = True
    return response

