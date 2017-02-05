#/usr/bin/python3.4
# coding: utf8
import requests
import json
import configparser
import re
import json
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

    def ifstrindata(self,str, data):
        if str in data:
            return data[str]

    def find_str_dict(self, fstr, data):
        findlist = []
        for key in data:
            if isinstance(data[key], dict):
                findlist.append(self.ifstrindata(fstr, data[key]))
                devicedict = data[key]
                self.find_str_dict(fstr, devicedict)
            elif isinstance(data[key], list):
                for i in data[key]:
                    findlist.append(self.ifstrindata(fstr, i))
                    if isinstance(i, dict):
                        self.find_str_dict(fstr, i)
        return findlist

    def searchitopelem(self, httpreq):
        elem = []
        for i in httpreq:
            if i == "objects":
                for a in httpreq[i]:
                    elem.append(httpreq[i][a]['fields'])
        return elem


    def run(self):
        pattern = re.compile("^class::[a-zA-Z]{1,}$")
        for v in self.get_itop_classes():
            if pattern.match(v):
                configclass = v.split('::')
                httpret = self.send_request(v, configclass)
                dataelem = self.searchitopelem(httpret)
                for srv in dataelem:
                    print(srv)
                    print(srv.get("name"))
                    print(srv.get("organization_name"))
                    if self.config.get(v, "test") not in srv:
                        print(self.find_str_dict(self.config.get(v, "test"), srv))

if __name__ == '__main__':
    ItopInventory("config.ini").run()