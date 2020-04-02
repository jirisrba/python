'''
Created on Oct 3, 2017
@author: anovak
'''

import cx_Oracle
from flask import Flask
from flask import jsonify
from flask import request
from flask import Response
import sys

from os import listdir
from os.path import isfile, join

import datetime
#import pytz
import requests
from requests.auth import HTTPBasicAuth
import json
import traceback

app = Flask(__name__)
root_dir = join('/var', 'dbci', 'log_data')

statuses_enum = ['Development', 'Test', 'Pre-production', 'Production']

@app.route('/SetBuildOk/<string:label>', methods=['POST'])
def build_ok(label):
    try:
        #appname = request.values['appname']
        dbname = request.values['dbname']
        appname,stage = get_api_data(dbname) #request.values['stage']
        #connect_string = get_connect_string(dbname) 
        commit_message = request.values['commit_message']
        if len(commit_message) > 1024:
            commit_message = commit_message[:1024]
        
        update_deployment_status('dbci/abcd1234@//oem12.vs.csin.cz:1521/INFP', label, appname, dbname, stage, commit_message)
    except cx_Oracle.Error as e:
        print('Oracle error:')
        error, = e.args
        return jsonify(insert = 'NOK', oracle_error = 'cx_Oracle.Error', error_code = error.code, error_message = error.message)
    except:
        print(sys.exc_info()[0])
        return jsonify(insert = 'NOK', error = sys.exc_info()[0])
    
    '''persist_label(label)'''
    return jsonify(insert='OK')

def update_deployment_status(connect_string, label, appname, dbname, stage, commit_message):
    with cx_Oracle.connect(connect_string) as con:
        cur = con.cursor()
        try:
            insert_flag = False
            if (cur.execute('SELECT 1 FROM DEPLOYMENT_STATUS WHERE GIT_COMMIT = :label AND DBNAME = :dbname', [label, dbname]) != None):
                result = cur.fetchone()
                if result == None:
                    insert_flag = True
            else:
                insert_flag = True
            
            if insert_flag:
                cur.execute('INSERT INTO DEPLOYMENT_STATUS (GIT_COMMIT, APPNAME, DBNAME, STAGE, GIT_COMMIT_MESSAGE) VALUES(:label, :appname, :dbname, :stage, :commit_message)', [label, appname, dbname, stage, commit_message])
        finally:
            cur.close()
        con.commit()


def check_label_in_directory(label, directory):
    for f in listdir(directory):
        fileName = join(directory, f)
        if isfile(fileName):
            if check_label_in_file(label, fileName):
                return True
    return False         
 
def check_label_in_file(label, fileName):
    with open(fileName, 'r') as sha_file:
        for line in sha_file:
            if label == line.strip():
                return True
    return False
 
def persist_log_file(label, dbname, log):
    fName = '{}_{}.log'.format(label, dbname)
    with open(join(root_dir, fName), 'w') as log_file:
        log_file.write('{}{}'.format(log, '\n'))
 

@app.route('/SetBuildFailed/<string:label>', methods=['POST'])
def build_failed(label):
    dbname = request.values['dbname']
    log = request.values['log']
    
    persist_log_file(label, dbname, log)
    return jsonify(result='OK')

@app.route('/GetLog/<string:label>/<string:dbname>', methods=['GET'])
def get_build_log(label, dbname):
    fName = '{}_{}.log'.format(label, dbname)
    response = ''
    try:
        with open(join(root_dir, fName), 'r') as log_file:
            for line in log_file:
                response += line
    except IOError:
        response = 'The log file has been deleted'   
    return Response(response, mimetype='text/plain')

@app.route('/CheckBuild/<string:dbname>', methods=['GET'])
def check_build(dbname):

    appname, env_status = get_api_data(dbname)
    if env_status == 'Production':
        return jsonify(build_status = 'NOK', error = 'Cannot use production system.')
    
    if env_status == 'Development':
        return jsonify(build_status = 'OK')

    if env_status not in statuses_enum:
        return jsonify(build_status = 'NOK', error = 'Unknown ENV_STATUS {} for DB {}.'.format(env_status, dbname))

    lesser_env_status = get_lesser_status(env_status, dbname)

    if lesser_env_status == None:
        return jsonify(build_status='OK')
    
    try:
        #with cx_Oracle.connect('/@DBCISYS', mode = cx_Oracle.SYSDBA) as con:
        with cx_Oracle.connect('dbci/abcd1234@//oem12.vs.csin.cz:1521/INFP') as con:
            cur = con.cursor()
            try:
                if (cur.execute('SELECT GIT_COMMIT FROM DEPLOYMENT_STATUS WHERE STAGE = :lesser_env_status AND APPNAME = :appname', [lesser_env_status, appname]) != None):
                    result = cur.fetchone()
                    if result != None:
                        return jsonify(build_status='OK', git_commit = str(result[0]))
            finally:
                cur.close()
            return jsonify(build_status='NOK', error = 'Deployment to a lesser environment required but not found')
    except cx_Oracle.Error as e:
        error, = e.args
        return jsonify(build_status = 'NOK', oracle_error = 'cx_Oracle.Error', error_code = error.code, error_message = error.message)
    except:
        return jsonify(build_status = 'NOK', error = sys.exc_info()[0])

 

'''
create table db_test_windows (
    dbname varchar2(512) primary key,
    start_time varchar2(32) not null,
    end_time varchar2(32) not null
    );
'''
@app.route('/GetDelay/<string:tnsname>', methods=['GET'])
def get_delay(tnsname):
    try:
        with cx_Oracle.connect('/@DBCI') as con:
            cur = con.cursor()
            try:
                if (cur.execute('select start_time, end_time from db_test_windows where UPPER(dbname) = UPPER(:tnsname)', [tnsname]) != None) :
                    result = cur.fetchone()
                    if result != None:
                        ret_secs = compute_delay_in_secs(result[0], result[1])
                        return jsonify(delay=str(ret_secs))
            finally:
                cur.close()
        return jsonify(delay='0')
    except cx_Oracle.Error as e:
        error, = e.args
        return jsonify(delay='0', oracle_error = 'cx_Oracle.Error', error_code = error.code, error_message = error.message)
    except:
        return jsonify(delay='0', error = sys.exc_info()[0])

def compute_delay_in_secs(start_date_str, end_date_str):
    prg = pytz.timezone('Europe/Prague')
    now = prg.localize(datetime.datetime.now())
    start_date = adjust_time(now, start_date_str) 
    end_date = adjust_time(now, end_date_str)
    if end_date < start_date:
        end_date = end_date + datetime.timedelta(days=1)
    
    if start_date < now:
        if now < end_date:
            return 0
        else :
            start_date = start_date + datetime.timedelta(days=7)
    
    return int((start_date - now).total_seconds())

'''
computes test window based on current date
'''
def adjust_time(now, time_str):
    test_day, hour, minute = parse(time_str)
    ret = now
    if test_day != None:
        current_weekday = now.weekday() # 0 - 6
        ''' roll ret to permitted test day, might be in past '''
        ret = now - datetime.timedelta(days=int(current_weekday) - test_day)  
    
    ''' roll ret to available test hour and minute '''
    ret = ret.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    return ret

'''
05-18:00 is parsed to (5,18,0)
'''
def parse(strDate):
    date_components = strDate.split('-')
    if len(date_components) > 1:
        sday = int(date_components[0])
        shm = date_components[1]
    else :
        shm = date_components[0]
        sday = None
    hour, minute = shm.split(':')
    return sday, int(hour), int(minute)

@app.route('/GetConnectString/<string:dbname>', methods=['GET'])
def get_connect_json(dbname):
    return jsonify(connect_descriptor=get_connect_string(dbname))

def get_connect_string(dbname):
    with cx_Oracle.connect('/@API_VIEW') as con:
        cur = con.cursor()
        try:
            if (cur.execute('select CONNECT_DESCRIPTOR from API_DB where UPPER(DBNAME) = UPPER(:dbname)', [dbname]) != None) :
                result = cur.fetchone()
                if result != None:
                    return str(result[0])
        finally:
            cur.close()
    
    return ''

def get_api_data(dbname):
    #/dba/local/dbci/ords_certfile
    r = requests.get('https://oem12.vs.csin.cz:1528/ords/api/v1/db/{}'.format(dbname), auth=HTTPBasicAuth('dashboard', 'abcd1234'), verify='/etc/ssl/certs/ca-bundle.crt')
    if r.status_code >= 200 and r.status_code < 300:
        json_map = json.loads(r.text)
        return [str(json_map['app_name'][0]), str(json_map['env_status'])]
    return ['', '']

def get_lesser_status(env_status, dbname):
    
    app_env_statuses = None
    with cx_Oracle.connect('dashboard/abcd1234@//oem12.vs.csin.cz:1521/INFP') as con:
        cur = con.cursor()
        try:
            if (cur.execute('select distinct adb2.ENV_STATUS from API_DB adb1, API_DB adb2 where UPPER(adb1.DBNAME) = UPPER(:dbname) and adb1.APP_NAME = adb2.APP_NAME', [dbname]) != None) :
                result = cur.fetchall()
                if result != None:
                    app_env_statuses = flatten_list_of_tuples(result)
        finally:
            cur.close()
    
    if app_env_statuses != None:
        # assert env_status is in because of check in check_build
        i = statuses_enum.index(env_status)
        while i > 0:
            lesser_candidate = statuses_enum[i - 1]
            if lesser_candidate in app_env_statuses:
                return lesser_candidate
            i -= 1
        
    
    return None

def flatten_list_of_tuples(result_set):
    ret = []
    for row in result_set:
        ret.append(str(row[0]))
        
    return ret

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=6000)

