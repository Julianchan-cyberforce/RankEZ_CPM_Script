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
    request = {
        "reqId": 1,  # Request ID
        "action": "change",  # Action: verify/change/reconcile
        "address": "127.0.0.1",  # Address of the target device
        "port": 22,  # The port configured on the CPM plugin.
        "protocol": "ssh",  # Access protocol, such as ssh, rdp, etc.
        "account": "test",  # Target account that need to be verified or changed or reconciled.
        "password": "111111",  # Old password
        "newPassword": "123123"  # New password, used when changing or reconciling.
    }

logger.info("Start CPM task")
if request['action'] == 'discovery':
    logger.info(request)


# Returning a non-zero number indicates that the operation failed, and the information in the error message will be displayed on the PAC page.
rs = {'code': 0, 'errorMsg': ''}

#######################################################################################################
# Return response to CPM
pamutility.response(rs)