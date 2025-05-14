# -*- coding: utf-8 -*-
import sys, os, logging

# Init plugin environment, DO NOT modify anything except debug level
# The script must be placed in <RemoteApp Path>\plugins\cpm\cus folder
bin_path = os.path.join(os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..\\..")), 'bin')
sys.path.append(bin_path)
import pamutility

logger, request, isTest = pamutility.init(os.path.realpath(__file__), loglevel=logging.DEBUG)
#######################################################################################################
# When debugging, please manually set the request dictionary below and run the script with "python <YourScript.py>"
# The debug log will be named <YourScript.py>.log and stored in the same directory as the script.
if isTest:

  request2 = {'protocol': 'remoteapp', 'address': '10.1.20.141', 'port': None, 'action': 'reconcile', 'newPassword': 'CPb87o&3`HyC', 'pluginData': {}, 'customInfo': {'sysDbPort': 27017, 'database': 'hello'}, 'processor': 'RemoteAppProcessor', 'timeout': 30, 'account': 'user1', 'reconcileAccount': {'password': 'Cyberport1', 'address': '10.1.20.141', 'customInfo': {'sysDbPort': 27017, 'database': 'hello'}, 'account': 'helloAdmin'}, 'reqId': 95}
  request = {'address': '10.1.20.141', 'newPassword': '12345678', 'customInfo': {'sysDbPort': 27017, 'database': 'hello'}, 'processor': 'RemoteAppProcessor', 'timeout': 30, 'reqId': 96, 'protocol': 'remoteapp', 'password': '12345678', 'port': None, 'action': 'change', 'pluginData': {}, 'account': 'user1', 'reconcileAccount': {'password': 'Cyberport1', 'address': '10.1.20.141', 'customInfo': {'sysDbPort': 27017, 'database': 'hello'}, 'account': 'helloAdmin'}}
  request3 = {'protocol': 'remoteapp', 'password': '123456', 'address': '10.1.20.141', 'port': None, 'action': 'verify', 'pluginData': {}, 'customInfo': {'sysDbPort': 27017, 'database': 'hello'}, 'processor': 'RemoteAppProcessor', 'timeout': 30, 'account': 'user1', 'reconcileAccount': {'password': 'Cyberport1', 'address': '10.1.20.141', 'customInfo': {'sysDbPort': 27017, 'database': 'hello'}, 'account': 'helloAdmin'}, 'reqId': 97}

logger.info("Start CPM task")

import subprocess
import urllib.parse

address = request['address']
port = request['customInfo']['sysDbPort']
database = request['customInfo']['database']

def main():
  if request['action'] == 'change':
    # Login user, translate accord to above table
    user = urllib.parse.quote(request['account'], safe="")
    password = urllib.parse.quote(request['password'], safe="")

    # Information to be updated
    new_password = request['newPassword']

    # Generate the connection URI
    mongosh_uri = f'"C:\\Program Files\\mongosh\\mongosh.exe" mongodb://{user}:{password}@{address}:{port}/{database}?tls=true^&tlsAllowInvalidCertificates=true'
    rs = changePassword(mongosh_uri, user, new_password)
    return rs

  elif request['action'] == 'reconcile':
    # Login user, translate accord to above table
    user = urllib.parse.quote(request['reconcileAccount']['account'], safe="")
    password = urllib.parse.quote(request['reconcileAccount']['password'], safe="")

    # Information to be updated
    update_user = request['account']
    new_password = request['newPassword']
  
    # Generate the connection URI
    mongosh_uri = f'"C:\\Program Files\\mongosh\\mongosh.exe" mongodb://{user}:{password}@{address}:{port}/{database}?tls=true^&tlsAllowInvalidCertificates=true'
    rs = changePassword(mongosh_uri, update_user, new_password)
    return rs
  
  elif request['action'] == 'verify':
    # Login user, translate accord to above table
    user = urllib.parse.quote(request['account'])
    password = request['password']

    mongosh_uri = f'"C:\\Program Files\\mongosh\\mongosh.exe" mongodb://{user}:{urllib.parse.quote(password, safe="")}@{address}:{port}/{database}?tls=true^&tlsAllowInvalidCertificates=true'

    logger.info(mongosh_uri)

    rs = verify(mongosh_uri, user, password)
    return rs
  else:
    rs = {'code': 1, 'errorMsg': f'Action {request["action"]} not implemented'}
    return rs

def changePassword(mongosh_uri, user, new_password):
  # Add the query using --eval
  query = f"db.updateUser('{user}', {{pwd: '{new_password}'}})"

  # Final command
  mongosh_command = f'{mongosh_uri} --eval "{query}"'

  logger.info(mongosh_command)

  # Run the command
  process = subprocess.Popen(
      mongosh_command,
      shell=True,
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE,
      text=True
  )

  # Get the output
  stdout, stderr = process.communicate()
  if stderr:
    rs = {'code': 2, 'errorMsg': stderr}
    return rs

def verify(mongosh_uri, user, password):
  # Add the query using --eval
  query = f"db.auth('{user}', '{password}')"

  # Final command
  mongosh_command = f'{mongosh_uri} --eval "{query}"'

  logger.info(mongosh_command)

  # Run the command
  process = subprocess.Popen(
      mongosh_command,
      shell=True,
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE,
      text=True
  )

  # Get the output
  stdout, stderr = process.communicate()
  if stderr:
    rs = {'code': 2, 'errorMsg': stderr}
    return rs


# Returning a non-zero number indicates that the operation failed, and the information in the error message will be displayed on the PAC page.
rs = {'code': 0, 'errorMsg': ''}

#######################################################################################################
# Return response to CPM
if __name__ == '__main__':
  rs = main()
  if not rs:
    rs = {'code': 0, 'errorMsg': ''}
  pamutility.response(rs)
