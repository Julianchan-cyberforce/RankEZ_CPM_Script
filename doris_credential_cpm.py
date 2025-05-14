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

import mysql.connector
address = request.get('address', '')
reconcileUser = request.get('reconcileAccount', '').get('account', '')
reconcilePassword = request.get('reconcileAccount', '').get('password', '')
update_user = request.get('account', '')
old_password = request.get('password', '')
update_password = request.get('newPassword', '')
port = request.get('customInfo', '').get('sysDbPort', '9030')
    
response = {'code': 0, 'errorMsg': ''}

def changePassword(user, password):
  try: 
      cnx = mysql.connector.connect(
        host=address,
        port=port,
        user=user,
        password=password,
        database="mysql"
      )
     
      # Get a cursor
      cur = cnx.cursor()
    
      # Execute a query
      cur.execute(f"set password for {update_user} = password('{update_password}');")
     
  except Exception as e:
      response = {'code': 1, 'errorMsg': str(e)}
  
  return response
    
def verify():
  try: 
      cnx = mysql.connector.connect(
          host=address,
          port=port,
          user=update_user,
          password=old_password,
          database="mysql"
      )
  
  except Exception as e:
      response = {'code': 1, 'errorMsg': str(e)}
  
  return response

def main():
    if request['action'] == 'change':
      response = changePassword(update_user, old_password)

    elif request['action'] == 'reconcile':
      response = changePassword(reconcileUser, reconcilePassword)

    elif request['action'] == 'verify':
      response = verify()

    else:
      response = {'code': 1, 'errorMsg': f"Action {request['action']} not implemented"}

    return response


# Returning a non-zero number indicates that the operation failed, and the information in the error message will be displayed on the PAC page.
rs = {'code': 0, 'errorMsg': ''}

#######################################################################################################
# Return response to CPM
if __name__ == '__main__':
  rs = main()
  if not rs:
    rs = {'code': 0, 'errorMsg': ''}
  pamutility.response(rs)
