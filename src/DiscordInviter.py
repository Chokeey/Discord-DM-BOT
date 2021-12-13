import asyncio
import logging

import aiohttp
import requests
from pprint import pprint
import discord

from requests.exceptions import ProxyError, SSLError

ua = None
bn = None
bv = None

async def init():
    global ua, bn, bv
    session = aiohttp.ClientSession()
    ua = await discord.utils._get_user_agent(session)
    bn = await discord.utils._get_build_number(session)
    bv = await discord.utils._get_browser_version(session)

loop = asyncio.get_event_loop()
loop.run_until_complete(init())

def Invite(token, code, proxy):
    logger = logging.getLogger("discordinviter")
    header = {
        "Authorization": token,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        'os': 'Windows',
        'browser': 'Chrome',
        'device': '',
        'browser_user_agent': ua,
        'browser_version': bv,
        'os_version': '10',
        'referrer': '',
        'referring_domain': '',
        'referrer_current': '',
        'referring_domain_current': '',
        'release_channel': 'stable',
        'system_locale': 'en-US',
        'client_build_number': str(bn),
        'client_event_source': None
    }

    try:
        r = requests.post("https://discordapp.com/api/v9/invites/" + code, headers=header, proxies=proxy)
        logger.info("{}{}".format(r.status_code, r.json()))
        return r.status_code
    except ProxyError and SSLError as e:
        logger.error(e)
        return 407

