#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import io
import sys
import json
import logging

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Standard format for formal environments, modification is not recommended.
def main():
    # Initialize the logger
    arg_length = len(sys.argv)
    log_path = '/var/pluginlog/'
    if not os.path.exists(log_path):
        os.makedirs(log_path, 0o755)
    filename = 'plugin' if arg_length == 0 else sys.argv[arg_length - 1]
    logging.basicConfig(level=logging.INFO, format='%(asctime)s pid=%(process)d %(levelname)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S', filename=log_path + filename + '-console.log')
    logger = logging.getLogger(__name__)

    try:
        # Load request
        sys.stdin.buffer.read(4)
        len_bytes = sys.stdin.buffer.read(4)
        req_len = int.from_bytes(len_bytes, byteorder='big', signed=True)
        params = sys.stdin.buffer.read(req_len).decode('utf-8')
        request = json.loads(params)
        # Handle request
        response = handle_request(request)
    except Exception as e:
        logger.exception(e)
        response = {'code': 1, 'errorMsg': 'Error: %s' % str(e)}

    # Send response
    res_str = json.dumps(response, ensure_ascii=False)
    res_len = len(res_str.encode(encoding='utf-8'))
    sys.stdout.flush()
    sys.stdout.write('BAFA')
    sys.stdout.flush()
    sys.stdout.buffer.write(res_len.to_bytes(4, byteorder='big', signed=True))
    sys.stdout.write(res_str)
    sys.stdout.flush()


# Handle the request and generate the response in this method.
def handle_request(request):
    import requests
    from requests.auth import HTTPBasicAuth
    import base64
    from hashlib import sha256, sha1, md5

    logger = logging.getLogger(__name__)

    ##################################
    #    Implement custom process    #
    ##################################

    # Generate response data and return.
    # The code is 0 for success and the other for failure.
    # The errorMsg will be displayed on the page when the code is not 0.
    address = request.get('address', '')
    reconcileUser = request.get('reconcileAccount', '').get('account', '')
    reconcilePassword = request.get('reconcileAccount', '').get('password', '')
    update_user = request.get('account', '')
    old_password = request.get('password', '')
    update_password = request.get('newPassword', '')

    def changePassword(user, password):
      response = {'code': 0, 'errorMsg': ''}

      # Construct the get and put URL
      url = f"{address}/api/users/{update_user}"

      # Make the API request to get tags before put
      getResults = requests.get(url, auth=HTTPBasicAuth(user, password))

      response_data = getResults.json()

      # Handle error between 400-599
      if getResults.status_code >= 400:
        response['code'] = getResults.status_code
        response['errorMsg'] = f"{address}/api/users/{update_user} error: {getResults.status_code} - {response_data['reason']}"
        return response
      
      # Parse the response data, get tags
      tags = response_data['tags']

      putData = {"password": update_password, "tags": tags}

      putResults = requests.put(url, data=json.dumps(putData), auth=HTTPBasicAuth(user, password))

      if putResults.status_code >= 400:
        response['code'] = putResults.status_code
        response['errorMsg'] = f"{address}/api/users/{update_user} error: {putResults.status_code} - {response_data['reason']}"
        return response
      
      return {'code': 0, 'errorMsg': ''}
    
    def verify():
      response = {'code': 0, 'errorMsg': ''}

      # Construct the get and put URL
      url = f"{address}/api/users/{update_user}"

      # Make the API request to get tags before put
      result = requests.get(url, auth=HTTPBasicAuth(reconcileUser, reconcilePassword))
      response_data = result.json()

      # Handle error between 400-599
      if result.status_code >= 400:
        response['code'] = result.status_code
        response['errorMsg'] = f"{address}/api/users/{update_user} error: {result.status_code} - {response_data['reason']}"
        return response

      password_hash = base64.b64decode(response_data['password_hash'])
      hashing_algorithm = response_data['hashing_algorithm']

      salted_password = password_hash.hex()[0:8]+ old_password.encode('utf-8').hex()

      if 'sha256' in hashing_algorithm:
        if (password_hash.hex()[0:8] + sha256(bytes.fromhex(salted_password)).hexdigest()) == password_hash.hex():
          return {'code': 0, 'errorMsg': ''}
        else:
          return {'code': 1, 'errorMsg': 'Wrong password.'}
        
      elif 'sha1' in hashing_algorithm:
        if (password_hash.hex()[0:8] + sha1(bytes.fromhex(salted_password)).hexdigest()) == password_hash.hex():
          return {'code': 0, 'errorMsg': ''}
        else:
          return {'code': 1, 'errorMsg': 'Wrong password.'}
        
      elif 'md5' in hashing_algorithm:
        if (password_hash.hex()[0:8] + md5(bytes.fromhex(salted_password)).hexdigest()) == password_hash.hex():
          return {'code': 0, 'errorMsg': ''}
        else:
          return {'code': 1, 'errorMsg': 'Wrong password.'}
      
      else:
        return {'code': 2, 'errorMsg': f"Does not support {hashing_algorithm}."}

    if request['action'] == 'change':
      response = changePassword(update_user, old_password)

    elif request['action'] == 'reconcile':
      response = changePassword(reconcileUser, reconcilePassword)

    elif request['action'] == 'verify':
      response = verify()
    
    else:
      response = {'code': 1, 'errorMsg': f"Action {request['action']} not implemented"}
    
    return response

if __name__ == '__main__':
    # If you need to debug the script on the remoteapp server, set the flag to "True".
    # In formal environments, this flag should be set to "False".
    istest = False
    if not istest:
        main()
    else:
        # test
        request = {
            "reqId": 1,                 # Request ID
            "action": "change",         # Action: verify/change/reconcile
            "address": "127.0.0.1",     # Address of the target device
            "port": 22,                 # The port configured on the CPM plugin.
            "protocol": "ssh",          # Access protocol, such as ssh, rdp, etc.
            "account": "test",          # Target account that need to be verified or changed or reconciled.
            "password": "111111",       # Old password
            "newPassword": "123123"     # New password, used when changing or reconciling.
        }
        response = handle_request(request)
        print(response)
