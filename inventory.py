#/usr/bin/python3.4
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

    def ansible_inventory(self, host, inventory):
        if inventory == None:
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

    def ifstrindata(self,str, data):
        if str in data:
            return data[str]

    def find_str_dict(self, fstr, data):
        findlist = []
        for key in data:
            """if isinstance(data[key], dict):
                findlist.append(self.ifstrindata(fstr, data[key]))
                devicedict = data[key]
                print("la1")
                self.find_str_dict(fstr, devicedict)"""
            if isinstance(data[key], list):
                for i in data[key]:
                    findlist.append(self.ifstrindata(fstr, i))
                    #print("la2")
                    if isinstance(i, dict):
                        #print("la3")
                        self.find_str_dict(fstr, i)
        return findlist

    def searchitopelem(self, httpreq):
        elem = []
        for i in httpreq:
            if i == "objects":
                for a in httpreq[i]:
                    elem.append(httpreq[i][a]['fields'])
        return elem


    def AnsibleInventory(self):
        inventory = None
        pattern = re.compile("^class::[a-zA-Z]{1,}$")
        for v in self.get_itop_classes():
            if pattern.match(v):
                configclass = v.split('::')
                httpret = self.send_request(v, configclass)
                dataelem = self.searchitopelem(httpret)
                for srv in dataelem:
                    host = srv.get("name").replace(" ", "_")
                    inventory = self.ansible_inventory(host, inventory)
                    inventory = self.ansible_group(host, srv.get("organization_name"), inventory)
                    rolesmapping = self.config.get(v, "roles_mapping").replace(" ", "").split(",")
                    for roles in rolesmapping:
                        if roles not in srv:
                            varmapping = self.find_str_dict(roles, srv)
                            for metavars in varmapping:
                                inventory = self.ansible_metavars(host, inventory, metavars)
                        else:
                            inventory = self.ansible_metavars(host, inventory, srv.get("roles"))
        print(json.dumps(inventory, indent=2))

### Revoir def find_str_dict

if __name__ == '__main__':
    ItopInventory("config.ini").AnsibleInventory()