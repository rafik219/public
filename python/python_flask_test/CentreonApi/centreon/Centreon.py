#!/usr/bin/env python2.7
# -*- coding: utf-8

# """""""""""""""""""""""
# @uthor: rbo
# version: 18/10/2017

# Centreon class utility
# need python2.7
#
# required package:
# easy_install pip
# pip install configparser
#
# """"""""""""""""""""""""""

import getopt
import json
import os
import sys
import time
import xml.etree.ElementTree as ElementTree
from datetime import datetime

import configparser
import requests


# from config.InitConfig import *


def usage():
    print "---------------------------------------------------------"
    script_name = sys.argv[0]
    print "Usage : \n" \
          "\t %s -g <val> -s <Yes/No>\n" \
          "\t %s --get <val> --save <Yes/No>\n" \
          "" % (script_name, script_name)
    print "Ou: \n" \
          "\t <val> = critical_service         : Get critical service status"
    print "\t       = critical_service_by_pop  : Get Critical service status by pop"
    print "\t       = all_host                 : Get list hosts"
    print "\t       = all_pop                  : Get list pop group by hosts"
    print "\n"
    print "\t <Yes/No> = Yes  : Generate JSON file"
    print "\t <Yes/No> = No   : Get result to standard output"
    print "---------------------------------------------------------"
    sys.exit(1)


def version():
    print "version 0.2"


class Centreon:
    config_file = os.path.abspath(os.path.join(os.path.realpath(__file__), "../../config/Centreon.ini"))

    def __init__(self):
        self.centreon_host = ""
        self.centreon_http_port = ""
        self.centreon_username = ""
        self.centreon_password = ""
        self.centreon_access_url = ""
        self.centreon_service_status_url = ""
        self.centreon_all_host_url = ""
        self.centreon_xml_all_host = ""
        self.centreon_xml_critical_service_status = ""
        self.centreon_xml_all_service_for_host = ""
        self.centreon_all_service_for_host_url = ""
        self.serialized_service_file = ""
        self.serialized_host_file = ""
        self._get_configuration()

    def _get_configuration(self):
        try:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), "data")
            data_dir_new = os.path.join(data_dir, datetime.now().strftime("%Y/%m/%d"))
            config = configparser.ConfigParser()
            config.read(Centreon.config_file)
            self.centreon_host = config['Centreon']['ip_addr']
            self.centreon_http_port = config['Centreon']['http_port']
            self.centreon_username = config['Centreon']['username']
            self.centreon_password = config['Centreon']['password']
            self.serialized_service_file = os.path.join(data_dir_new, config['Centreon']['critical_service_filename'])
            self.serialized_host_file = os.path.join(data_dir_new, config['Centreon']['host_filename'])
        except Exception, ex:
            print("ERROR: during getting configuration from {0}, cause: {1}".format(Centreon.config_file, ex))
            sys.exit(-2)

        # print(data_dir, data_dir_new)

    def _init_request(self):
        self.centreon_access_url = \
            "http://{0}:{1}/centreon/index.php".format(self.centreon_host, self.centreon_http_port)

        self.centreon_service_status_url = \
            "http://{0}:{1}/centreon/include/monitoring/status/Services/xml/ndo/serviceXML.php" \
                .format(self.centreon_host, self.centreon_http_port)

        self.centreon_all_host_url = \
            "http://{0}/centreon/include/monitoring/status/Hosts/xml/ndo/hostXML.php".format(self.centreon_host)

        self.centreon_all_service_for_host_url = \
            "http://{0}/centreon/include/monitoring/status/Services/xml/ndo/serviceXML.php".format(self.centreon_host)

    def _get_xml_response(self, type_=None, search_host=None):
        self._init_request()
        http_session = requests.Session()
        payload_data = {
            'useralias': self.centreon_username,
            'password':  self.centreon_password,
            'submit':    'Connect'
        }
        # make POST request to authenticate to centreon with login/password and get PHPSESSID
        try:
            post_request = http_session.post(self.centreon_access_url, data=payload_data)
            if post_request.status_code != 200:
                print("ERROR: server responds with {0} for this request {1}".format(post_request.status_code,
                                                                                  self.centreon_access_url))
                sys.exit(-1)
        except Exception, ex:
            print("Authentication failed to: %s with login: %s pass: %s, cause : %s" % (
                self.centreon_access_url, self.centreon_username, self.centreon_password, ex))
            sys.exit(-2)
        request_sid = http_session.cookies.get_dict().get('PHPSESSID')
        if type_ == 'critical_service':
            # make GET request to get critical service status
            payload_params = {
                'sid':                     request_sid,
                'search':                  '',
                'search_host':             '',
                'search_output':           '',
                'num':                     '0',
                'limit':                   '100000',  # we assume that we have not more then 100000 checks on Nagios
                'sort_type':               'criricality_id',
                'order':                   'ASC',
                'date_time_format_status': 'd/m/Y H:i:s',
                'o':                       'svc_critical',
                'p':                       '20201',
                'host_name':               '',
                'nc':                      '0',
                'criticality':             '0'
            }
            try:
                get_request = http_session.get(self.centreon_service_status_url, params=payload_params)
                self.centreon_xml_critical_service_status = get_request.content
            except Exception, ex:
                print("Failed to send GET request, cause: %s" % ex)
                sys.exit(-3)

        elif type_ == 'all_host':
            payload_params = {
                'sid':                     request_sid,
                'search':                  '',
                'num':                     '0',
                'limit':                   '10000',  # we assume that we have not more then 10000 servers on Nagios
                'sort_type':               '',
                'order':                   'ASC',
                'date_time_format_status': 'd/m/Y H:i:s',
                'o':                       'h',
                'p':                       '20102',
                'time':                    str(int(time.time())),
                'criticality':             '0'
            }
            try:
                get_request = http_session.get(self.centreon_all_host_url, params=payload_params)
                self.centreon_xml_all_host = get_request.content
            except Exception, ex:
                print("Failed to send GET request, cause: %s" % ex)
                sys.exit(-4)

        elif type_ == 'all_service_for_host' and search_host is not None:
            payload_params = {
                'sid':                     request_sid,
                'search_host':             search_host,
                'search_output':           '',
                'num':                     '0',
                'limit':                   '500',
                'sort_type':               'criticality_id',
                'order':                   'ASC',
                'date_time_format_status': 'd/m/Y%20H:i:s',
                'o':                       'svc',
                'p':                       '20201',
                'host_name':               '',
                'nc':                      '0',
                'criticality':             '0'
            }
            try:
                get_request = http_session.get(self.centreon_all_service_for_host_url, params=payload_params)
                print(get_request.url)
                self.centreon_xml_all_service_for_host = get_request.content
            except Exception, ex:
                print("Failed to send GET request, cause: %s" % ex)
                sys.exit(-5)

    def _format_xml_response(self, type_=None):
        if type_ == 'critical_service':
            self._get_xml_response(type_='critical_service')
            xml_root = ElementTree.fromstring(self.centreon_xml_critical_service_status)
            critical_service = list()
            for list_down in xml_root.findall('l'):
                critical_host_status_dict_tmp = dict()
                critical_service_dict_tmp = dict()
                critical_host_status_dict_tmp["host_name"] = list_down.find('hnl').text
                critical_service_dict_tmp["service_name"] = list_down.find('sd').text
                critical_service_dict_tmp["check_status"] = list_down.find('cs').text
                critical_service_dict_tmp["check_info"] = list_down.find('po').text
                critical_service_dict_tmp["check_duration"] = list_down.find('d').text
                critical_service_dict_tmp["last_hard_state_change"] = list_down.find('last_hard_state_change').text
                critical_service_dict_tmp["last_check"] = list_down.find('lc').text
                critical_service_dict_tmp["disable_notification"] = list_down.find('ne').text
                critical_service_dict_tmp["tries"] = list_down.find('ca').text
                critical_host_status_dict_tmp["service_down"] = critical_service_dict_tmp
                if list_down.find('hn').get('none') == '0':
                    critical_host_status_dict_tmp["host_ip"] = list_down.find('hip').text
                else:
                    critical_host_status_dict_tmp["host_ip"] = None
                critical_service.append(critical_host_status_dict_tmp)
            return critical_service
        elif type_ == 'all_host':
            self._get_xml_response(type_='all_host')
            xml_root = ElementTree.fromstring(self.centreon_xml_all_host)
            all_host = list()
            for list_host in xml_root.findall('l'):
                host_status_dict_tmp = dict()
                host_status_dict_tmp['host_name'] = list_host.find('hnl').text
                host_status_dict_tmp['host_ip'] = list_host.find('a').text
                host_status_dict_tmp['host_status'] = list_host.find('cs').text
                all_host.append(host_status_dict_tmp)
            return all_host

    def get_all_service_for_host(self, search_host=None):
        self._get_xml_response(type_='all_service_for_host', search_host=search_host)
        xml_root = ElementTree.fromstring(self.centreon_xml_all_service_for_host)
        host_description = dict()
        list_service_war = list()
        list_service_ok = list()
        list_service_cri = list()
        list_service_unk = list()
        host_description["count_ok_service"] = 0
        host_description["count_cri_service"] = 0
        host_description["count_war_service"] = 0
        host_description["count_unk_service"] = 0
        host_name = ""
        one_access = True
        for elt in xml_root.findall('i'):
            host_description["count_all_service"] = elt.find('numrows').text
        for service in xml_root.findall('l'):
            service_war_description = dict()
            service_cri_description = dict()
            service_ok_description = dict()
            service_unk_description = dict()
            if service.find('hn').get('none') == "0" and one_access:
                host_description["host_ip"] = service.find('hip').text
                host_description["host_name"] = service.find('hnl').text
                host_name = host_description["host_name"]
                one_access = False
            service_status = service.find('cs').text.strip()
            if host_name == service.find('hnl').text:
                if service_status == "WARNING":
                    host_description["count_war_service"] += 1
                    service_war_description["check_name"] = service.find('sd').text
                    service_war_description["check_status"] = service.find('cs').text
                    service_war_description["check_info"] = service.find('po').text
                    list_service_war.append(service_war_description)
                elif service_status == "OK":
                    host_description["count_ok_service"] += 1
                    service_ok_description["check_name"] = service.find('sd').text
                    service_ok_description["check_status"] = service.find('cs').text
                    service_ok_description["check_info"] = service.find('po').text
                    list_service_ok.append(service_ok_description)
                elif service_status == "CRITICAL":
                    host_description["count_cri_service"] += 1
                    service_cri_description["check_name"] = service.find('sd').text
                    service_cri_description["check_status"] = service.find('cs').text
                    service_cri_description["check_info"] = service.find('po').text
                    list_service_cri.append(service_cri_description)
                elif service_status == "UNKNOWN":
                    host_description["count_unk_service"] += 1
                    service_unk_description["check_name"] = service.find('sd').text
                    service_unk_description["check_status"] = service.find('cs').text
                    service_unk_description["check_info"] = service.find('po').text
                    list_service_unk.append(service_unk_description)

        host_description["service_ok"] = list_service_ok
        host_description["service_war"] = list_service_war
        host_description["service_cri"] = list_service_cri
        host_description["service_unk"] = list_service_unk

        return host_description
        # print "count all service: %s" % host_description['count_all_service']
        # print "host name: %s" % host_description['host_name']
        # print "host ip: %s" % host_description['host_ip']
        # print "count war: %s" % host_description['count_war_service']
        # print "count ok: %s" % host_description['count_ok_service']
        # print "count cri: %s" % host_description['count_cri_service']
        # print "count unk: %s" % host_description['count_unk_service']
        # print "service ok: %s" % host_description['service_ok']
        # print "service war: %s" % host_description['service_war']
        # print "service cri: %s" % host_description['service_cri']
        # print "service unk: %s" % host_description['service_unk']

    def group_critical_services_by_hosts(self, critical_service=None):
        if critical_service is None:
            critical_service = self._format_xml_response(type_='critical_service')
        hosts = list()
        found_host = list()
        found_host_inter = list()
        for service in critical_service:
            host_name = service.get('host_name')
            list_service_down = list()
            list_service_down_inter = list()
            service_down_for_host = dict()
            count = 0
            if host_name not in found_host:
                found_host.append(host_name)
                service_down_for_host["host_name"] = host_name
                list_service_down.append(service.get('service_down'))
                service_down_for_host["service_down"] = list_service_down
                service_down_for_host["host_ip"] = service.get('host_ip')
                count += 1
                service_down_for_host["count_down_service"] = count
            else:
                if host_name not in found_host_inter:
                    found_host_inter.append(host_name)
                    for serv in critical_service[critical_service.index(service):]:
                        list_service_down_inter.append(serv.get('service_down'))
                        count += 1
                        if serv.get('host_name') not in found_host:
                            hosts[len(hosts) - 1]["count_down_service"] = count
                            hosts[len(hosts) - 1]["service_down"] += list_service_down_inter[
                                                                     :len(list_service_down_inter) - 1]
                            break
                        elif (critical_service.index(service) + count) == len(critical_service):
                            hosts[len(hosts) - 1]["count_down_service"] = count + 1
                            hosts[len(hosts) - 1]["service_down"] += list_service_down_inter[
                                                                     :len(list_service_down_inter)]
                            break
            if len(service_down_for_host) != 0:
                hosts.append(service_down_for_host)
        return hosts
        # for h in hosts:
        #     print h.get('host_name')
        #     print h.get('host_ip')
        #     print h.get('count_down_service')
        #     for s in h.get('service_down'):
        #         print "\t - %s" % s
        #     print "---------------------------"

    def group_hosts_by_pop(self, list_host=None):
        if list_host is None:
            all_host = self._format_xml_response(type_='all_host')
        else:
            all_host = list_host
        list_pop_tmp = list()
        list_pop = list()
        list_host_pop = list()
        count_host = 0
        for host in all_host:
            host_name = host.get('host_name').upper()
            position1 = host_name.find('_')
            position2 = host_name.find('-')
            if position1 < position2:
                if position1 != -1:
                    host_name = host_name[:position1]
                else:
                    host_name = host_name[:position2]
            else:
                if position2 != -1:
                    host_name = host_name[:position2]
                else:
                    host_name = host_name[:position1]
            pop_name = ""
            pop_description = dict()
            if host_name.isalnum():
                if not host_name.isalpha():
                    for e, ch in enumerate(host_name):
                        if not ch.isalpha():
                            pop_name = host_name[:e].upper()
                            break
                else:
                    pop_name = host_name.upper()
                if pop_name not in list_pop_tmp:
                    list_pop_tmp.append(pop_name.upper())
                    pop_description['pop_name'] = pop_name
                    count_host += 1
                    pop_description['count_host'] = count_host
                    list_host_pop.append(host)
                    pop_description['pop_host'] = list_host_pop
                    list_host_pop = list()
                    count_host = 0
                else:
                    list_pop[len(list_pop) - 1]['pop_host'].append(host)
                    list_pop[len(list_pop) - 1]['count_host'] += 1
            if len(pop_description) != 0:
                list_pop.append(pop_description)
        return list_pop
        # for p in list_all_pop:
        #     print p.get('pop_name')
        #     print p.get('count_host')
        #     for h in p.get('pop_host'):
        #         print "\t - %s" % h
        #     print "----------------------------"

    def get_critical_service_for_host(self):
        pass

    # Create serialized object
    # @staticmethod
    def save_object(self, type_='critical_service', critical_service=None, obj=None):
        epoch = datetime.now().strftime("%Y%m%d_%H%M%S")
        if critical_service is None and obj is None:
            critical_host = self._format_xml_response(type_=type_)
        elif critical_service is not None:
            if len(critical_service) == 0:
                print("Not need to generate empty file, critical_service: %s is empty" % critical_service)
                sys.exit(-5)
        else:
            critical_host = critical_service
        saved_file = ""
        if type_ == 'critical_service':
            saved_file = "{0}_{1}.json".format(self.serialized_service_file, epoch)
        elif type_ == 'all_host':
            saved_file = "{0}_{1}.json".format(self.serialized_host_file, epoch)
        else:
            saved_file = type_

        if obj is not None:
            critical_host = obj
        if not os.path.exists(os.path.dirname(saved_file)):
            try:
                os.makedirs(os.path.dirname(saved_file))
            except Exception, ex:
                print("Error can't create directory : %s, cause: %s" % (os.path.dirname(saved_file), ex))
                sys.exit(-6)
        with open(saved_file, 'w') as serialized_file:
            serialized_file.write(json.dumps(critical_host, indent=4))
        print "OK: file generated on: %s" % saved_file

    # @staticmethod
    def get_all_critical_service(self):
        return self._format_xml_response(type_='critical_service')

    # @staticmethod
    def save_critical_service(self):
        self.save_object(type_='critical_service', obj=self.group_critical_services_by_hosts())

    # @staticmethod
    def saved_all_hosts(self):
        self.save_object(type_='all_host')

    # @staticmethod
    def get_all_hosts(self):
        return self._format_xml_response(type_='all_host')
        # _init_request = staticmethod(_init_request)
        # _get_xml_response = staticmethod(_get_xml_response)
        # _format_xml_response = staticmethod(_format_xml_response)
        # save_object = staticmethod(save_object)


if __name__ == "__main__":
    argument = sys.argv[1:]
    if len(argument) != 4:
        usage()
    opts = None
    args = None
    try:
        opts, args = getopt.getopt(argument, "g:s:h", ["get=", "save="])
    except getopt.GetoptError, ex:
        print str(ex)
        usage()
    param = ""
    save = ""
    for opt, arg in opts:
        if opt in ("-g", "--get"):
            param = arg.strip().lower()
            if param not in ("critical_service", "critical_service_by_pop", "all_host", "all_pop"):
                usage()
        elif opt in ("-s", "--save"):
            save = arg.strip().lower()
            if save not in ("no", "yes"):
                usage()
        else:
            usage()

    # centreon_config file
    # configfile = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "centreon_config/Centreon.ini")
    # create object
    centreonAccess = Centreon()

    if param == "critical_service":
        if save == "no":
            print centreonAccess.group_critical_services_by_hosts()
        elif save == "yes":
            centreonAccess.save_critical_service()
    elif param == "critical_service_by_pop":
        if save == "no":
            print(centreonAccess.group_hosts_by_pop(list_host=centreonAccess.group_critical_services_by_hosts()))
        elif save == "yes":
            print("Sorry: this Option is not implemented !")
            # centreonAccess.save_critical_service()
            # centreonAccess.save_object(critical_service=centreonAccess.group_critical_services_by_hosts())
    elif param == "all_host":
        if save == "no":
            print centreonAccess.get_all_hosts()
        elif save == "yes":
            centreonAccess.saved_all_hosts()
    elif param == "all_pop":
        if save == "no":
            print centreonAccess.group_hosts_by_pop()
        elif save == "yes":
            centreonAccess.save_object(type_='all_host', obj=centreonAccess.group_hosts_by_pop())

    print "SUCCESS !!"
