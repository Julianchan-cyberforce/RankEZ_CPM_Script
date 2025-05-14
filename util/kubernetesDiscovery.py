#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import io
import sys
import json
import logging
import requests

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
        response = handle(request)
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
def handle(request):
    logger = logging.getLogger(__name__)
    code = 0
    error_msg = ''
    scan = None
    action = request.get('action')
    req_id = request.get('reqId')
    try:
        if action == 'discoveryK8S':
            scan, customInfo = handle_request(request)
            if not scan or len(scan) == 0:
                error_msg = 'Scan with no results.'
            logger.info('scan done.')
        else:
            code = 1
            error_msg = 'Unsupported action: %s' % action
            logger.warning(error_msg)
    except Exception as e:
        code = 1
        error_msg = str(e)
        logger.exception(e)
    response = {'code': code, 'errorMsg': error_msg}
    if code == 0 and scan:
        response['scanResult'] = scan
        response["customInfo"] = customInfo
    response["reqId"] = req_id
    return response


# Handle the request and generate the response in this method.
def handle_request(request):
    scan = None
    logger = logging.getLogger(__name__)
    address = request.get('address')
    port = str(request.get('port'))
    custom_info = request.get('customInfo', {})
    tokens = custom_info.get('tokens', []) if custom_info else []
    unDiscoveryNamespaces = custom_info.get('unDiscoveryNamespaces', []) if custom_info else []
    if len(tokens) == 0:
        raise Exception("Password is empty")
    url = "https://" + address + ":" + str(port) + "/api/v1/namespaces"
    needToDisNamespaces = unDiscoveryNamespaces
    firstDiscoveryNamespace = False
    if len(needToDisNamespaces) == 0:
        firstDiscoveryNamespace = True
        isAllFailed = True
        errorMsg = ""
        needToDisNamespaces = []
        existNamespaces = []
        for token in tokens:
            headers = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'}
            response = requests.get(url, headers=headers, verify=False)
            logger.info(response.reason)
            if response.status_code == 200:
                isAllFailed = False
                rs = response.json()
                data = rs['items']
                tokenSpaces = []
                for metadata in data:
                    if metadata['metadata']['name'] in existNamespaces:
                        continue
                    existNamespaces.append(metadata['metadata']['name'])
                    tokenSpaces.append(metadata['metadata']['name'])
                queryNamespace = {"token": token, "namespaces": tokenSpaces}
                if len(tokenSpaces) > 0:
                    needToDisNamespaces.append(queryNamespace)
            else:
                logger.info('Failed to request namespace :%s' % str(response))
                errorMsg = response.reason
        # 所有请求失败返回
        if isAllFailed:
            logger.info("Request namespace failed")
            raise Exception(errorMsg)
    disNamespaces = {}
    if len(needToDisNamespaces) > 0:
        hasFindPodsCount = 0
        removedNeedNamespace = []
        for namespace in needToDisNamespaces:
            token = namespace["token"]
            namespaces = namespace["namespaces"]
            if len(namespaces) > 0:
                isAllFailed = True
                removedNamespace = []
                for nsp in namespaces:
                    url = "https://" + address + ":" + port + "/api/v1/namespaces/" + nsp + "/pods"
                    headers = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'}
                    queryPodsRes = requests.get(url, headers=headers, verify=False)
                    pods = []
                    if queryPodsRes.status_code == 200:
                        isAllFailed = False
                        resPod = queryPodsRes.json()
                        items = resPod['items']
                        # pods
                        for item in items:
                            status = item["status"]["phase"]
                            containers = item["spec"]["containers"]
                            if len(containers) == 0:
                                continue
                            hasFindPodsCount = hasFindPodsCount + len(containers)
                            resContainers = []
                            # containers
                            for cont in containers:
                                resContainer = {"name": cont["name"], "image": cont["image"]}
                                resContainers.append(resContainer)
                            podIp = ""
                            nodeName = ""
                            if ("podIP" in item["status"]):
                                podIp = item["status"]["podIP"]
                            if ("nodeName" in item["spec"]):
                                nodeName = item["spec"]["nodeName"]
                            pod = {"podName": item["metadata"]["name"], "podIp": podIp,
                                   "status": status, "desc": item,
                                   "node": nodeName,
                                   "containers": resContainers}
                            pods.append(pod)
                    else:
                        logger.info('Failed to request pods :%s' % str(queryPodsRes))
                    disNamespaces[nsp] = pods
                    removedNamespace.append(nsp)
                    if len(namespaces) == len(removedNamespace):
                        removedNeedNamespace.append(namespace)
                    if hasFindPodsCount > 1000:
                        for re in removedNamespace:
                            namespaces.remove(re)
                        break
                # 所有请求失败返回
                if isAllFailed:
                    logger.info("Request pods failed")
                    return None, None
        for removeSpace in removedNeedNamespace:
            needToDisNamespaces.remove(removeSpace)
        scan = [disNamespaces]
    else:
        # 没有需要发现的namespace
        return None, None
    customInfo = {"firstDiscoveryNamespace": firstDiscoveryNamespace, "unDiscoveryNamespaces": needToDisNamespaces}
    return scan, customInfo


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
