#!/sur/bin/python3.4
# coding: utf8
import configparser
import json
import re
import requests


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

    def send_request(self, reqclass, def_class, sslverify=False):
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
        itop_class = self.config.sections()
        return itop_class

    @staticmethod
    def ansible_add_inventory(host, inventory):
        if inventory is None:
            inventory = {"hosts": [], "vars": {}, "_meta": {"hostvars": {}}}
            inventory["hosts"].append(host)
        else:
            inventory["hosts"].append(host)
        return inventory

    def ansible_group(self, host, inventory, itop_class, srv):
        group_filter = self.config.get(itop_class, "group_filter").replace(" ", "").split(",")
        for group in group_filter:
            if group not in inventory:
                inventory[srv.get(group)] = []
                inventory[srv.get(group)].append(host)
            else:
                inventory[srv.get(group)].append(host)
        return inventory

    @staticmethod
    def ansible_meta_vars(host, inventory, meta_vars):
        if host not in inventory["_meta"]["hostvars"]:
            inventory["_meta"]["hostvars"][host] = {}
            inventory["_meta"]["hostvars"][host][meta_vars] = "True"
        else:
            inventory["_meta"]["hostvars"][host][meta_vars] = "True"
        return inventory

    @staticmethod
    def if_str_in_data(str, data):
        if str in data:
            if data[str]:
                return data[str]

    def find_str_dict(self, fstr, data):
        find_list = []
        for key in data:
            if isinstance(data[key], list):
                for i in data[key]:
                    find_list.append(self.if_str_in_data(fstr, i))
                    if isinstance(i, dict):
                        self.find_str_dict(fstr, i)

        return find_list

    @staticmethod
    def search_itop_elem(http_req):
        elem = []
        for i in http_req:
            if i == "objects":
                for a in http_req[i]:
                    elem.append(http_req[i][a]['fields'])
        return elem

    def ansible_roles_mapping(self, roles_mapping, srv, host, inventory):
        for roles in roles_mapping:
            if roles not in srv:
                list_mapping = self.find_str_dict(roles, srv)
                for meta_vars in list_mapping:
                    if meta_vars is not None:
                        inventory = self.ansible_meta_vars(host, inventory, meta_vars)
            else:
                if srv.get(roles):
                    inventory = self.ansible_meta_vars(host, inventory, srv.get(roles))
        return inventory

    def ansible_inventory(self):
        inventory = None
        pattern = re.compile("^class::[a-zA-Z]+$")
        for itop_class in self.get_itop_classes():
            if pattern.match(itop_class):
                config_class = itop_class.split('::')
                http_return = self.send_request(itop_class, config_class)
                data_elem = self.search_itop_elem(http_return)
                for srv in data_elem:
                    host = srv.get("name").replace(" ", "_")
                    inventory = self.ansible_add_inventory(host, inventory)
                    inventory = self.ansible_group(host, inventory, itop_class, srv)
                    roles_mapping = self.config.get(itop_class, "roles_mapping").replace(" ", "").split(",")
                    inventory = self.ansible_roles_mapping(roles_mapping, srv, host, inventory)

        return json.dumps(inventory, indent=2)

if __name__ == '__main__':
    ansible_inventory = ItopInventory("config.ini").ansible_inventory()
    print(ansible_inventory)
