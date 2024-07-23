import os,time,sys
import random, string
import json
import subprocess
# import imp,re,shutil
import argparse
import logging
import paramiko
import psycopg2
from . import check_connectivity
_logger = logging.getLogger(__name__)

def ishostaccessible(details):
    if details['server_type'] == "self":
        return True
    try:
        ssh_obj = paramiko.SSHClient()
        ssh_obj.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        _logger.info("Saas In check_if_db_accessible scipt at Line {}".format(19))
        ssh_obj.connect(hostname = details['host'], username = details['user'], password = details['password'], port = details['port'])
        return ssh_obj
    except Exception as e:
        _logger.info("Couldn't connect remote%r"%e)
        raise e
class connect_exception(Exception):
    def __init__(self,message):
        print(message)





def isdbaccessible(host_server, db_server, config_path=None):
    response = dict()
    response['status'] = True
    response['message'] = 'Success'
    res = check_connectivity.ishostaccessible(host_server)
    if not res.get('status'):
        return res
    _logger.info("Recieved Request %r"%locals())
    details = db_server
    try:
        psycopg2.connect(
                dbname="postgres",
                user=details['user'],
                password=details['password'],
                host=details['host'],
                port=details['port'])
        _logger.info("Local Connection BUilt")
    except Exception as e:
        response['status'] = False
        response['message'] = e    
        _logger.info("Error while connecting from local DB :-%r"%e)
        return response
    if host_server['server_type'] == "self":
        return response
    try:
        ssh_obj = paramiko.SSHClient()
        ssh_obj.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_obj.connect(hostname = host_server['host'], username = host_server['user'],password = host_server['password'], port = host_server['port'])
        sftp = ssh_obj.open_sftp()
        sftp.put(config_path+"/models/lib/connect_db.py",'/tmp/connect_db.py')
        sftp.close()

        cmd = "python3 -W ignore /tmp/connect_db.py  %r %r %r %r"%(details['user'], details['password'], details['host'], details['port'])
        ssh_stdin, ssh_stdout, ssh_stderr = ssh_obj.exec_command(cmd)
        res = ssh_stdout.readlines()
        _logger.info("result = %r  %r"%(ssh_stderr.readlines(),res))

        if str(res[0].strip()) != "Yes":
            response['status'] = False
            response['message'] = "Connecting from Remote Host :- {}".format(res)
    except Exception as e:
        response['status'] = False
        response['message'] = e
    return response
