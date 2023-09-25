import time, json
import os.path
import requests
import logging

logger = logging.getLogger('zscaler-client')

def obfuscateApiKey(seed):
    now = int(time.time() * 1000)
    n = str(now)[-6:]
    r = str(int(n) >> 1).zfill(6)
    key = ""
    for i in range(0, len(str(n)), 1):
        key += seed[int(str(n)[i])]
    for j in range(0, len(str(r)), 1):
        key += seed[int(str(r)[j])+2]

    logger.debug("Time: %s, Key: %s", now, key)

    return (key, now)

class ZscalerClient:
    tenant_name = None
    api_version = None
    api_key = None
    cred_username = None
    cred_password = None

    headers = {
        'content-type': "application/json",
        'cache-control': "no-cache"
    }
    session = None

    def __init__(self, config=None):
        self._load_config(config=config)


    def _load_config(self, config=None, configfile='~/.zscalercf.json'):
        if configfile.startswith("~"):
            configfile = os.path.expanduser(configfile)
        else:
            configfile = os.path.abspath(configfile)
        if os.path.exists(configfile):
            jsconfig = None
            with open(configfile, 'r') as f:
                jsconfig = json.load(f)
                f.close()
            if 'tenant_name' in jsconfig:
                self.tenant_name  = jsconfig['tenant_name']
            if 'api_version' in jsconfig:
                self.api_version  = jsconfig['api_version']
            if 'api_key' in jsconfig:
                self.api_key  = jsconfig['api_key']
            if 'username' in jsconfig:
                self.cred_username  = jsconfig['username']
            if 'password' in jsconfig:
                self.cred_password  = jsconfig['password']
        if config:
            if 'tenant_name' in config:
                self.tenant_name  = config['tenant_name']
            if 'api_version' in config:
                self.api_version  = config['api_version']
            if 'api_key' in config:
                self.api_key  = config['api_key']
            if 'username' in config:
                self.cred_username  = config['username']
            if 'password' in config:
                self.cred_password  = config['password']


    def _url(self, uri):
        return "https://{0}/api/{1}/{2}".format(self.tenant_name, self.api_version, uri)

    def login(self):
        self.session = requests.session()
        (key, now) = obfuscateApiKey(self.api_key)
        payload = {
            "username": self.cred_username,
            "password": self.cred_password,
            "apiKey": key,
            "timestamp": str(now)
        }
        self.post("authenticatedSession", payload)
        self.get("authenticatedSession")

    def logout(self):
        self.delete("authenticatedSession")
        self.session = None

    def post(self, uri, payload):
        if self.session == None: 
            return
        logger.debug("[POST] %s", self._url(uri))
        res = self.session.post(self._url(uri), headers = self.headers, data = json.dumps(payload))
        logger.debug(str(res) + " | %s", payload)
        time.sleep(0.5)
        if res.status_code >= 200 and res.status_code < 300:
            jv = json.loads(res.text)
            if 'code' in jv and 'message' in jv:
                raise Exception(jv['code'], jv['message'])   
            return jv
        else:
            raise Exception(str(res), res.text, res)

    def get(self, uri, params={}):
        if self.session == None: 
            return
        time.sleep(0.5)
        logger.debug("[GET] %s", self._url(uri))
        res = self.session.get(self._url(uri), headers = self.headers, params=params)
        logger.debug(str(res) + " | %s", res.text)
        return self._manage_response(res)

    def delete(self, uri):
        if self.session == None: 
            return
        logger.debug("[DELETE] %s", self._url(uri))
        res = self.session.delete(self._url(uri), headers = self.headers)
        logger.debug(str(res) + " | %s", res.text)
        time.sleep(1)
        return self._manage_response(res)

    def put(self, uri, payload):
        if self.session == None: 
            return
        logger.debug("[PUT] %s | %s", self._url(uri), json.dumps(payload))
        res = self.session.put(self._url(uri), headers = self.headers, data = json.dumps(payload))
        logger.debug(str(res) + " | %s", res.text)
        time.sleep(0.5)
        return self._manage_response(res)
    
    def _manage_response(self, res):
        if res.status_code >= 200 and res.status_code < 300:
            jv = json.loads(res.text)
            if 'code' in jv and 'message' in jv:
                raise Exception(jv['code'], jv['message'])   
            return jv
        else:
            raise Exception(str(res), res.text, res)


if __name__ == "__main__":
    import sys
    logging.basicConfig(stream = sys.stdout, filemode = "w", level = logging.DEBUG)
    zcli = ZscalerClient()
    zcli.login()
    zcli.get('staticIP', params={'ipAddress':'12.1.1.1'})
    zcli.logout()
