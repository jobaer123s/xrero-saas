import os,time,sys
import random, string
import json
import subprocess
# import imp,re,shutil
import argparse
import logging
import logging
import paramiko
import psycopg2
_logger = logging.getLogger(__name__)

def ishostaccessible(details):
    response = dict(
        status=True,
        message='Success'
    )
    if details['server_type'] == "self":
        return response
    try:
        ssh_obj = paramiko.SSHClient()
        ssh_obj.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        _logger.info("Saas In check_connectivity scipt at Line {}".format(23))
        ssh_obj.connect(hostname = details['host'], username = details['user'], password = details['password'], port = details['port'])
        response['result'] = ssh_obj
        return response
    except Exception as e:
        _logger.info("Couldn't connect remote %r"%e)
        response['status'] = False
        response['message'] = e
    return response

def isdbaccessible(details):
    response = dict(
        status=True,
        message='Success'
    )
    _logger.info("Recieved Request %r"%locals())
    try:
        psycopg2.connect(
                dbname="postgres",
                user=details['user'],
                password=details['password'],
                host=details['host'],
                port=details['port'])
    except Exception as e:
        _logger.info("Error while connecting DB :-%r"%e)
        response['status'] = False
        response['message'] = e
    return response
