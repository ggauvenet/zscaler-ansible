#!/usr/bin/python 
# -*- coding: utf-8 -*-
import traceback, logging
from ansible.module_utils.basic import AnsibleModule 
from ansible.module_utils.zpa_util import ZPAClient

logger = logging.getLogger('ansible-zpa-application')

BYPASS_TYPE = ["ALWAYS", "NEVER", "ON_NET"]
CONFIG_SPACE = ["DEFAULT", "SIEM"]
HEALTHCHECK_TYPE = ["DEFAULT", "NONE"]
HEALTH_REPORTING = ["NONE", "ON_ACCESS", "CONTINUOUS"]
ICMPACCESS_TYPE = ["PING_TRACEROUTING", "PING", "NONE"]
PROTOCOLS =  ["NONE","KERBEROS","LDAP","SMB"]
APPLICATION_PROTOCOL = ["HTTP","HTTPS","FTP","RDP","SSH","WEBSOCKET","VNC"]
CONNECTION_SECURITY = ["ANY","NLA","NLA_EXT","TLS","VM_CONNECT","RDP"]

INTEGER_FIELDS = ['defaultIdleTimeout', 'defaultMaxAge']


def compare_sraapps(req, get):
    equal = True
    if len(req) != len(get):
        return False
    for gitem in get:
        gfound = False
        gequal = True
        for ritem in req:
            if ritem['name'] == gitem['name']:
                test = {}
                gfound = True
                for key in ritem.keys():
                    if key == 'applicationPort':
                        test[key] = str(ritem[key]) == str(gitem[key])
                    else:
                        test[key] = ritem[key] == gitem[key]
                    gequal &= test[key]
                    logger.info('Test sraApps Key=%s, Req=%s, Get=%s, Test=%s', key, ritem[key], gitem[key], test[key])
        equal &= gfound & gequal
    return equal

def compare_groups(req, get):
    equal = True
    if len(req) != len(get):
        return False
    for gitem in get:
        gfound = False
        for ritem in req:
            if str(ritem['id']) == str(gitem['id']) and str(ritem['name']) == str(gitem['name']):
                gfound = True
        equal &= gfound
    return equal


def compare_portrange(req, get): 
    equal = True
    if len(req) != len(get):
        return False
    for gitem in get:
        gfound = False
        for ritem in req:
            if str(ritem['to']) == str(gitem['to']) and str(ritem['from']) == str(gitem['from']):
                gfound = True
        equal &= gfound
    return equal

def compare_domainName(req, get):
    if len(req) != len(get):
        return False
    equal = True
    for gitem in get:
        if not gitem in req:
            equal &= False
    for ritem in req:
        if not ritem in get:
            equal &= False
    return equal

def compare_application(req, get):
    equal = True
    test = {}
    for key in req.keys():
        if key in get:

            if key == 'tcpPortRange' or key == 'udpPortRange':
                test[key] = compare_portrange(req[key], get[key])
            elif key == 'serverGroups':
                test[key] = compare_groups(req[key], get[key])
            elif key in 'domainNames':
                test[key] = compare_domainName(req[key], get[key])
            elif key in 'sraApps':
                test[key] = compare_sraapps(req[key], get[key])
            elif key in INTEGER_FIELDS:
                test[key] = str(req[key]) == str(get[key])
            else:
                test[key] = req[key] == get[key]
            logger.info('Test Key=%s, Req=%s, Get=%s, Test=%s', key, req[key], get[key], test[key])
        else:
            if req[key] == None:
                test[key] = True
                logger.info('Test Key=%s, Req=[Empty or Null Value], Get=[Missing Value], Test=%s', key, req[key], test[key])
            else:
                test[key] = False
                logger.info('Test Key=%s, Req=%s, Get=[Missing Value], Test=%s', key, req[key], test[key])
        equal &= test[key]
    return (equal, test)


def main(): 
    logging.basicConfig(filename="/tmp/zpa_util.log", filemode = "a", level = logging.DEBUG)

    module = AnsibleModule( 
        argument_spec=dict( 
            state = dict(required=True, choices=['present', 'absent']), 
            name = dict(required=True, type='str'), 
            description = dict(type='str', default=""), 
            enabled = dict(type='bool', default=False),
            domainNames = dict(required=True, type='list', elements='str'),
            configSpace = dict(type='str', choices=CONFIG_SPACE, default="DEFAULT"),
            healthCheckType = dict(type='str', choices=HEALTHCHECK_TYPE, default="DEFAULT"),
            healthReporting = dict(type='str', choices=HEALTH_REPORTING, default="ON_ACCESS"),
            passiveHealthEnabled = dict(type='bool', default=True),

            ipAnchored = dict(type='bool', default=False),
            doubleEncrypt = dict(type='bool', default=False),
            isCnameEnabled = dict(type='bool', default=True),
            icmpAccessType = dict(type='str', choices=ICMPACCESS_TYPE, default="NONE"),
            bypassType = dict(type='str', choices=BYPASS_TYPE, default="NEVER"),
            tcpPortRange = dict(type='list', elements='dict'),
            udpPortRange = dict(type='list', elements='dict'),
            applicationGroup = dict(type='str'), 
            segmentGroup = dict(type='str'),
            appRecommendation = dict(type='str'),
            serverGroups = dict(required=True, type='list', elements='str'),

            adpEnabled = dict(type='bool', default=False),
            udpProtocols = dict(type='str', choices=PROTOCOLS),
            tcpProtocols = dict(type='str', choices=PROTOCOLS),
            bypassOnReauth = dict(type='bool', default=False),
            inspectTrafficWithZia = dict(type='bool', default=False),
            useInDrMode = dict(type='bool', default=False),

            selectConnectorCloseToApp = dict(type='bool', default=True),

            defaultIdleTimeout = dict(type='int', default=0),
            defaultMaxAge = dict(type='int', default=0),
            clientlessApps = dict(type='list', elements='dict'),

            sraApps = dict(type='list', elements='dict')
        ),
        supports_check_mode=True
    )

    state = module.params.get('state')
    name = module.params.get('name')


    zcls = ZPAClient()
    zcls.login()

    action = "Nothing"
    changed = False
    _create = False
    _update = False
    _delete = False 

    get = None

    retlist = zcls.get('application', { 'search': 'name LIKE {0}'.format(name) })
    if 'list' in retlist:
        for appitem in retlist['list']: 
            if appitem['name'] == name:
                get = appitem
    
    if state == 'present':
        if not get: 
            _create = True
        else:
            _update = True
    elif state == 'absent':
        if get:
            _delete = True 

    req = module.params.copy()
    req.pop('state')

    ## Description
    ################
    if 'description' in req: 
        if req['description'] == "":
            req.pop('description')

    ## Port Range
    ################
    if 'udpPortRange' in req: 
        if len(req['udpPortRange']) == 0:
            req.pop('udpPortRange')

    if 'tcpPortRange' in req: 
        if len(req['tcpPortRange']) == 0:
            req.pop('tcpPortRange')

    ## Connector Close to App
    ################
    if 'selectConnectorCloseToApp' in req:
        if req['selectConnectorCloseToApp'] == False:
            req.pop('defaultIdleTimeout')
            req.pop('defaultMaxAge')

    ## RDP / SSH Portal  (sraApps)
    ################
    if 'sraApps' in req:
        if len(req['sraApps']) == 0:
            req.pop('sraApps')

    ## Segment Group
    ################
    if 'segmentGroup' in req: 
        segmentGroupName = req.pop('segmentGroup')
        retlist = zcls.get('segmentGroup', { 'search': 'name LIKE {0}'.format(segmentGroupName) })
        if 'list' in retlist:
            for segitem in retlist['list']:
                if segitem['name'] == segmentGroupName: 
                    req['segmentGroupId'] = segitem['id']
                    req['segmentGroupName'] = segitem['name']

    ## Server Group
    ###############
    if 'serverGroups' in req:
        srvGroupList = req.pop('serverGroups')
        serverGroups = []
        retlist = zcls.get('serverGroup', { 'pagesize': 500 })
        if 'list' in retlist:
            for srvgitem in retlist['list']:
                for reqsrvitem in srvGroupList: 
                    if srvgitem['name'] == reqsrvitem:
                        serverGroups.append({'id': srvgitem['id'], 'name': srvgitem['name']})
        req['serverGroups'] = serverGroups
    

    equal = False
    if _update and (get != None):
        (equal, test) = compare_application(req, get)
        if equal:
            action = "Checked"
        else:
            req['id'] = get['id']

    try: 
        if _create:
            #module.fail_json(msg="Test Create", get=get, req=req)
            if not module.check_mode:
                zcls.post('application', req)
            changed = True
            action = "Create"
        if _update and (not equal):
            #module.fail_json(msg="Update", get=get, req=req)
            if not module.check_mode:
                result = zcls.put('application/{0}'.format(get['id']), req)
            changed = True
            action = "Update"
        if _delete: 
            if not module.check_mode:
                zcls.delete('application/{0}'.format(get['id']))
            action = "Delete"
            changed = True
    except Exception as err:
        module.fail_json(msg=str(err), get=get, req=req)

    finally: 
        zcls.logout()

    module.exit_json(changed=changed, failed=False, result=req, action=action)

if __name__ == "__main__":
    main()