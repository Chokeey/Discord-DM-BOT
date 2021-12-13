import asyncio
import concurrent.futures
import logging
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

import aiohttp
from urllib3.exceptions import ProxyError

from ChokeBotMrk3 import ChokeBot
from discord import errors

from pprint import pprint

from aiohttp import BasicAuth


def writeToAcquires(line):
    with open("acquire.log", "a+") as f:
        f.write(line)
        f.write("\n")


def writeToAttempts(line):
    with open("attempts.log", "a+") as f:
        f.write(line)
        f.write("\n")


class ChokeBotManager:

    def __init__(self, tokens, ids, proxies, preferredProxies, config, proxyLogin):
        self.tokens = tokens
        self.ids = ids
        self.idsList = [
            key
            for key in self.ids
        ]
        self.proxies = proxies
        self.preferredProxies = preferredProxies
        self.proxyLogin = proxyLogin
        self.config = config
        self.botRunnerTasks = []
        self.bots = []
        self.tokensInUse = []
        self.spliceIndex = 0
        self.spliceAmount = config["dmPerBot"] if config["dmPerBot"] else 100
        self.ppe: ThreadPoolExecutor = None
        self.loop: asyncio.AbstractEventLoop = None
        self.threadCount = 0
        self.lock = Lock()

    def start(self, count):
        self.loop = asyncio.get_event_loop()
        self.threadCount = count
        try:
            self.botRunner()
        except Exception as e:
            pass
        finally:
            pass

    def genToken(self):
        token = ""
        for key in self.tokens:
            if self.tokens[key] is True and key not in self.tokensInUse:
                token = key
                self.tokensInUse.append(key)
                break
        return token

    def genBot(self, token):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        log = logging.getLogger('genBot')
        log.info('running')
        basic_auth = BasicAuth(self.proxyLogin["user"], self.proxyLogin["pass"])
        proxy = random.choice(list(self.proxies.keys()))
        if token in self.preferredProxies:
            proxy = self.preferredProxies[token]
        else:
            self.preferredProxies[token] = proxy

        client = None
        try:
            client = ChokeBot(proxy="http://" + proxy, proxy_auth=basic_auth)
            client.configure(token, self)
            pprint("Attempt to run bot:{}\n".format(token))
            self.bots.append(client)
            client.run(token)
        except errors.HTTPException and errors.LoginFailure as e:
            self.tokens[token] = False
            log.error(e)
        except aiohttp.ServerDisconnectedError as e:
            log.error(e)
        except ProxyError as e:
            log.error(e)
        except Exception as e:
            log.error(e)
        finally:
            self.bots.remove(client)

    def genId(self):
        if len(self.idsList) <= 0:
            return

        with self.lock:
            userId = None
            while userId is None:
                if self.spliceIndex >= len(self.idsList):
                    return

                temp = self.idsList[self.spliceIndex]
                self.spliceIndex += 1
                if self.ids[temp]:
                    continue
                else:
                    userId = temp

        return userId

    def botRunner(self):
        if self.loop is None:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
        
        log = logging.getLogger('botRunner')
        log.info('running')

        validTokens = [self.genToken() for i in range(self.threadCount)]
        while "" in validTokens:
            validTokens.remove("")

        count = len(validTokens) if len(validTokens) < self.threadCount else self.threadCount
        self.ppe = ThreadPoolExecutor(max_workers=count)
        self.botRunnerTasks = [
            self.ppe.submit(self.genBot, validTokens[i])
            for i in range(count)
        ]

        pprint("threadpool filled")

        def IdQueuer():
            while True:
                time.sleep(1)
                if len(self.bots) == 0:
                    return

                reuse = None
                for bot in self.bots:
                    if reuse is None:
                        userId = self.genId()
                    else:
                        userId = reuse

                    if userId is None:
                        return

                    if bot.AddIdToQueue(userId):
                        reuse = None
                        continue
                    else:
                        reuse = userId

        with ThreadPoolExecutor() as executor:
            executor.submit(IdQueuer())
            for task in as_completed(executor):
                pprint(task.result())

        for i in range(len(self.bots)):
            if not self.bots[i].is_closed():
                self.bots[i].close()


    def getDmContent(self):
        return self.config["message"]

    def setMessaged(self, userId):
        self.ids[userId] = True

    def logAttempt(self, line):
        writeToAttempts(line)
