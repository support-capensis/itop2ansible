#!/usr/bin/python3.4
# coding: utf8
import configparser
import json
import re
import requests
import argparse

class ItopInventory(object):
    def __init__(self, configfile):
        config = configparser.ConfigParser()
        self.config = config
        try:
            with open(configfile) as f:
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
            '--output-indent', dest='indent', type=int,
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
    def ansible_add_inventory(host, inventory):
        """
        Create and add host to a simple ansible inventory
        """
        if inventory is None:
            inventory = {"hosts": [], "vars": {}, "_meta": {"hostvars": {}}}
            inventory["hosts"].append(host)
        else:
            inventory["hosts"].append(host)
        return inventory

    @staticmethod
    def ansible_group_format(group_name):
        pattern = re.compile("^[A-Za-z0-9\s]{1,}$")
        if pattern.match(group_name):
            return group_name.replace(" ", "_")
        else:
            return group_name

    def ansible_group(self, host, inventory, itop_class, srv):
        """
        Add host to group from what's defined in the config file
        """
        group_filter = self.config.get(itop_class, "group_filter").replace(" ", "").split(",")
        for group in group_filter:
            if group not in inventory:
                group_name = self.ansible_group_format(srv.get(group))
                inventory[group_name] = []
                inventory[group_name].append(host)
            else:
                inventory[group_name].append(host)
        return inventory

    @staticmethod
    def ansible_meta_vars(host, inventory, meta_vars):
        """
        Add special var for a host in the _meta key of the inventory
        """
        if host not in inventory["_meta"]["hostvars"]:
            inventory["_meta"]["hostvars"][host] = {}
            inventory["_meta"]["hostvars"][host][meta_vars] = "True"
        else:
            inventory["_meta"]["hostvars"][host][meta_vars] = "True"
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

    def ansible_roles_mapping(self, roles_mapping, srv, host, inventory):
        """
        Add roles by settings witch value to map as a role in itop data
        from config in role_mapping value
        """
        for roles in roles_mapping:
            if roles not in srv:
                list_mapping = self.find_elem_dict(roles, srv)
                for meta_vars in list_mapping:
                    if meta_vars is not None:
                        inventory = self.ansible_meta_vars(host, inventory, meta_vars)
            else:
                if srv.get(roles):
                    inventory = self.ansible_meta_vars(host, inventory, srv.get(roles))
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
                    host = srv.get("name").replace(" ", "_")
                    inventory = self.ansible_add_inventory(host, inventory)
                    inventory = self.ansible_group(host, inventory, itop_class, srv)
                    roles_mapping = self.config.get(itop_class, "roles_mapping").replace(" ", "").split(",")
                    inventory = self.ansible_roles_mapping(roles_mapping, srv, host, inventory)

        return json.dumps(inventory, indent=args.indent)

if __name__ == '__main__':
    ansible_inventory = ItopInventory("config.ini").itop_inventory()
    print(ansible_inventory)
