#!/usr/bin/python 
# -*- coding: utf-8 -*-
import traceback, logging
from ansible.module_utils.basic import AnsibleModule 
from ansible.module_utils.zscaler_util import ZscalerClient

logger = logging.getLogger('ansible-zscaler-location')

TIME_UNIT = ["MINUTE", "HOUR", "DAY"]
PROFILE_VALUES = ["NONE", "CORPORATE", "SERVER", "GUESTWIFI", "IOT"]

ZSCALER_COUNTRY = {
    None : "NONE",
    'FR': "FRANCE",
    'PL': "POLAND",
    'ES': "SPAIN",
    'IT': "ITALY",
    'CZ': "CZECH_REPUBLIC",
    'RO': "ROMANIA",
    'UA': "UKRAINE",
    'BR': "BRAZIL",
    'BG': "BULGARIA",
    'HU': "HUNGARY",
    'RU': "RUSSIA",
    'SG': "SINGAPORE",
    'RS': "SERBIA",
    'VN': "VIETNAM",
}
ZSCALER_TZ = { 
    None: "NOT_SPECIFIED",
    'Europe/Paris': "FRANCE_EUROPE_PARIS",
    'Europe/Warsaw': "POLAND_EUROPE_WARSAW",
    'Europe/Madrid': "SPAIN_EUROPE_MADRID",
    'Europe/Rome': "ITALY_EUROPE_ROME",
    'Europe/Prague': "CZECH_REPUBLIC_EUROPE_PRAGUE",
    'Europe/Bucharest': "ROMANIA_EUROPE_BUCHAREST",
    'Europe/Kiev' : "UKRAINE_EUROPE_KIEV",
    'Europe/Sofia': "BULGARIA_EUROPE_SOFIA",
    'Europe/Budapest': "HUNGARY_EUROPE_BUDAPEST",
    'Europe/Moscow': "RUSSIA_EUROPE_MOSCOW",
    'Europe/Kaliningrad': "RUSSIA_EUROPE_KALININGRAD",
    'Europe/Samara': "RUSSIA_EUROPE_SAMARA",
    'Europe/Volgograd': "RUSSIA_EUROPE_VOLGOGRAD",
    'Europe/Belgrade' : "SERBIA_EUROPE_BELGRADE",
    'Asia/Anadyr': "RUSSIA_ASIA_ANADYR",
    'Asia/Irkutsk': "RUSSIA_ASIA_IRKUTSK",
    'Asia/Kamchatka': "RUSSIA_ASIA_KAMCHATKA",
    'Asia/Krasnoyarsk': "RUSSIA_ASIA_KRASNOYARSK",
    'Asia/Magadan': "RUSSIA_ASIA_MAGADAN",
    'Asia/Novosibirsk': "RUSSIA_ASIA_NOVOSIBIRSK",
    'Asia/Omsk': "RUSSIA_ASIA_OMSK",
    'Asia/Sakhalin': "RUSSIA_ASIA_SAKHALIN",
    'Asia/Vladivostok': "RUSSIA_ASIA_VLADIVOSTOK",
    'Asia/Yakutsk': "RUSSIA_ASIA_YAKUTSK",
    'Asia/Yekaterinburg': "RUSSIA_ASIA_YEKATERINBURG",
    'Asia/Singapore': "SINGAPORE_ASIA_SINGAPORE",
    'America/Sao_Paulo': "BRAZIL_AMERICA_SAO_PAULO",
    'America/Rio_Branco': "BRAZIL_AMERICA_RIO_BRANCO",
    'America/Recife': "BRAZIL_AMERICA_RECIFE",
    'America/Porto_Velho': "BRAZIL_AMERICA_PORTO_VELHO",
    'America/Noronha': "BRAZIL_AMERICA_NORONHA",
    'America/Manaus': "BRAZIL_AMERICA_MANAUS",
    'America/Maceio': "BRAZIL_AMERICA_MACEIO",
    'America/Fortaleza': "BRAZIL_AMERICA_FORTALEZA",
    'America/Eirunepe': "BRAZIL_AMERICA_EIRUNEPE",
    'America/Cuiaba': "BRAZIL_AMERICA_CUIABA",
    'America/Campo_Grande': "BRAZIL_AMERICA_CAMPO_GRANDE",
    'America/Boa_Vista': "BRAZIL_AMERICA_BOA_VISTA",
    'America/Belem': "BRAZIL_AMERICA_BELEM",
    'America/Bahia': "BRAZIL_AMERICA_BAHIA",
    'America/Araguaina': "BRAZIL_AMERICA_ARAGUAINA",
    'Asia/Saigon': "VIETNAM_ASIA_SAIGON",
    'Asia/Ho_Chi_Minh': "VIETNAM_ASIA_SAIGON",
}

    # upBandwidth: "{{ (item.bandwidth.up * 1024) * 0.8 }}"
    # dnBandwidth: "{{ (item.bandwidth.down * 1024) * 0.8 }}"
    # country: "{{ site.country }}"
    # tz: "{{ site.timezone }}"
    # ipAddresses: []
    # authRequired: false
    # sslScanEnabled: false
    # zappSSLScanEnabled: false
    # xffForwardEnabled: false
    # surrogateIP: false
    # idleTimeInMinutes: 0
    # displayTimeUnit: "MINUTES"
    # surrogateIPEnforcedForKnownBrowsers: false
    # surrogateRefreshTimeInMinutes: 0
    # surrogateRefreshTimeUnit: "MINUTES"
    # ofwEnabled: false
    # ipsControl: false
    # aupEnabled: false
    # cautionEnabled: false
    # aupBlockInternetUntilAccepted: false
    # aupForceSslInspection: false
    # aupTimeoutInDays: false
    # profile: "NONE"
    # description: ""
def compare_vpnCredentials(req, get):
    equal = True
    testList = []
    for i in range(len(req)):
        testDict = {}
        for key in req[i].keys():
            if key in get[i]:
                testDict[key] = req[i][key] == get[i][key]
                equal &= testDict[key]
        testList.append(testDict)
    return equal

def compare_groups(req, get):
    equal = True
    if len(req) != len(get):
        return False
    for gitem in get:
        gfound = False
        for ritem in req:
            if ritem['id'] == gitem['id']:
                gfound = True
        equal &= gfound
    return equal

def compare_list(req, get):
    equal = True
    if len(req) != len(get):
        return False
    for gitem in get:
        equal &= gitem in req
    return equal


def compare_location(req, get):
    equal = True
    test = {}
    for key in req.keys():
        if key in get:
            if key == 'vpnCredentials':
                test[key] = compare_vpnCredentials(req[key], get[key])
            elif key == 'staticLocationGroups':
                test[key] = compare_groups(req[key], get[key])
            elif key == 'ipAddresses':
                test[key] = compare_list(req[key], get[key])
            else:
                test[key] = req[key] == get[key]
        else:
            test[key] = False
        logger.info('Test Key=%s, Req=%s, Get=%s, Test=%s', key, req[key], get[key], test[key])
        equal &= test[key]
        
    return (equal, test)


def main(): 

    logging.basicConfig(filename="/tmp/zscaler_util.log", filemode = "a", level = logging.INFO)

    module = AnsibleModule( 
        argument_spec=dict( 
        state = dict(required=True, choices=['present', 'absent']), 
        name = dict(required=True, type='str'), 
        description = dict(type='str', default=""), 
        upBandwidth = dict(type='int', default=0), 
        dnBandwidth = dict(type='int', default=0),
        country = dict(type='str', default='NONE'),
        city = dict(type='str', default=''),
        tz = dict(type='str', default='NOT_SPECIFIED'),
        ipAddresses = dict(type='list', elements='str'),
        authRequired = dict(type='bool', default=False),
        sslScanEnabled = dict(type='bool', default=False),
        zappSslScanEnabled = dict(type='bool', default=False),
        xffForwardEnabled = dict(type='bool', default=False),
        surrogateIP = dict(type='bool', default=False),
        idleTimeInMinutes = dict(type='int', default=0),
        displayTimeUnit = dict(type='str', default="MINUTE", choices=TIME_UNIT),
        surrogateIPEnforcedForKnownBrowsers = dict(type='bool', default=False),
        surrogateRefreshTimeInMinutes = dict(type='int', default=0),
        surrogateRefreshTimeUnit = dict(type='str', default="MINUTE", choices=TIME_UNIT),
        ofwEnabled = dict(type='bool', default=False),
        ipsControl = dict(type='bool', default=False),
        aupEnabled = dict(type='bool', default=False),
        cautionEnabled = dict(type='bool', default=False),
        aupBlockInternetUntilAccepted = dict(type='bool', default=False),
        aupForceSslInspection = dict(type='bool', default=False),
        aupTimeoutInDays = dict(type='int', default=0),
        profile = dict(type='str', default="NONE", choices=PROFILE_VALUES),
        vpnCredentials = dict(type='list', elements='str'),
        countryCode = dict(type='str', default=None),
        subLocation = dict(type='bool', default=False),
        parentName = dict(type='str', default=None),
        groups = dict(type='list', elements='str'),
        ),
        supports_check_mode=True
    )

    if module.params.get('subLocation') and module.params.get('parentName') == None:
        module.fail_json(msg='If subLocation flag set, parentName is madatory')

    state = module.params.get('state')
    locname = module.params.get('name')
    subloc = module.params.get('subLocation')


    zcls = ZscalerClient()
    zcls.login()

    action = "Nothing"
    changed = False
    _create = False
    _update = False
    _delete = False 

    ret = None
    parent = None

    if subloc: 
        parentret = zcls.get('locations', params=dict(search=module.params.get('parentName')))
        if len(parentret) != 0:
            parent = parentret[0]
            ret = zcls.get('locations/{0}/sublocations'.format(parent['id']), params=dict(search=locname))
        else:
            module.fail_json(msg="Parent location {0} not found".format(module.params.get('parentName')))
    else:
        ret = zcls.get('locations', params=dict(search=locname))

    if state == 'present':
        if len(ret) == 0: 
            _create = True
        else:
            _update = True
    elif state == 'absent':
        if len(ret) < 0:
            _delete = True 


    # Groups 
    groups = None
    if module.params.get('groups'):
        groups = [] 
        for groupName in module.params.get('groups'):
            groupRet = zcls.get('locations/groups', params=dict(name=groupName))
            for gritem in groupRet:
                if gritem['name'] == groupName:
                    groups.append(dict(id=gritem['id'], name=gritem['name']))
        logger.info("Groups= %s", groups)

    #module.fail_json(msg="groups", group=groups)

    # Generate req values

    req = None

    if subloc:
        req = module.params.copy()
        req['parentId'] = parent['id']
        req.pop('parentName')
        req.pop('subLocation')
        req.pop('countryCode')
        req.pop('description')
        req['country'] = parent['country']
        req['tz'] = parent['tz']
        if module.params.get('upBandwidth') == 0 and parent['upBandwidth'] > 0:
            req['upBandwidth'] = -1 
        elif module.params.get('upBandwidth') > 0 :
            req['upBandwidth'] = int(float(module.params.get('upBandwidth')) * 1024 * 0.8)
        else:
            req['upBandwidth'] = 0 

        if module.params.get('dnBandwidth') == 0 and parent['dnBandwidth'] > 0:
            req['dnBandwidth'] = -1 
        elif module.params.get('dnBandwidth') > 0 :
            req['dnBandwidth'] = int(float(module.params.get('dnBandwidth')) * 1024 * 0.8)
        else:
            req['dnBandwidth'] = 0 
        req.pop('vpnCredentials')
        #req['vpnCredentials'] = vpnCredentials
        #req.pop('ipAddresses')
        #req['ipAddresses'] = ipAddresses
        req.pop('city')
        req.pop('state')
        req['state'] = parent['state']
        req.pop('groups')
        if groups:
            req['staticLocationGroups'] = groups
        
        if req['surrogateIP'] == False:
            req.pop('surrogateIPEnforcedForKnownBrowsers')
            req.pop('surrogateRefreshTimeInMinutes')
            req.pop('surrogateRefreshTimeUnit')

    else:
        vpnCredentials = []
        ipAddresses = []
        for cred in module.params.get('vpnCredentials'):
            credlist = zcls.get('vpnCredentials', params=dict(search=cred, type="IP"))
            if len(credlist):
                vpnCredentials.append({'id': credlist[0]['id'], 'type': credlist[0]['type'], 'ipAddress': credlist[0]['ipAddress']})
                ipAddresses.append(credlist[0]['ipAddress'])

        req = module.params.copy()
        req.pop('parentName')
        req.pop('subLocation')
        req.pop('countryCode')
        if req['surrogateIP'] == False:
            req.pop('surrogateIPEnforcedForKnownBrowsers')
            req.pop('surrogateRefreshTimeInMinutes')
            req.pop('surrogateRefreshTimeUnit')
        req['country'] = ZSCALER_COUNTRY[module.params.get('countryCode')]
        req['tz'] = ZSCALER_TZ[module.params.get('tz')]
        req['upBandwidth'] = int(float(module.params.get('upBandwidth')) * 1024 * 0.8)
        req['dnBandwidth'] = int(float(module.params.get('dnBandwidth')) * 1024 * 0.8)
        req.pop('vpnCredentials')
        req['vpnCredentials'] = vpnCredentials
        req.pop('ipAddresses')
        req['ipAddresses'] = ipAddresses
        req.pop('city')
        req.pop('state')
        req['state'] = module.params.get('city')
        req.pop('groups')

    # If object exits get values

    get = None
    if len(ret) != 0:
        get = zcls.get('locations/{0}'.format(ret[0]['id']))
        #module.fail_json(msg="Get", get=get)


    # check if diffrent

    equal = False
    if _update and (get != None):
        (equal, test) = compare_location(req, get)
        #module.fail_json(msg="Compare", test=test, equal=equal, get=get, req=req)

        if equal:
            action = "Checked"
        else:
            req['id'] = get['id']

    #module.fail_json(msg="Update", get=get, req=req)

    try: 
        if _create:
            #module.fail_json(msg="Test Create", get=get, req=req)
            if not module.check_mode:
                zcls.post('locations', req)
            changed = True
            action = "Create"
        if _update and (not equal):
            #module.fail_json(msg="Update", get=get, req=req)
            if not module.check_mode:
                result = zcls.put('locations/{0}'.format(get['id']), req)
            changed = True
            action = "Update"
        if _delete: 
            if not module.check_mode:
                zcls.delete('locations/{0}'.format(get['id']))
            action = "Delete"
            changed = True
    except Exception as err:
        module.fail_json(msg=str(err), get=get, req=req)

    finally: 
        zcls.logout()

    module.exit_json(changed=changed, failed=False, result=req, action=action)

if __name__ == "__main__":
    main()