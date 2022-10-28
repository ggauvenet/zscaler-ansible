#!/usr/bin/python 
# -*- coding: utf-8 -*-
import traceback
from ansible.module_utils.basic import AnsibleModule 
from ansible.module_utils.zscaler_util import ZscalerClient

def main(): 
    module = AnsibleModule( 
        argument_spec=dict( 
        state = dict(required=True, choices=['present', 'absent']), 
        ip = dict(required=True, type='str'), 
        location = dict(required=True, type='str'), 
        description = dict(required=True, type='str'), 
        ),
        supports_check_mode=True
    )
    changed = False
    _create = False
    _delete = False

    state = module.params.get('state')
    static_ip = module.params.get('ip') 
    location = module.params.get('location')    
    description = module.params.get('description')

    zcls = ZscalerClient()
    zcls.login()
    ret = zcls.get('staticIP', params=dict(ipAddress=static_ip))

    action = "Nothing"
    changed = False
    _create = False
    _update = False
    _delete = False 

    if state == 'present':
        if len(ret) == 0: 
            _create = True
        elif not 'comment' in ret[0]: 
            _update = True
        elif 'comment' in ret[0] and ret[0]['comment'] != description:
            _update = True
    elif state == 'absent':
        if len(ret) < 0:
            _delete = True 

    payload = None
    if len(ret) != 0:
        payload = zcls.get('staticIP/{0}'.format(ret[0]['id']))


    try:
        if _create:
            payload = {
                "ipAddress": static_ip,
                "comment": description,
            }
            if not module.check_mode:
                zcls.post('staticIP', payload)
            changed = True
            action = "Create"
        if _update:
            payload['comment'] = description
            if not module.check_mode:
                result = zcls.put('staticIP/{0}'.format(ret[0]['id']), payload)
            changed = True
            action = "Update"
        if _delete: 
            if not module.check_mode:
                zcls.delete('staticIP/{0}'.format(ret[0]['id']))
            action = "Delete"
            changed = True
    except Exception as err:
        module.fail_json(msg=str(err), get=get, req=req)

    zcls.logout()

    module.exit_json(changed=changed, result=payload, action=action)

if __name__ == "__main__":
    main()