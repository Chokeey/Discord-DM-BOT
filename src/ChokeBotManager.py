import asyncio
import logging
import random
import sys
from threading import Lock
from concurrent.futures import ThreadPoolExecutor

import aiohttp
from urllib3.exceptions import ProxyError

from ChokeBot import ChokeBot
from discord import errors

from pprint import pprint
import itertools

from aiohttp import BasicAuth, TCPConnector


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
        self.idsLoadedBy = {}
        self.proxies = proxies
        self.preferredProxies = preferredProxies
        self.proxyLogin = proxyLogin
        self.config = config
        self.botThreads = []
        self.tokensInUse = []
        self.idsInUse = []
        self.totalTokensAcquired = {}
        self.spliceIndex = 0
        self.spliceAmount = config["dmPerBot"] if config["dmPerBot"] else 100
        self.loop: asyncio.AbstractEventLoop = None
        self.ppe: ThreadPoolExecutor = None
        self.threadCount = 0
        self.lock = Lock()

    def start(self, count):
        self.loop = asyncio.get_event_loop()
        self.threadCount = count
        self.ppe = ThreadPoolExecutor(max_workers=count)
        try:
            self.loop.run_until_complete(self.runExecutors())
        finally:
            pass

    async def runExecutors(self):
        log = logging.getLogger('run_botRunner_tasks')
        log.info('starting')

        log.info('creating executor tasks')
        blocking_tasks = [
            self.loop.run_in_executor(self.ppe, self.botRunner, i)
            for i in range(self.threadCount)
        ]
        log.info('waiting for executor tasks')
        completed, pending = await asyncio.wait(blocking_tasks)
        results = [t.result() for t in completed]
        log.info('results: {!r}'.format(results))
        log.info('exiting')

    def botRunner(self, i):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        log = logging.getLogger('botRunner({})'.format(i))
        log.info('running')

        while True:
            try:
                botToken = ""
                freeTokens = True
                for key in self.tokens:
                    if self.tokens[key] is True and key not in self.tokensInUse:
                        botToken = key
                        self.tokensInUse.append(key)
                        freeTokens = False
                        break

                basic_auth = BasicAuth(self.proxyLogin["user"], self.proxyLogin["pass"])
                proxy = random.choice(list(self.proxies.keys()))
                if botToken in self.preferredProxies:
                    proxy = self.preferredProxies[botToken]
                else:
                    self.preferredProxies[botToken] = proxy

                client = ChokeBot(proxy="http://"+proxy, proxy_auth=basic_auth)
                client.configure(botToken, self)
                pprint("Attempt to run bot:{}\n".format(botToken))
                client.run(botToken)
            except errors.HTTPException and errors.LoginFailure as e:
                self.tokens[botToken] = False
                log.error(e)
                break
            except aiohttp.ServerDisconnectedError as e:
                log.error(e)
                break
            except ProxyError as e:
                log.error(e)
                break
            except Exception as e:
                log.error(e)
                break

    def getDmContent(self):
        return self.config["message"]

    def setMessaged(self, userId):
        self.ids[userId] = True

    def requestIds(self, token):
        with self.lock:
            idsection = {}
            i = 0
            for key in self.ids:
                if i >= self.spliceAmount:
                    break

                if self.ids[key] is False and key not in self.idsInUse:
                    idsection[key] = False
                    self.idsInUse.append(key)
                    i += 1

            if token in self.totalTokensAcquired:
                self.totalTokensAcquired[token] += len(idsection)
            else:
                self.totalTokensAcquired[token] = len(idsection)

            writeToAcquires("{} has acquired {} in total. Current acquisition: {}"
                            .format(token, self.totalTokensAcquired[token], len(idsection)))
            return idsection

    def loadIds(self, token, ids):
        for uid in ids:
            if uid in self.idsLoadedBy:
                if token not in self.idsLoadedBy[uid]:
                    self.idsLoadedBy[uid].append(token)
            else:
                self.idsLoadedBy[uid] = []

            if uid not in self.ids:
                self.ids[uid] = False

    def logAttempt(self, line):
        writeToAttempts(line)
