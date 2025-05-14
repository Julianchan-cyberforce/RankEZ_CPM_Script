# -*- coding: utf-8 -*-
import sys, logging, time, os, base64, win32wnet, win32api, json, io
 
###############################################################################################
def init(script_path, loglevel=logging.DEBUG):
    log_path = os.path.join(os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..\\..")), 'logs')
    request = None
    isTest = True
    # Product run
    if len(sys.argv) == 3:
        isTest = False
        log_file_str = base64.b64decode(sys.argv[1]).decode('utf-8')
        log_file = "".join(i for i in log_file_str if i not in r'\/:*?"<>|')
        plugin_type = sys.argv[2]
        log_path = os.path.join(log_path, "psm") if plugin_type == "psm" else os.path.join(log_path, "cpm")
        logger = get_logger(os.path.join(log_path, log_file), loglevel)
        try:
            # Disable stdin/stdout
            nulstd = open('nul', 'w')
            sys.stdout = nulstd
            sys.stderr = nulstd
            # Load request
            sys.stdin.buffer.read(4)
            len_bytes = sys.stdin.buffer.read(4)
            req_len = int.from_bytes(len_bytes, byteorder='big', signed=True)
            source_req_bytes = sys.stdin.buffer.read(req_len)
            req_bytes = source_req_bytes
            if plugin_type == "psm":
                req_bytes = base64.b64decode(source_req_bytes)
            request = json.loads(req_bytes)
        except Exception as e:
            logger.exception(e)
    # Test run
    else:
        logger = get_logger(script_path + ".log", loglevel, attach_con=True)
    return logger, request, isTest
 
###############################################################################################
def response(res):
    # Recover stdout/stderr , CPM will read output to determine script status, DO NOT print/write anything to std pipe after that!!
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    # Send response
    res_str = json.dumps(res, ensure_ascii=False)
    res_len = len(res_str.encode(encoding='utf-8'))
    sys.stdout.flush()
    sys.stdout.write('BAFA')
    sys.stdout.flush()
    sys.stdout.buffer.write(res_len.to_bytes(4, byteorder='big', signed=True))
    sys.stdout.write(res_str)
    sys.stdout.flush()
 
###############################################################################################
def get_logger(logfilename, loglevel, filemode='a', attach_con=False):
    logger = logging.getLogger("pam")
    logger.setLevel(loglevel)
    file_handler = logging.FileHandler(logfilename, mode=filemode, encoding='utf-8')
    file_handler.setLevel(loglevel)
    file_handler.setFormatter(logging.Formatter('[%(asctime)s] [line:%(lineno)d] [%(levelname)s] %(message)s'))
    logger.addHandler(file_handler)
    if attach_con:
        console = logging.StreamHandler()
        console.setLevel(loglevel)
        logger.addHandler(console)
    return logger
 
###############################################################################################
RESOURCE_CONNECTED = 0x00000001
RESOURCETYPE_DISK = 0x00000001
RESOURCE_REMEMBERED = 0x00000003
def findUnusedDriveLetter(logger):
    unusedDriveLetter = []
    existing = [x[0].lower() for x in win32api.GetLogicalDriveStrings().split("\0") if x]
    handle = win32wnet.WNetOpenEnum(RESOURCE_REMEMBERED, RESOURCETYPE_DISK, 0, None)
    try:
        while 1:
            items = win32wnet.WNetEnumResource(handle, 0)
            #for item in items:
                #logger.debug("Attempting remove connection of"+item.lpLocalName+"to"+item.lpRemoteName+" with "+str(item.dwType))
                #win32wnet.WNetCancelConnection2(item.lpRemoteName,item.dwType,True)
            if len(items) == 0:
                break
            xtra = [i.lpLocalName[0].lower() for i in items if i.lpLocalName]
            existing.extend(xtra)
    except Exception as e:
        logger.error("Failed to list existing driver letters, error=" + str(e))
    finally:
        handle.Close()
    logger.debug("Existing Driver letters:" + ','.join(existing))
    for driveLetter in "defghijklmnopqrstuvwxyz":
        if driveLetter not in existing:
            unusedDriveLetter.append(driveLetter)
    unusedDriveLetter.sort(reverse=True)
    return unusedDriveLetter
 
###############################################################################################
def addMapDrive(logger,max_retries=5, wait_time=10):
    retries = 0
    unusedDriveLetter = findUnusedDriveLetter(logger)
    mappedDriverList= []
     
    while retries < max_retries:
        try:
            handle = win32wnet.WNetOpenEnum(RESOURCE_CONNECTED, RESOURCETYPE_DISK, 0, None)
            if handle == 0:
                logger.debug("Failed to open resource enumeration")
            else:
                items = win32wnet.WNetEnumResource(handle, 64)
                if len(items) != 0:
                    for item in items:
                        logger.debug('local name:{0}, remote name:{1}, provider name:{2}'.format(item.lpLocalName, item.lpRemoteName, item.lpProvider))
                        if item.lpRemoteName not in mappedDriverList:
                            localName = unusedDriveLetter.pop(0) + ":"
                            logger.debug("Attempting connection of"+localName+"to"+item.lpRemoteName+" with "+str(item.dwType))
                            win32wnet.WNetAddConnection2(item.dwType, localName, item.lpRemoteName)
                            mappedDriverList.append(item.lpRemoteName)
            time.sleep(wait_time)
            retries += 1
        finally:
            handle.Close()