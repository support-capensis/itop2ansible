#!/usr/bin/python3
# coding: utf8
import configparser
import json
import re
import requests
import argparse


class ItopInventory(object):
    def __init__(self):
        config = configparser.ConfigParser()
        self.config = config
        try:
            with open("/etc/itop2inventory/config.ini") as f:
                config.read_file(f)
        except IOError:
            print("No config.ini file found")
        self.pattern = re.compile("^[a-zA-Z]+::[0-9]+$")
        self.url = self.config.get("itop", "url")
        self.user = self.config.get("itop", "user")
        self.api_pass = self.config.get("itop", "passwd")

    def itop_inventory(self):
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '--output-indent', dest='indent', type=int, default=4,
            help='Set number of space to indent output'
        )
        parser.add_argument(
            '--inventory', '-i', dest='inventory', type=str,
            help='default ansible, set output type inventory (icinga2, rundeck)'
        )
        parser.add_argument(
            '--show-api-output', dest='http_output', action='store_true',
            help='for debugging purpose show output of api'
        )
        parser.add_argument(
            '--list', dest='ansible_list', action='store_true',
            help='list ansible'
        )
        parsed_args = parser.parse_args()
        if parsed_args.inventory is None:
            return self.ansible_inventory(parsed_args)

    def send_request(self, reqclass, def_class, sslverify=False):
        """
        Send request to ITOP Api
        """
        filter = self.config.get(reqclass, "filter")
        req = "{\"operation\":\"core/get\",\"" + def_class[0] + "\":\"" + def_class[1] + "\",\"key\":\"SELECT " + \
              def_class[1] + "\",\"output_fields\":\"*\"}"
        params = {"version": self.config.get("itop", "version"), "json_data": req}

        if filter:
            params["json_data"] = (params["json_data"].replace("*", filter))

        if not sslverify:
            from requests.packages.urllib3.exceptions import InsecureRequestWarning
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

        try:
            itop_api_request = requests.post(self.url, auth=(self.user, self.api_pass), params=params, verify=False)
            response = itop_api_request.json()
            return response
        except json.JSONDecodeError:
            print("HTTP error unable to connect to Itop API")
            exit(1)

    def get_itop_classes(self):
        """
        Get top level ini definition in config file
        """
        itop_class = self.config.sections()
        return itop_class

    @staticmethod
    def ansible_add_inventory(inventory):
        """
        Create and add host to a simple ansible inventory
        """
        if inventory is None:
            inventory = {
                "_meta": {
                    "hostvars": {},
                }
            }
        return inventory

    def ansible_add_prefix(self, itop_class, meta_var, prefix):
        add_prefix = self.config.get(itop_class, prefix)
        if add_prefix:
            meta_var = add_prefix + "_" + meta_var
            return meta_var
        else:
            return meta_var

    def ansible_group(self, host, inventory, itop_class, srv):
        """
        Add host to group from what's defined in the config file
        """
        group_filter = self.config.get(itop_class, "group_filter").replace(" ", "").split(",")
        for group in group_filter:
            special_group = self.find_elem_dict(group, srv)
            if srv.get(group):
                inventory = self.ansible_add_group(inventory, srv.get(group), host)
            elif special_group:
                for new_group in special_group:
                    inventory = self.ansible_add_group(inventory, new_group, host)
        return inventory

    @staticmethod
    def ansible_add_group(inventory, group, host):
        if group is None:
            return inventory
        else:
            group = group.replace(" ", "_")

        if group not in inventory:
            inventory[group] = {
                "hosts": [],
                "vars": {},
            }
            inventory[group]["hosts"].append(host)
        else:
            inventory[group]["hosts"].append(host)
        return inventory

    @staticmethod
    def ansible_meta_vars(host, inventory, meta_vars):
        """
        Add boolean var for role mapping of host in the _meta key of the inventory
        """
        if host not in inventory["_meta"]["hostvars"]:
            inventory["_meta"]["hostvars"][host] = {}
            inventory["_meta"]["hostvars"][host][meta_vars] = True
        else:
            inventory["_meta"]["hostvars"][host][meta_vars] = True
        return inventory

    def ansible_add_vars(self, host, inventory, srv, srv_elem, itop_class):
        """
        Add special var for a host in the _meta key of the inventory
        """
        if host not in inventory["_meta"]["hostvars"]:
            inventory["_meta"]["hostvars"][host] = {}
            inventory["_meta"]["hostvars"][host][self.ansible_add_prefix(itop_class, srv_elem, "prefix")] = srv.get(
                srv_elem)
        else:
            inventory["_meta"]["hostvars"][host][self.ansible_add_prefix(itop_class, srv_elem, "prefix")] = srv.get(
                srv_elem)
        return inventory

    @staticmethod
    def check_exist(check_str, data):
        """
        check if a string is in an element(dict, list)
        """
        if check_str in data:
            if data[check_str]:
                return data[check_str]

    def find_elem_dict(self, search_elem, data):
        """
        Check if element(search_elem) exist in hashtable(data)
        """
        find_list = []
        for key in data:
            if isinstance(data[key], list):
                for elem in data[key]:
                    find_list.append(self.check_exist(search_elem, elem))
                    if isinstance(elem, dict):
                        self.check_exist(search_elem, elem)
        return find_list

    @staticmethod
    def search_itop_srv(http_req):
        """
        Search for itop object(hashtable) in http return request
        """
        elem = []
        for i in http_req:
            if i == "objects":
                for a in http_req[i]:
                    elem.append(http_req[i][a]['fields'])
        return elem

    def ansible_roles_mapping(self, roles_mapping, srv, host, inventory, itop_class):
        """
        Add roles by settings witch value to map as a role in itop data
        from config in role_mapping value
        """
        for roles in roles_mapping:
            if roles not in srv:
                list_mapping = self.find_elem_dict(roles, srv)
                for meta_vars in list_mapping:
                    if meta_vars is not None:
                        inventory = self.ansible_meta_vars(host, inventory,
                                                           self.ansible_add_prefix(itop_class, meta_vars,
                                                                                   "role_prefix"))
            else:
                if srv.get(roles):
                    inventory = self.ansible_meta_vars(host, inventory,
                                                       self.ansible_add_prefix(itop_class, srv.get(roles),
                                                                               "role_prefix"))
        return inventory

    def get_name (self, itop_class, srv):
        name_mapping = self.config.get(itop_class, "name",)
        try:
            host = srv.get(name_mapping).replace(" ", "_")
        except AttributeError:
            host = self.find_elem_dict(name_mapping, srv)
        return host

    def make_inventory(self, host, itop_class, srv, inventory):
        inventory = self.ansible_add_inventory(inventory)
        inventory = self.ansible_group(host, inventory, itop_class, srv)
        roles_mapping = self.config.get(itop_class, "roles_mapping").replace(" ", "").split(",")
        inventory = self.ansible_roles_mapping(roles_mapping, srv, host, inventory, itop_class)
        for srv_elem in srv:
            inventory = self.ansible_add_vars(host, inventory, srv, srv_elem, itop_class)
        return inventory

    def ansible_inventory(self, args):
        """
        Set complete inventory
        """
        inventory = None
        pattern = re.compile("^class::[a-zA-Z]+$")
        for itop_class in self.get_itop_classes():
            if pattern.match(itop_class):
                config_class = itop_class.split('::')
                http_return = self.send_request(itop_class, config_class)
                if args.http_output:
                    print(json.dumps(http_return, indent=args.indent))
                    exit(1)
                data_elem = self.search_itop_srv(http_return)
                for srv in data_elem:
                    hosts = self.get_name(itop_class, srv)
                    if type(hosts) == list:
                        for host in hosts:
                            inventory = self.make_inventory(host, itop_class, srv, inventory)
                    else:
                        host = hosts
                        inventory = self.make_inventory(host, itop_class, srv, inventory)
        return json.dumps(inventory, indent=args.indent)

    def __call__(self, *args, **kwargs):
        ansible_inventory = self.itop_inventory()
        return ansible_inventory