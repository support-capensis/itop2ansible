# /usr/bin/python3.4
# coding: utf8
import requests
import configparser
import re
import json


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
        self.passwd = self.config.get("itop", "passwd")

    def send_request(self, reqclass, defclass, sslverify=False):
        self.filter = self.config.get(reqclass, "filter")
        self.group_filter = self.config.get(reqclass, "group_filter").split(",")
        self.req = "{\"operation\":\"core/get\",\"" + defclass[0] + "\":\"" + defclass[1] + "\",\"key\":\"SELECT " + \
                   defclass[1] + "\",\"output_fields\":\"*\"}"
        self.params = {"version": self.config.get("itop", "version"), "json_data": self.req}

        if self.filter:
            self.params["json_data"] = (self.params["json_data"].replace("*", self.filter))

        if not sslverify:
            from requests.packages.urllib3.exceptions import InsecureRequestWarning
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

        try:
            r = requests.post(self.url, auth=(self.user, self.passwd), params=self.params, verify=False)
            response = r.json()
            return response
        except requests.exceptions.ConnectionError:
            print("HTTP error unable to connect to Itop API")

    def get_itop_classes(self):
        itopclass = self.config.sections()
        return itopclass

    def ansible_add_inventory(self, host, inventory):
        if inventory is None:
            inventory = {"hosts": [], "vars": {}, "_meta": {"hostvars": {}}}
            inventory["hosts"].append(host)
        else:
            inventory["hosts"].append(host)
        return inventory

    def ansible_group(self, host, group, inventory):
        if group not in inventory:
            inventory[group] = []
            inventory[group].append(host)
        else:
            inventory[group].append(host)
        return inventory

    def ansible_metavars(self, host, inventory, metavars):
        if host not in inventory["_meta"]["hostvars"]:
            inventory["_meta"]["hostvars"][host] = {}
            inventory["_meta"]["hostvars"][host][metavars] = "True"
        else:
            inventory["_meta"]["hostvars"][host][metavars] = "True"
        return inventory

    def if_str_in_data(self, str, data):
        if str in data:
            return data[str]

    def find_str_dict(self, fstr, data):
        find_list = []
        for key in data:
            """ Why that shit !!!!
                if isinstance(data[key], dict):
                findlist.append(self.ifstrindata(fstr, data[key]))
                devicedict = data[key]
                print("la1")
                self.find_str_dict(fstr, devicedict)"""
            if isinstance(data[key], list):
                for i in data[key]:
                    find_list.append(self.if_str_in_data(fstr, i))
                    # print("la2")
                    if isinstance(i, dict):
                        # print("la3")
                        self.find_str_dict(fstr, i)
        return find_list

    def search_itop_elem(self, http_req):
        elem = []
        for i in http_req:
            if i == "objects":
                for a in http_req[i]:
                    elem.append(http_req[i][a]['fields'])
        return elem

    def ansible_inventory(self):
        inventory = None
        pattern = re.compile("^class::[a-zA-Z]{1,}$")
        for v in self.get_itop_classes():
            if pattern.match(v):
                config_class = v.split('::')
                http_return = self.send_request(v, config_class)
                data_elem = self.search_itop_elem(http_return)
                for srv in data_elem:
                    host = srv.get("name").replace(" ", "_")
                    inventory = self.ansible_add_inventory(host, inventory)
                    inventory = self.ansible_group(host, srv.get("organization_name"), inventory)
                    roles_mapping = self.config.get(v, "roles_mapping").replace(" ", "").split(",")
                    for roles in roles_mapping:
                        if roles not in srv:
                            list_mapping = self.find_str_dict(roles, srv)
                            for meta_vars in list_mapping:
                                inventory = self.ansible_metavars(host, inventory, meta_vars)
                        else:
                            inventory = self.ansible_metavars(host, inventory, srv.get("roles"))
        print(json.dumps(inventory, indent=2))


### Revoir def find_str_dict
### Revoir le null dans les metavars

if __name__ == '__main__':
    ItopInventory("config.ini").ansible_inventory()
