#!/usr/bin/python 
# -*- coding: utf-8 -*-
import traceback, logging
from ansible.module_utils.basic import AnsibleModule 
from ansible.module_utils.zscaler_util import ZscalerClient

TIME_UNIT = ["MINUTE", "HOUR", "DAY"]
PROFILE_VALUES = ["NONE", "CORPORATE", "SERVER", "GUESTWIFI", "IOT"]

ZSCALER_COUNTRY = {
    None : "NONE",
    'FR': "FRANCE"
}
ZSCALER_TZ = { 
    None: "NOT_SPECIFIED",
    'Europe/Paris': "FRANCE_EUROPE_PARIS"
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


def compare_location(req, get):
    equal = True
    test = {}
    for key in req.keys():
        if key in get:
            if key == 'vpnCredentials':
                test[key] = compare_vpnCredentials(req[key], get[key])
                equal &= test[key]
            else:
                test[key] = req[key] == get[key]
                equal &= test[key]
        else:
            test[key] = False
            equal &= test[key]
    return (equal, test)


def main(): 

    logging.basicConfig(filename="/tmp/zscaler_util.log", filemode = "a", level = logging.DEBUG)

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
        )
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
            if len(groupRet) > 0:
                groups.append(dict(id=groupRet[0]['id'], name=groupRet[0]['name']))

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
        
        # Euh comment dire ! 
        req.pop('surrogateRefreshTimeInMinutes') 

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
            zcls.post('locations', req)
            changed = True
            action = "Create"
        if _update and (not equal):
            #module.fail_json(msg="Update", get=get, req=req)
            result = zcls.put('locations/{0}'.format(get['id']), req)
            changed = True
            action = "Update"
        if _delete: 
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