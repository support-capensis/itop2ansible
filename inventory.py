#/usr/bin/python3.4
# coding: utf8
import requests
import json
import configparser
import re
import json
import argparse

class itopobje(object):
    def __init__(self, configfile):
        config = ConfigParser.ConfigParser()
        self.config = config
        try:
            with open(configfile) as f:
                config.readfp(f)
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

    def ifstrindata(str, data):
        if str in data:
            return data[str]

    def find_str_dict(fstr, data):
        findlist = []
        for key in data:
            if isinstance(data[key], dict):
                findlist.append(ifstrindata(fstr, data[key]))
                devicedict = data[key]
                find_str_dict(fstr, devicedict)
            elif isinstance(data[key], list):
                for i in data[key]:
                    findlist.append(ifstrindata(fstr, i))
                    if isinstance(i, dict):
                        find_str_dict(fstr, i)
        return findlist

    def searchitopelem(httpreq):
        elem = []
        for i in httpreq:
            if i == "objects":
                for a in httpreq[i]:
                    elem.append(httpreq[i][a]['fields'])
        return elem

objt = itopobje("config.ini")
retreq = itopobje.send_request()
result = searchitopelem(retreq)
# find_str_dict("organization_name", retreq)
for i in result:
    print(i.get("name"))
    print(i.get("organization_name"))
    if "applicationsolution_id_friendlyname" not in i:
        print(find_str_dict('applicationsolution_name', i))
        # NONE NONE PROBLEM
        # CHECK RETURN FOR DEEP SEARCH IN DICT
        # find_str_dict("organization_name", retreq)
        # print(json.dumps(retreq, indent=4))
        # find_str_dict('applicationsolution_id_friendlyname', retreq)