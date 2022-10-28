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
        psk = dict(required=True, type='str'), 
        description = dict(required=True, type='str'), 
        ),
        supports_check_mode=True
    )
    changed = False
    _create = False
    _delete = False

    state = module.params.get('state')
    ip = module.params.get('ip') 
    psk = module.params.get('psk')    
    description = module.params.get('description')

    zcls = ZscalerClient()
    zcls.login()
    ret = zcls.get('vpnCredentials', params=dict(search=ip, type="IP"))

    action = "Nothing"
    changed = False
    _create = False
    _update = False
    _delete = False 

    if state == 'present':
        if len(ret) == 0: 
            _create = True
    elif state == 'absent':
        if len(ret) < 0:
            _delete = True 

    payload = None
    if len(ret) != 0:
        payload = zcls.get('vpnCredentials/{0}'.format(ret[0]['id']))
    
    if payload != None:
        if not 'comments' in payload: 
            _update = True
        elif 'comments' in payload and payload['comments'] != description:
            _update = True

    try:
        if _create:
            payload = {
                "ipAddress": ip,
                "comments": description,
                "type": "IP",
                "preSharedKey": psk
            }
            if not module.check_mode:
                zcls.post('vpnCredentials', payload)
            changed = True
            action = "Create"
        if _update:
            payload['comments'] = description
            payload['preSharedKey'] = psk
            if not module.check_mode:
                result = zcls.put('vpnCredentials/{0}'.format(ret[0]['id']), payload)
            changed = True
            action = "Update"
        if _delete: 
            if not module.check_mode:
                zcls.delete('vpnCredentials/{0}'.format(ret[0]['id']))
            action = "Delete"
            changed = True

    except Exception as err:
        module.fail_json(msg=str(err), get=get, req=req)

    zcls.logout()

    module.exit_json(changed=changed, result=payload, action=action)

if __name__ == "__main__":
    main()