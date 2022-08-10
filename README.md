# :warning: This module is not offical
This modules is not supported by zscaler or his retailers

# Zscaler Ansible Module

## Configuration

Create a file in the user home path : ~/.zscalercf.json
```
{  
    "tenant_name": "<Specifed the name for your tenant API  ex: zsapi.zscloud.net>",
    "api_version": "v1",
    "api_key": "<insert key here>",
    "username": "<insert username here>",
    "password": "<insert password here>"
}
```

## Examples

### Static IP

Add / Update Object
```
    - name: "Static IP"
      zscaler_staticip:
        ip: "99.99.99.99"
        location: "Paris"
        description: "Orange Prim ISP"
        state: "present"
```

Delete Object
```
    - name: "Static IP"
      zscaler_staticip:
        ip: "99.99.99.99"
        state: "absent"
```

### VPN Credentials

Add / Update Object
```
    - name: "VPN Credential"
      zscaler_vpncredentials:
        ip: "99.99.99.99"
        psk: "< psk >"
        description: "Orange Prim ISP"
        state: "present"
```

Delete Object
```
    - name: "VPN Credential"
      zscaler_vpncredentials:
        ip: "99.99.99.99"
        state: "absent"
```

### Location / Sublocation

Add / Update Location
```
  - name: "Location"
      zscaler_locations:
        name: "Test-Loc1"
        state: "present"
        upBandwidth: "20"
        dnBandwidth: "20"
        countryCode: "FR"
        tz: "Europe/Paris"
        profile: "CORPORATE"
        description: "My Location on Orange Prim"
        vpnCredentials: [ "99.99.99.99" ]
        city: "Paris"
```

Add / Update SubLocation
```
    - name: "Sublocation"
      zscaler_locations:
        state: "present"
        subLocation: true
        parentName: "Test-Loc1"
        name: "SubLoc1"
        ipAddresses:
          - "192.168.1.0-192.168.1.255"
        profile: "CORPORATE"
        groups:
          - "MyGroup"
        ofwEnabled: true
```

Delete Location
```
  - name: "Location"
      zscaler_locations:
        name: "Test-Loc1"
        state: "absent"
```

Delete SubLocation
```
  - name: "Location"
      zscaler_locations:
        subLocation: true
        parentName: "Test-Loc1"
        name: "SubLoc1"
        state: "absent"
```
