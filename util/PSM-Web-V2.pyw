#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
import sys, os, logging, time,shutil, win32api

# Init plugin environment, DO NOT modify anything except debug level
# The script must be placed in <RemoteApp Path>\plugins\psm\cus folder
bin_path = os.path.join(os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..\\..")), 'bin')
sys.path.append(bin_path)
import pamutility
from DrissionPage import ChromiumOptions, ChromiumPage
from DrissionPage.errors import *
from DrissionPage.common import Settings
import traceback
import re
import threading
import random
import uuid

logger, request, isTest = pamutility.init(os.path.realpath(__file__), loglevel=logging.DEBUG)
#######################################################################################################
# When debugging, please manually set the request dictionary below and run the script with "python <YourScript.py>"
# The debug log will be named <YourScript.py>.log and stored in the same directory as the script.

def download_file_process(page, download_path, logger, request):
    copied_files = []
    try:
        pamutility.addMapDrive(logger)
        while True:
            if page.states.is_alive:
                # Auto save downloaded file to \\tsclient\Z for HTML5 connection
                if request["clientType"] == "HTML5":
                    for root, dirs, files in os.walk(download_path):
                        for file in files:
                            if not file.endswith(".tmp") and not file.endswith(".crdownload"):
                                src_path = os.path.join(root, file)
                                dst_path = os.path.join("\\\\tsclient\\Z\\", file)
                                logger.debug("Moving downloaded file" + file)
                                try:
                                    if src_path not in copied_files:
                                        shutil.copyfile(src_path, dst_path)
                                        copied_files.append(src_path)
                                except Exception as e:
                                    logger.debug(f"Failed to move file {src_path}, will retry later. Error: {e}")

                                logger.debug("Delete downloaded file which is moved" + file)
                                try:
                                    os.remove(src_path)
                                    copied_files.remove(src_path)
                                except Exception as e:
                                    logger.debug(f"Failed to remove file {src_path}, will retry later. Error: {e}")
                time.sleep(2)
            else:
                logger.info('Browser window closed')
                os._exit(0)
    except Exception as e:
        logger.error(f"Unexpected error in clean_files: {e}")
        traceback.print_exc()

if isTest:
    request = {
        "address": "",
        "account": "",
        "password": "",
        "customInfo": {
            "sysURL": "http://192.168.1.231:8000"
        },
        "webProperties": {
            'accountXPath':'//*[@id="account"]',
            'passwordXPath':'//*[@id="password"]',
            'submitXPath':'//*[@id="btnLogon"]',
            'webFrame':''
        },
        "pluginCustomProperties": {
            "browserPath": r"C:\Program Files\Google\Chrome\Application\Chrome.exe",
            "arguments": [
                "disable-infobars",
                "--disable-notifications",
                '--lang=en-US',
                '--ignore-certificate-errors',
                '--disable-component-update',
                '--start-maximized',
                '--hide-crash-restore-bubble'
            ]
        },
        "clientType": "mstsc" #or HTML5
    }

logger.debug("Start PSM task")
try:
    url = ""
    if 'sysURL' in request['customInfo']:
        url = request['customInfo']['sysURL']
    if (url is None or url == "") and 'accessUrl' in request['webProperties']:
        logger.debug("sysURL is not set, use accessUrl instead")
        url = request["webProperties"]["accessUrl"]
    logger.debug("url:" + url)
    password = str(request['password'])
    username = str(request['account'])
    # logger.debug("request:" + str(request))
    logger.debug("username:" + username)
    Settings.cdp_timeout = 1500

    # Init chrome
    #co = ChromiumOptions(read_file=False)
    guid = uuid.uuid4()
    seed = guid.int
    random.seed(seed)
    Start=random.randint(9600,19599)
    End=random.randint(Start,19600)
    co = ChromiumOptions(read_file=False).auto_port(True,None,[Start,End])
    try:
        browserPath = request['pluginCustomProperties']['browserPath']
        logger.debug("Set browserPath:" + browserPath)
        co.set_browser_path(browserPath)
    except:
        logger.warning("Failed to set browserPath, use default setting")
    co.incognito()
    co.headless(False)
    co.set_pref('credentials_enable_service', False)  # Disable save password prompt
    #co.auto_port(True)  # Auto create user profile folder

    if 'arguments' in request['pluginCustomProperties']:
        for arg in request['pluginCustomProperties']['arguments']:
            logger.debug("Add chrome argument:" + arg)
            co.set_argument(arg)

    # Change default download folder and clean files for HTML5 connection
    if request["clientType"] == "HTML5":
        logger.debug("Change default download folder and clean files for HTML5 connection")
        download_path = os.path.join(os.path.expanduser("~"),"Downloads")
        co.set_download_path(download_path)
        

    accountXPath = request["webProperties"]['accountXPath']
    logger.debug("accountXPath" + accountXPath)
    passwordXPath = request["webProperties"]['passwordXPath']
    logger.debug("passwordXPath" + passwordXPath)
    submitXPath = request["webProperties"]['submitXPath']
    logger.debug("submitXPath" + submitXPath)

    page = ChromiumPage(co)
    try:
        logger.debug("Go to URL")
        logger.debug("Current Chrome port is: "+co._address)
        page.get(url)
        
        # run clean_files in a new thread
        download_path = os.path.join(os.path.expanduser("~"), "Downloads")
        download_file_thread = threading.Thread(target=download_file_process, args=(page, download_path, logger, request))
        download_file_thread.start()
        page.wait(2)
        if not username or username == 'None' or accountXPath == 'None':
            logger.error("Username or accountXPath is empty, skip inputing username steps.")
        else:
            logger.debug("Try to input username")
            usernameElement=page.ele('xpath:' + accountXPath)
            page.wait.ele_displayed(usernameElement)
            usernameElement.input(username)

        if not password or password == 'None' or passwordXPath == 'None':
            logger.debug("Password or passwordXPath is empty, skip inputing password steps.")
        else:
            logger.debug("Try to input password")
            passwordElement=page.ele('xpath:' + passwordXPath)
            page.wait.ele_displayed(passwordElement)
            passwordElement.input(password)

        if submitXPath == 'None':
            logger.debug("SubmitXPath is empty, skip inputing password steps.")
        else:
            logger.debug("Try to click submit button")
            loginbuttonElement=page.ele('xpath:' + submitXPath)
            page.wait.ele_displayed(loginbuttonElement)
            loginbuttonElement.click()
    except Exception as e:
        logger.error("Failed to open web page, error:" + str(e))
        traceErr = traceback.format_exc()
        logger.debug(traceErr)
        if not isinstance(e, ElementNotFoundError):
            page.quit()
except Exception as e:
    logger.exception(str(e))

