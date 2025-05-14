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
    response = {'code': 0, 'errorMsg': ''}

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
