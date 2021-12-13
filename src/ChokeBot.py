import logging
import random
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
        self.log = logging.getLogger("ChokeBot")

    async def GetMemberIds(self):
        ids = []
        for member in self.get_all_members():
            ids.append(member.id)
        return ids

    async def broadcast(self):
        if not self.ready:
            return

        for userId in self.userIds:
            if self.userIds[userId]:
                continue
            try:
                await asyncio.sleep(random.uniform(10.0, 15.0))
                asyncio.ensure_future(self.SendInviteMessage(userId))
            except Exception as e:
                self.log.error(e)
                self.manager.logAttempt("context:{}-{}, error:{}".format(Thread.name, userId, e))


        #self.manager.loadIds(self.token, await self.GetMemberIds())
        newIds = self.manager.requestIds(self.token)
        if len(newIds) == 0:
            pprint("No more ids to invite, bot instance shutting down...")
            self.manager.logAttempt("context:{}, event:acquire, info:{}".format(Thread.name, "No more ids."))
            await self.close()
        else:
            self.userIds = newIds
            asyncio.ensure_future(self.broadcast())

    async def on_error(self, event_method, *args, **kwargs):
        message = args[0]  # Gets the message object
        pprint("on_error({})".format(message))

    async def on_ready(self):
        pprint('Logged on as {0}!'.format(self.user))
        await self.change_presence(status=discord.Status.online)
        self.ready = True
        #self.manager.loadIds(self.token, await self.GetMemberIds())
        asyncio.ensure_future(self.broadcast())
        #await self.TestDM("dank")

    async def SendInviteMessage(self, userid):
        if (userid == self.user.id):
            return #drop silently

        #user = await discord.Client.fetch_user(self, userid)
        user = None
        for guild in self.guilds:
            tmp = await guild.query_members(user_ids=[userid])
            if tmp is not None:
                user = tmp[0]
                break

        if user is None:
            return

        pprint("Attempting to message to:{}".format(user))
        self.manager.logAttempt("context:{}-{}, event:dm attempt".format(Thread.name, user.id))
        try:
            await user.send(await self.BuildMessage())
            pprint("Sent message to:{}".format(user))
            self.manager.logAttempt("context:{}-{}, event:dm success".format(Thread.name, user.id))
            self.manager.setMessaged(userid)
        except errors.Forbidden as e:
            self.log.error(e)
            pprint("Message attempt failed. Reason: {}".format(e))
            self.manager.logAttempt("context:{}-{}, error:{}".format(Thread.name, user.id, e))


    async def TestDM(self, message):
        #users = ["775690931235586068", "206371167735513089", "504432447782649876"]
        users = ["504432447782649876"]
        pprint("TESTDM")
        for uid in users:
            user = await discord.Client.fetch_user(self, uid)
            if user is not None:
                #await user.send(message)
                await self.SendInviteMessage(uid)
                pprint(user)
        await self.close()
        
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
        return content#, False, embed)
        
##    async def on_message(self, message):
##        print('Message from {0.author}: {0.content}'.format(message))
##        if message.author.id not in ids:
##            ids[message.author.id] = False;
##        print(ids)
