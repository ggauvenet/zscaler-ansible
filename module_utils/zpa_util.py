import time, json
import os.path
import requests
import logging

logger = logging.getLogger('zpa-client')

_prefix_application = {
    'application': 'mgmtconfig/v1',
    'segmentGroup': 'mgmtconfig/v1', 
    'server': 'mgmtconfig/v1', 
    'serverGroup': 'mgmtconfig/v1',
    'appConnectorGroup': 'mgmtconfig/v1'
}


class ZPAClient:
    tenant_name = None
    customer_id = None
    client_id = None
    client_secret = None

    headers = {
        'content-type': "application/json",
        'cache-control': "no-cache"
    }
    session = None

    def __init__(self, config=None):
        self._load_config(config=config)

    def _load_config(self, config=None, configfile='~/.zpacf.json'):
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
            if 'customer_id' in jsconfig:
                self.customer_id  = jsconfig['customer_id']
            if 'client_id' in jsconfig:
                self.client_id  = jsconfig['client_id']
            if 'client_secret' in jsconfig:
                self.client_secret  = jsconfig['client_secret']
        if config:
            if 'tenant_name' in config:
                self.tenant_name  = config['tenant_name']
            if 'customer_id' in config:
                self.customer_id  = config['customer_id']
            if 'client_id' in config:
                self.client_id  = config['client_id']
            if 'client_secret' in config:
                self.client_secret  = config['client_secret']


    def _url(self, uri):
        logger.debug('URI: URI=%s, Split=%s', uri, uri.split("/"))
        app = uri.split('/')[0]
        return "https://{0}/{1}/admin/customers/{2}/{3}".format(self.tenant_name, _prefix_application[app], self.customer_id, uri)

    def login(self):
        self.session = requests.session()
        headers = {
          'content-type': 'application/x-www-form-urlencoded'
        }
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        logger.debug("[POST] %s", "https://{0}/signin".format(self.tenant_name))
        time.sleep(2.2)
        res = self.session.post("https://{0}/signin".format(self.tenant_name), headers = headers, data = payload)

        jv = self._manage_response(res)
        if jv != None:
            if 'token_type' in jv and jv['token_type'] == "Bearer": 
                self.headers['Authorization'] = "Bearer {0}".format(jv['access_token'])

        logger.debug("[Authorization] %s", self.headers)

    def logout(self):
        logger.debug("[POST] %s", "https://{0}/signout".format(self.tenant_name))
        time.sleep(2.2)
        res = self.session.post("https://{0}/signout".format(self.tenant_name), headers = self.headers, data = {})
        logger.debug(str(res))
        self._manage_response(res)
        self.session = None

    def post(self, uri, payload):
        if self.session == None: 
            return
        logger.debug("[POST] %s", self._url(uri))
        jsdata = json.dumps(payload)
        time.sleep(2.2)
        res = self.session.post(self._url(uri), headers = self.headers, data = jsdata)
        logger.debug(str(res) + " | %s", jsdata)
        return self._manage_response(res)

    def get(self, uri, params={}):
        if self.session == None: 
            return
        time.sleep(1.2)
        res = self.session.get(self._url(uri), headers = self.headers, params=params)
        logger.debug("[GET] %s", res.url)
        logger.debug(str(res) + " | %s", res.text)
        return self._manage_response(res)

    def delete(self, uri):
        if self.session == None: 
            return
        logger.debug("[DELETE] %s", self._url(uri))
        time.sleep(5.2)
        res = self.session.delete(self._url(uri), headers = self.headers)
        logger.debug(str(res) + " | %s", res.text)
        return self._manage_response(res)

    def put(self, uri, payload):
        if self.session == None: 
            return
        logger.debug("[PUT] %s | %s", self._url(uri), json.dumps(payload))
        time.sleep(2.2)
        res = self.session.put(self._url(uri), headers = self.headers, data = json.dumps(payload))
        logger.debug(str(res) + " | %s", res.text)
        return self._manage_response(res)
    
    def _manage_response(self, res):
        if res.status_code >= 200 and res.status_code < 300:
            if res.text != "":
                jv = json.loads(res.text)
                if 'code' in jv and 'message' in jv:
                    raise Exception(jv['code'], jv['message'])   
                return jv
        else:
            raise Exception(str(res), res.text, res)

if __name__ == "__main__":
    import sys
    logging.basicConfig(stream = sys.stdout, filemode = "w", level = logging.DEBUG)
    zcli = ZPAClient()
    zcli.login()
    zcli.get('application', {'page': 1, 'pagesize': 500 })
    zcli.logout()
