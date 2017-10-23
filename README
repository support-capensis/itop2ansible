# Itop2inventory

## Purpose


Itop2inventory is made to convert itop cmdb entry to an ansible/icinga/rundeck inventory

## Requierement

 - Python >= 3

## Setup

 - Clone repository
 - define credential and filter in config.ini
 - invoke inventory

## Config.ini

```
[itop]
# Itop api url (example : https://foobar.com/webservices/rest.php)
url = 
# Itop api user (user as to be allow in itop configuration)
user = 
# Itop password
passwd = 
# Set api version ( latest version 1.3 )
version = 1.3

[class::Server]
# Only filter top level field and make vars with them ( ex: prefix + fieldname )
filter = name, organization_name, applicationsolution_list
# make group for ansible select a top level unit
group_filter = organization_name
# How to map vars with role
roles_mapping = applicationsolution_name
# Prefix of vars of role_mapping for ansible
role_prefix = role
# Prefix of vars not from role mapping
prefix = itop

[class::NetworkDevice]
# Only filter top level field and make vars with them ( ex: prefix + fieldname )
filter = name, organization_name, applicationsolution_list
# make group for ansible select a top level unit
group_filter = organization_name
# How to map vars with role
roles_mapping = applicationsolution_name
# Prefix of vars of role_mapping for ansible
role_prefix = role
# Prefix of vars not from role mapping
prefix = itop
```

If user as no right in itop that's the return the script give: 

```
{
    "_meta": {
        "hostvars": {}
    }
}
```

## Itop output 
```
"Server3": {
                "itop_name": "Server3",
                "itop_applicationsolution_list": [
                    {
                        "friendlyname": "13 3",
                        "applicationsolution_id": "13",
                        "applicationsolution_id_friendlyname": "itop",
                        "applicationsolution_name": "itop"
                    },
                    {
                        "friendlyname": "36 3",
                        "applicationsolution_id": "36",
                        "applicationsolution_id_friendlyname": "icinga2-client",
                        "applicationsolution_name": "icinga2-client"
                    }
                ],
                "itop_organization_name": "Demo"
            },

```

## Ansible output

```
    "_meta": {
        "hostvars": {
            "Server3": {
                    "itop_organization_name": "Demo",
                    "role_itop": "True",
                    "itop_name": "Server3",
                    "role_icinga2-client": "True",
                    "itop_applicationsolution_list": [
                        {
                            "applicationsolution_id_friendlyname": "itop",
                            "friendlyname": "13 3",
                            "applicationsolution_id": "13",
                            "applicationsolution_name": "itop"
                        },
                        {
                            "applicationsolution_id_friendlyname": "icinga2-client",
                            "friendlyname": "36 3",
                            "applicationsolution_id": "36",
                            "applicationsolution_name": "icinga2-client"
                        }
                    ]
                },
            }
        }
    }
```

## Command line option

```
optional arguments:
  -h, --help            show this help message and exit
  --output-indent INDENT
                        Set number of space to indent output
  --inventory INVENTORY, -i INVENTORY
                        default ansible, set output type inventory (icinga2,
                        rundeck)
  --show-api-output     for debugging purpose show output of api
  --list                list ansible
```

## Todo

incorporate icinga2 and rundeck host

## Environement

python 3.4

## License

MIT/BSD

## Author Information

Gregory O'Toole/CAPENSIS - 2016
