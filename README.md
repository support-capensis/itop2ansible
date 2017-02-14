# Itop2ansible

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
version =

[class::Server]
# Only filter top level field and make vars with them ( ex: prefix + fieldname )
filter = name, organization_name, applicationsolution_list
# make group for ansible select a top level unit
group_filter = organization_name
# How to map vars with role 
roles_mapping = applicationsolution_list::applicationsolution_name
# Prefix of vars of role_mapping for ansible
roles_prefix = role
# Prefix of vars not from role mapping
prefix = itop

[class::NetworkDevice]
# Only filter top level field and make vars with them ( ex: prefix + fieldname )
filter = name, organization_name, applicationsolution_list
# make group for ansible select a top level unit
group_filter = organization_name
# How to map vars with role 
roles_mapping = applicationsolution_list::applicationsolution_name
# Prefix of vars of role_mapping for ansible
roles_prefix = role
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


## Environement

python 3.4

## License

MIT/BSD

## Author Information

Gregory O'Toole/CAPENSIS - 2016
