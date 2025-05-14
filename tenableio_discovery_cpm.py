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
    logger = logging.getLogger(__name__)

    ##################################
    #    Implement custom process    #
    ##################################

    # Generate response data and return.
    # The code is 0 for success and the other for failure.
    # The errorMsg will be displayed on the page when the code is not 0.
    import requests
    from datetime import datetime
    import copy

    true = True
    false = False
    null = None

    # Initialize response
    response = {"code": 0, "errorMsg": "", "reqId": request["reqId"], "scanResult": []}

    # Construct the URL, by default should be this
    url = "https://cloud.tenable.com/users"

    try:
        x_apikeys = request["pluginData"]['properties']["x_apikeys"]
    except KeyError as e:
        response["code"] = 2
        response["errorMsg"] = str(e) + ' ' + str(request)
        return response
    
    try:
        # Make the API request
        results = requests.get(url, headers={"X-ApiKeys": x_apikeys})

        # Parse the response data
        response_data = results.json()

        logger.info(str(response_data))

        # Handle error between 400-599
        if results.status_code >= 400:
          response["code"] = results.status_code
          response["errorMsg"] = f"{url} error: {results.status_code} - {response_data['reason']}"
          return response

        # Define the scan result template
        scanResultTemplate = {
            "account": "",
            "type": "local",
            "description": "",
            "uid": "",
            "gid": "",
            "enabled": true,
            "createdTime": 0,
            "lastPasswordSetTime": 0,
            "passwordNeverExpires": true,
            "passwordExpirationTime": 0,
            "pwdChangeable": false,
            "lastLogonTime": 0,
            "lastLogonAddress": "",
            "lockedTime": null,
            "isLocked": false,
            "groups": "root",
            "privileged": false,
            "devTypeAccountAttrs": {}
        }

        # Populate the scan results
        for result in response_data["users"]:
            scan_result = copy.deepcopy(scanResultTemplate)
            scan_result.update({
                "account": result["username"],
            })
            if result["permissions"] == 64:
                scan_result.update({
                  "privileged": true  
                })

            # lastLogonTime = datetime.strptime(result["lastlogin"], "%Y-%m-%dT%H:%M:%S.%f").timestamp()

            # lastLogonTime = datetime.fromisoformat(result["lastLoginTime"]).timestamp()
            # createdTime = datetime.fromisoformat(result["created"]).timestamp()

            # datetime.timestamp returns a float - the number of seconds since epoch 
            # as the integer part and microseconds and the fraction.
            # lastLogonTime = int(lastLogonTime * 1000)

            scan_result.update({
                "lastLogonTime": result.get("lastlogin", 0)
            })

            response["scanResult"].append(scan_result)
    
    except Exception as e:
        response["code"] = 1
        response["errorMsg"] = str(e)
        return response

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
