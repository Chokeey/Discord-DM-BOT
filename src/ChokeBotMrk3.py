import logging
import queue
import random
import threading
import time
from threading import Thread

import discord
from discord import errors
from pprint import pprint
import asyncio

class ChokeBot(discord.Client):
    
    def configure(self, token, manager):
        self.token = token
        self.userIds = {}
        self.manager = manager
        self.ready = False
        self.dmQueue = queue.Queue(maxsize=1)
        self.log = logging.getLogger("ChokeBot")
        self.nextDm = time.time()

    async def on_error(self, event_method, *args, **kwargs):
        message = args[0]  # Gets the message object
        pprint("on_error({})".format(message))

    async def on_ready(self):
        pprint('Logged on as {0}!'.format(self.user))
        await self.change_presence(status=discord.Status.online)
        self.ready = True
        asyncio.create_task(self.dmTaskRunner())

    async def dmTaskRunner(self):
        self.manager.logAttempt("context:{}-{}, event:Dm Task Runner Started"
                                .format(threading.current_thread().getName(), self.token))
        while True:
            await asyncio.sleep(0.1)
            #pprint("context:{}-{}, event:Is Running"
            #       .format(threading.current_thread().getName(), self.user))
            now = time.time()
            if now < self.nextDm:
                delta = self.nextDm-now
                pprint("context:{}-{}, event:TimeLeftTillNextDm={}"
                       .format(threading.current_thread().getName(), self.token, delta))
                await asyncio.sleep(delta)
                continue

            if self.dmQueue.qsize() > 0:
                userId = self.dmQueue.get()
                try:
                    await self.SendInviteMessage(userId)
                except Exception as e:
                    pprint(e)
                self.nextDm = time.time() + random.uniform(10.0, 15.0)

    def AddIdToQueue(self, userid):
        try:
            self.dmQueue.put(userid, block=False)
            #pprint("context:{}-{}, event:PutInQueue={}"
            #       .format(threading.current_thread().getName(), self.token, userid))
            return True
        except queue.Full as e:
            return False

    async def SendInviteMessage(self, userid):
        if userid == self.user.id:
            return

        user = None
        for guild in self.guilds:
            tmp = await guild.query_members(user_ids=[userid])
            self.manager.logAttempt("context:{}-{}, event:Member Query={}, info:{}"
                                    .format(threading.current_thread().getName(), self.token, userid, str(tmp)))
            if len(tmp) > 0:
                user = tmp[0]
                break
            else:
                try:
                    user = await self.fetch_user(int(userid))
                except discord.NotFound as e:
                    user = None
                except Exception as e:
                    user = None

        if user is None:
            return

        pprint("Attempting to message to:{}".format(user))
        self.manager.logAttempt("context:{}-{}, event:dm attempt={}"
                                .format(threading.current_thread().getName(), self.token, user.id))
        try:
            await user.send(await self.BuildMessage())
            pprint("Sent message to:{}".format(user))
            self.manager.logAttempt("context:{}-{}, event:dm success={}"
                                    .format(threading.current_thread().getName(), self.token, user.id))
            self.manager.setMessaged(userid)
            return True
        except errors.Forbidden as e:
            self.log.error(e)
            pprint("Message attempt failed. Reason: {}".format(e))
            self.manager.logAttempt("context:{}-{}, error:{}"
                                    .format(threading.current_thread().getName(), user.id, e))

    async def BuildMessage(self):
        content = self.manager.getDmContent()
        if content is None or len(content) == 0:
            content = """Hey, check out this NFT collection called Plumpy Pandas! 

🐼The launch date is yet to be announced. The team consists of pretty big marketers from other projects working together🐼

🐼 They’re doing multiple giveaways which is why I’m messaging you (sorry for the spam)  🐼

🐼 The team has insane backing & the website alone looks freaking AMAZING. 🐼

Check out their discord:
https://discord.gg/NVBPBURCQf
https://cdn.discordapp.com/attachments/891323466312216616/892508932810096650/plumpypanda.gif"""
        #embed = discord.Embed(title="You've been invited to a server!", description="Plumpy Panda",
        #                      url="https://discord.gg/NVBPBURCQf")
        #embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/891323466312216616/892508932810096650/plumpypanda.gif")
        return "{}{}{}".format(content, "\n", str(random.uniform(10000.0, 90000.0)))#, False, embed)

