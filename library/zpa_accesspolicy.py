#!/usr/bin/python 
# -*- coding: utf-8 -*-
import traceback, logging
from ansible.module_utils.basic import AnsibleModule 
from ansible.module_utils.zpa_util import ZPAClient

logger = logging.getLogger('ansible-zpa-accesspolicy')

ACTION = ["ALLOW","DENY","LOG","RE_AUTH","NEVER","BYPASS","INTERCEPT","NO_DOWNLOAD","BYPASS_RE_AUTH","INTERCEPT_ACCESSIBLE","ISOLATE","BYPASS_ISOLATE","INSPECT","BYPASS_INSPECT","REQUIRE_APPROVAL","INJECT_CREDENTIALS","CHECK_CAPABILITIES","MONITOR","DO_NOT_MONITOR"]
OPERATOR = ["AND","OR"]


def get_application(zcls, name):
    retlist = zcls.get('application', { 'search': 'name LIKE {0}'.format(name) })
    if 'list' in retlist:
        for appitem in retlist['list']: 
            if appitem['name'] == name:
                return appitem
    return None

def get_samlattribute(zcls, name):
    retlist = zcls.get('samlAttribute', { 'search': 'name LIKE {0}'.format(name) })
    if 'list' in retlist:
        for sattitem in retlist['list']: 
            if sattitem['name'] == name:
                return sattitem
    return None

def compare_operands(req, get):
    pass

def compare_conditions(req, get):
    equal = True
    if len(req) != len(get):
        return False
    for gitem in get:
        gfound = False
        for ritem in req:
            if gitem['operator'] == ritem['operator']:
                gfound = True
        equal &= gfound
    return equal

def compare_accesspolicy(req, get):
    equal = True
    test = {}
    for key in req.keys():
        if key in get:
            if key == 'conditions':
                test[key] = compare_conditions(req[key], get[key])
            elif key in ['policyType']:
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
            action = dict(type='str', choices=ACTION, default="ALLOW"), 
            conditions = dict(type='list', elements='dict'),
            operator = dict(type='str', choices=OPERATOR, default="AND"),
            defaultRule = dict(type='bool', default=False),
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

    policySet = zcls.get('policySet/policyType/ACCESS_POLICY')

    retlist = zcls.get('policySet/rules/policyType/ACCESS_POLICY', { 'search': 'name LIKE {0}'.format(name) })
    if 'list' in retlist:
        for acpitem in retlist['list']: 
            if acpitem['name'] == name:
                get = acpitem
    
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
    req['policyType'] = "1"

    if 'conditions' in req:
        for i in range(len(req['conditions'])):
            if not 'negated' in req['conditions'][i]:
                req['conditions'][i]['negated'] = False
            if 'operands' in req['conditions'][i]:
                for j in range(len(req['conditions'][i]['operands'])): 
                    oper = req['conditions'][i]['operands'][j]
                    if oper['objectType'] == "APP": 
                        app = get_application(zcls, oper['name'])
                        if app:
                            req['conditions'][i]['operands'][j]['lhs'] = "id"
                            req['conditions'][i]['operands'][j]['rhs'] = app['id']
                    elif oper['objectType'] == "SAML": 
                        attr = get_samlattribute(zcls, oper['name'])
                        if attr:
                            req['conditions'][i]['operands'][j]['lhs'] = attr['id']
                    elif oper['objectType'] == "CLIENT_TYPE": 
                        req['conditions'][i]['operands'][j]['lhs'] = 'id'
                        req['conditions'][i]['operands'][j]['rhs'] = oper['name']


    #module.fail_json(msg="Stop", get=get, req=req)

    equal = False
    if _update and (get != None):
        (equal, test) = compare_accesspolicy(req, get)
        if equal:
            action = "Checked"
        else:
            req['id'] = get['id']

    try: 
        if _create:
            #module.fail_json(msg="Test Create", get=get, req=req)
            if not module.check_mode:
                zcls.post('policySet/{0}/rule'.format(policySet['id']), req)
            changed = True
            action = "Create"
        if _update and (not equal):
            #module.fail_json(msg="Update", get=get, req=req)
            if not module.check_mode:
                result = zcls.put('policySet/{0}/rule/{1}'.format(policySet['id'], get['id']), req)
            changed = True
            action = "Update"
        if _delete: 
            if not module.check_mode:
                zcls.delete('policySet/{0}/rule/{1}'.format(policySet['id'], get['id']))
            action = "Delete"
            changed = True
    except Exception as err:
        module.fail_json(msg=str(err), get=get, req=req)

    finally: 
        zcls.logout()

    module.exit_json(changed=changed, failed=False, result=req, action=action)

if __name__ == "__main__":
    main()