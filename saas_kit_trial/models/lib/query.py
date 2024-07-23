import os,time,sys
import random, string
import json
import subprocess
# import re,shutil
import argparse
import logging
from collections import defaultdict
import socket
from contextlib import closing
import logging
_logger = logging.getLogger(__name__)
from . pg_query import PgQuery
#import pg_query


#CONF VALUES
def is_db_exist(database, host_server = None, db_server = None):
    query = "SELECT datname FROM pg_catalog.pg_database WHERE datname = '{}';".format(database)
    pgX = PgQuery(db_server['host'], "postgres", db_server['user'], db_server['password'], db_server['port'])
    result = False
    with pgX as pg:
        if not pg.get('status'):
            return pg
        result = pgX.selectQuery(query)
        if result:
            result = True
    response = dict(
        status=True,
        result=result
    )
    return response

def get_user_count(database,host_server = None, db_server = None):
    query = "SELECT COUNT(*) FROM res_users WHERE active=True and share=False;"

    pgX = PgQuery(db_server['host'], database, db_server['user'], db_server['password'], db_server['port'])

    with pgX as pg:
        if not pg.get('status'):
            return pg
        result = pgX.selectQuery(query)

    response = dict(
        status=True,
        result=result
    )
    return response


def get_arrear_users(database , host_server = None, db_server=None, limit = 10000):
    query = "select  login, create_date, (DATE_PART('year', CURRENT_TIMESTAMP::date) - DATE_PART('year', create_date::date)) * 12 + (DATE_PART('month',CURRENT_TIMESTAMP::date) - DATE_PART('month', create_date::date)) from res_users where active = True and share = False order by create_date desc limit %s;"%limit

    pgX = PgQuery(db_server['host'], database, db_server['user'], db_server['password'], db_server['port'])

    with pgX as pg:
        if not pg.get('status'):
            return pg
        result = pgX.selectQuery(query)

    response = dict(
        status=True,
        result=result
    )
    return response

def get_credentials(database, host_server = None, db_server = None):
    #FOR admin user_id = 2
    query = "SELECT login, COALESCE(password, '') FROM res_users WHERE id=2;"

    pgX = PgQuery(db_server['host'], database, db_server['user'], db_server['password'], db_server['port'])

    with pgX as pg:
        if not pg.get('status'):
            return pg
        result = pgX.selectQuery(query)

    response = dict(
        status=True,
        result=result
    )
    return response

def update_user(database, user_id, user_data, partner_data,host_server = None, db_server = None):
    #FOR admin user_id = 2
    user_id = user_id or 2
    # print("----------------%-----%---%---%", database, user_data, partner_data, user_id)
    pgX = PgQuery(db_server['host'], database, db_server['user'], db_server['password'], db_server['port'])
    query = "Update res_users set login = '%s' WHERE id =%d;"%(user_data['login'],user_id)

    with pgX as pg:
        if not pg.get('status'):
            return pg
        result = pgX.executeQuery(query)
    with pgX as pg:
        if not pg.get('status'):
            return pg
        partner_id = pgX.selectQuery("Select partner_id from res_users where id = %d;"%user_id)[0][0]
    print(partner_id)
    query = "Update res_partner set name = '%s', street = '%s', street2 = '%s', city = '%s', zip = '%s', phone = '%s', mobile = '%s', email = '%s', website = '%s', signup_token = '%s', signup_type = '%s' WHERE id =%s;"%(partner_data['name'],partner_data['street'],partner_data['street2'],partner_data['city'],partner_data['zip'],partner_data['phone'],partner_data['mobile'],partner_data['email'],partner_data['website'], partner_data['signup_token'], partner_data['signup_type'], partner_id)

    with pgX as pg:
        if not pg.get('status'):
            return pg
        result = pgX.executeQuery(query)

    response = dict(
        status=True,
        result=result
    )
    return response

def set_user_limt(vals, db_server=None, is_count=None):
    """
    Use to set the max and min user limit of user to be created in client's instance
    called from set user data if per_user_pricing is true
    """
    pgX = PgQuery(db_server['host'], vals['database'], db_server['user'], db_server['password'], db_server['port'])
    query1 = "Update ir_config_parameter set value ='{}' where key='user.min_users'".format(str(vals['min_users']))
    query2 = "Update ir_config_parameter set value ='{}' where key='user.max_users'".format(str(vals['max_users']))
    query3 = "Update ir_config_parameter set value ='{}' where key='user.count'".format(str(is_count))
    with pgX as pg:
        if not pg.get('status'):
            return pg
        result1 = pgX.executeQuery(query1)
        result2 = pgX.executeQuery(query2)
        result3 = pgX.executeQuery(query3)
    result = result1 and result2 and result3
    response = dict(
        status=True,
        result=result
    )
    return response


def set_trial_data(database, trial_data, db_server=None):
    pgX = PgQuery(db_server['host'], database, db_server['user'], db_server['password'], db_server['port'])
    query1 = "Update ir_config_parameter set value ='{}' where key='trial.is_trial_enabled'".format(trial_data['trial.is_trial_enabled'])
    query2 = "Update ir_config_parameter set value ='{}' where key='trial.trial_period'".format(trial_data['trial.trial_period'])
    query3 = "Update ir_config_parameter set value ='{}' where key='trial.purchase_link'".format(trial_data['trial.purchase_link'])
    with pgX as pg:
        if not pg.get('status'):
            return pg
        result1 = pgX.executeQuery(query1)
        result2 = pgX.executeQuery(query2)
        result3 = pgX.executeQuery(query3)
    result = result1 and result2 and result3

    response = dict(
        status=True,
        result=result
    )
    return response


if __name__=='__main__':
    data = {
      'database': 'template_test_plan_tid_31',
      'user_id': 6,
      'user_data': {
        'name': 'Aditya Sharma',
        'login': 'aditya.sharma185@webkul.com'
      },
      'partner_data': {
        'name': 'Aditya Sharma',
        'street': '',
        'street2': '',
        'city': '',
        'state_id': False,
        'zip': '',
        'country_id': False,
        'phone': '',
        'mobile': '',
        'email': 'aditya.sharma185@webkul.com',
        'website': '',
        'signup_token': 'asghCKmcBjZ1FIMiI78k',
        'signup_type': 'signup'
      }
    }
    #print(get_credentials())
    #print(update_user(**data))
