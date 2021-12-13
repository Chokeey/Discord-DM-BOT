import requests
from requests.exceptions import ProxyError
import time
proxies = []

with open("proxyalt.txt") as f:
    lines = f.readlines()
    for line in lines:
        line = line.strip()
        if line not in proxies:
            proxies.append(line)
            
proxyUser = "geonode_94xDyQbtzA"
proxyPass = "abbdd564-a554-4a2d-9528-63af746c1bc2"
proxyUser = "Selzacharye9"
proxyPass = "S4e3BsQ"
for p in proxies:
    try:
        proxy = {"https": "http://{}:{}@{}".format(proxyUser, proxyPass, p)}
        r = requests.get("https://api.ipify.org", proxies=proxy)
        print(r.text)
        time.sleep(1)
    except ProxyError as e:
        print(e)
