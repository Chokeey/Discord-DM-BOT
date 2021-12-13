import asyncio
import logging
import os
import signal
import sys
import threading
import time

import argparse
from logging.handlers import QueueHandler

from ChokeBotManagerMrk3 import ChokeBotManager
from pymongo import MongoClient
from pymongo import ASCENDING
from pymongo import errors
from pprint import pprint
from sys import platform
import random
import json

import atexit

from gui import BotGui

if platform == "win32":
    policy = asyncio.WindowsSelectorEventLoopPolicy()
    asyncio.set_event_loop_policy(policy)

config = {}
tokens = {}
ids = {}
proxies = {}
invites = {}
preferredProxies = {}
loadedInvites = []
proxyUser = "geonode_94xDyQbtzA"
proxyPass = "abbdd564-a554-4a2d-9528-63af746c1bc2"
#proxyUser = "Selzacharye9"
#proxyPass = "S4e3BsQ"
inviteMode = False
dataUpdateThread = None
botRunnerThread = None
minimalInvitesToStart = False
gui = BotGui()
logger = logging.getLogger("main")
consoleQueueHandler = QueueHandler(gui.dmListQueue)
logQueueHandler = QueueHandler(gui.logListQueue)

class consoleLogger:
    def write(self, txt):
        gui.pushToNotificationQueue(txt)

class logLogger:
    def write(self, txt):
        gui.pushToLogQueue(txt)


oldout = sys.stdout
olderr = sys.stderr

sys.stdout = consoleLogger()
sys.stderr = logLogger()

# Configure logging to show the name of the thread
# where the log message originates.
logging.basicConfig(
    level=logging.INFO,
    format='%(threadName)10s %(name)18s: %(message)s',
    stream=sys.stderr,
)

with open('config.json') as f:
    config = json.load(f)

proxyUser = config["proxyuser"]
proxyPass = config["proxypass"]

def exit_handler():
    print("Updating database...")
    for key in tokens:
        result = db.tokens.update_one({"token":key},
                          {"$set": {"alive": tokens[key]}},
                          upsert=True)
        
    for key in ids:
        result = db.ids.update_one({"userid": key},
                          {"$set": {"messaged": ids[key]}},
                          upsert=True)

    for key in invites:
        result = db.invites.update_one({"code": key},
                          {"$set": {"tokens": invites[key]}},
                          upsert=True)

    for key in preferredProxies:
        result = db.preferredProxies.update_one({"token": key},
                          {"$set": {"proxy": preferredProxies[key]}},
                          upsert=True)
    print("Database updated!")


def data_update(secs):
    asyncio.set_event_loop(asyncio.new_event_loop())
    while True:
        exit_handler()
        time.sleep(secs)


def runInvites():
    asyncio.set_event_loop(asyncio.new_event_loop())
    global minimalInvitesToStart
    if inviteMode:
        viableBots = 0
        from DiscordInviter import Invite

        if args["invite"]:
            loadedInvites.append(args["invite"])
        for code in loadedInvites:
            if code not in invites:
                invites[code] = []

            for tok in tokens:
                if len(tokens) > 0:
                    if tok in tokens:
                        if tokens[tok] is False:
                            continue

                if len(invites) > 0:
                    if code in invites:
                        if tok in invites[code]:
                            viableBots += 1
                            if config["threads"] and viableBots >= config["threads"]:
                                break
                            else:
                                continue

                loopNext = True
                while loopNext:
                    try:
                        GEONODE_DNS = random.choice(list(proxies.keys()))
                        if tok in preferredProxies:
                            GEONODE_DNS = preferredProxies[tok]
                        proxy = {"https": "http://{}:{}@{}".format(proxyUser, proxyPass, GEONODE_DNS)}
                        status = Invite(tok, code, proxy)
                        pprint("Invited token {} with code {}".format(tok, code))
                        if status == 407:
                            loopNext = True
                        elif status == 401 or status == 403:
                            tokens[tok] = False
                            loopNext = False
                        else:
                            loopNext = False
                            if tok not in invites[code]:
                                invites[code].append(tok)
                            if tok not in preferredProxies:
                                preferredProxies[tok] = GEONODE_DNS

                            #minimalInvitesToStart = True
                    except Exception as e:
                        logger.error(e)

                time.sleep(random.uniform(5, 7))

        minimalInvitesToStart = True


def runBots():
    while True:
        if not minimalInvitesToStart:
            time.sleep(1)
            continue

        asyncio.set_event_loop(asyncio.new_event_loop())

        try:
            manager = ChokeBotManager(tokens, ids, proxies, preferredProxies, config,
                                      {"user": proxyUser, "pass": proxyPass})

            threadCount = config["threads"]
            if not threadCount or threadCount <= 0:
                threadCount = 10

            manager.start(threadCount)
            exit_handler()
            while True:
                try:
                    time.sleep(1)
                except:
                    break
        except Exception as e:
            logger.error(e)
        break


atexit.register(exit_handler)

parser = argparse.ArgumentParser(description='ChokeBot')
parser.add_argument('-i', '--invite', help='Invite all tokens to this guild', required=False)
args = vars(parser.parse_args())

mongoclient = MongoClient("mongodb://localhost:27017")
db = mongoclient.chokebot
try:
    db.tokens.create_index([("token", ASCENDING)], unique=True)
    db.ids.create_index([("userid", ASCENDING)], unique=True)
except errors.OperationFailure:
    pass

result = db.tokens.find({})
for row in result:
    tokens[row.get("token")] = row.get("alive")
    
result = db.ids.find({})
for row in result:
    ids[row.get("userid")] = row.get("messaged")

result = db.invites.find({})
for row in result:
    invites[row.get("code")] = row.get("tokens")

with open("tokens.txt", "r") as f:
    lines = f.readlines()
    for line in lines:
        if line == '\n':
            continue
        line = line.strip()
        token = ""
        if config["tokenFileFormat"] == "tokenonly":
            token = line
        elif config["tokenFileFormat"] == "tokenandlogin":
            token = line.split(";")[1]
        else:
            raise Exception("Invalid token file format.")

        if token not in tokens:
            tokens[token] = True

with open("ids.txt", "r") as f:
    lines = f.readlines()
    for line in lines:
        if line == '\n':
            continue
        if "invite:" in line:
            loadedInvites = line.split(":")[1].strip().split(",")
        elif line not in ids:
            ids[line.strip()] = False

with open("proxies.txt", "r") as f:
    lines = f.readlines()
    for line in lines:
        if line == '\n':
            continue
        proxies[line.strip()] = True

if args["invite"] and len(args["invite"]) > 0:
    inviteMode = True

if len(loadedInvites):
    inviteMode = True

if config["dataUpdateFrequency"] and config["dataUpdateFrequency"] > 0:
    dataUpdateThread = threading.Thread(target=data_update, args=(config["dataUpdateFrequency"],))
    dataUpdateThread.start()

botRunnerThread = threading.Thread(target=runBots, name="BotRunnerThread")
botRunnerThread.start()
minimalInvitesToStart = True

inviteRunnerThread = threading.Thread(target=runInvites, name="InviteRunnerThread")
#inviteRunnerThread.start()

gui.run()
exit_handler()
os.kill(os.getpid(), signal.CTRL_C_EVENT)
