#!/usr/bin/python 
# -*- coding: utf-8 -*-
import traceback, logging
from ansible.module_utils.basic import AnsibleModule 
from ansible.module_utils.zpa_util import ZPAClient

logger = logging.getLogger('ansible-zpa-segmentgroup')

CONFIG_SPACE = ["DEFAULT", "SIEM"]

def compare_segmentgroup(req, get):
    equal = True
    test = {}
    for key in req.keys():
        if key in get:
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
            # inspectTrafficWithZia = dict(type='bool', default=False),
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

    retlist = zcls.get('segmentGroup', { 'search': name })
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

    equal = False
    if _update and (get != None):
        (equal, test) = compare_segmentgroup(req, get)
        if equal:
            action = "Checked"
        else:
            req['id'] = get['id']

    try: 
        if _create:
            #module.fail_json(msg="Test Create", get=get, req=req)
            if not module.check_mode:
                zcls.post('segmentGroup', req)
            changed = True
            action = "Create"
        if _update and (not equal):
            #module.fail_json(msg="Update", get=get, req=req)
            if not module.check_mode:
                result = zcls.put('segmentGroup/{0}'.format(get['id']), req)
            changed = True
            action = "Update"
        if _delete: 
            if not module.check_mode:
                zcls.delete('segmentGroup/{0}'.format(get['id']))
            action = "Delete"
            changed = True
    except Exception as err:
        module.fail_json(msg=str(err), get=get, req=req)

    finally: 
        zcls.logout()

    module.exit_json(changed=changed, failed=False, result=req, action=action)

if __name__ == "__main__":
    main()