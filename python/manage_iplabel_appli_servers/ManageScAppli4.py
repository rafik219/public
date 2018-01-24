#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# author: rbo
# version : 07/12/2016

# install:
# require python2.6
# not tested on python2.7
# yum install python-pip.noarch
# yum install python-paramiko.noarch
# easy_install install pip
# pip install xmltodict
# pip install paramiko
# pip install pywinrm

import getopt
import os
import sys
from datetime import datetime
from time import sleep

import paramiko
import xmltodict
from winrm.protocol import Protocol


def usage():
    print "--------------------------------------------------"
    print "Usage:"
    print "\t %s -f <file> -o <opts> -c <cons> " % sys.argv[0]
    print "\t %s --file <file> --option <opt> --console <con> " % sys.argv[0]
    print "\n<file> = full path xml config file"
    print "\n<opts> = stop \t: Arrete les services" \
          "\n\t start \t: Lancer les services" \
          "\n\t status\t: Afficher le statut des services\n" \
          "\n<cons> = on : Afficher la stdout sur la console" \
          "\n\t off : Afficher la stdout sur un fichier de log"
    print "--------------------------------------------------"
    sys.exit(1)


class ManageSiteCentralServices:
    ssh = None
    winrm = None
    default_xml_file = None
    paramiko_log_file = None
    version = None

    def __init__(self):
        # self.default_xml_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "server_config.xml")
        self.paramiko_log_file = os.path.join(os.path.dirname(__file__), "paramiko.log")
        self.set_paramiko_log_file()
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.set_missing_host_key_policy(paramiko.MissingHostKeyPolicy())
        self.version = "version 0.3"

    def set_xml_file(self, path):
        self.default_xml_file = path

    def set_paramiko_log_file(self):
        paramiko.util.log_to_file(self.paramiko_log_file)

    def get_version(self):
        return self.version

    def init_ssh_connection(self, host, port, login, password):
        try:
            self.ssh.connect(hostname=host, port=int(port), username=login, password=password, timeout=60)
            return True
        except Exception as ex:
            print "\t=> SSH : Authentication failed on server: %s cause: %s" % (host, str(ex))
            return False

    def close_ssh_connection(self):
        self.ssh.close()

    def execute_ssh_shell_cmd(self, cmd):
        try:
            stdin, stdout, stderr = self.ssh.exec_command(cmd)
            while not stdout.channel.recv_exit_status():
                sleep(1)
                break
            while not stderr.channel.recv_exit_status():
                sleep(1)
                break
            return stdout.readlines(), stderr.readlines()
        except Exception as ex:
            print "\t=> Problem when executing command: %s, cause: %s " % (cmd, ex)

    def init_winrm_connection(self, host, port, username, password):
        endpoint = 'https://%s:%s/wsman' % (host, port)
        try:
            self.winrm = Protocol(endpoint=endpoint, transport='ntlm', username=username, password=password,
                                  server_cert_validation='ignore')
            return True
        except Exception as ex:
            print "\t=> WinRM : Authentication failed on server: %s cause: %s" % (host, str(ex))
            return False

    def execute_winrm_shell_cmd(self, cmd):
        stdout = list()
        stderr = list()
        try:
            pars_cmd = cmd.strip().split(' ')
            # print pars_cmd
            command_cmd = pars_cmd[0]
            # print command_cmd
            # param_cmd = pars_cmd.remove(command_cmd) # return None !!!
            param_cmd = pars_cmd[1:]
            # print param_cmd
            shell_id = self.winrm.open_shell()
            command_id = self.winrm.run_command(shell_id, command_cmd, param_cmd)
            stdout, stderr, status_code = self.winrm.get_command_output(shell_id, command_id)
            # print stdout
            # print stderr
            # print status_code
            self.winrm.cleanup_command(shell_id, command_id)
            self.winrm.close_shell(shell_id)
            return stdout, stderr
        except Exception as ex:
            print "\t=> WinRM : Authentication failed, cause: %s" % (str(ex))
            return stdout, stderr

    def get_service_status(self, service, os="linux"):
        # stdout, stderr = self.execute_ssh_shell_cmd("/etc/init.d/" + service + " status")
        # stdout, stderr = self.execute_ssh_shell_cmd("ps -ef | grep -v grep | grep " + service + " | wc -l")
        if os == "linux":
            stdout, stderr = self.execute_ssh_shell_cmd("service " + service + " status")
        elif os == "windows":
            cmd = "sc query %s" % service
            stdout, stderr = self.execute_winrm_shell_cmd(cmd)
            list_tmp = list()
            stdout = r'%s' % stdout
            stdout = stdout.replace(" ", "").replace("\r", "").replace("\n", " ")
            # print stdout
            list_tmp.append(str(stdout))
            stdout = list_tmp
            list_tmp = list()
            stderr = r'%s' % stderr
            stderr = stderr.replace(" ", "").replace("\r", "").replace("\n", " ")
            list_tmp.append(str(stderr))
            stderr = list_tmp

        if len(stdout) != 0:
            status = ""
            for resp in stdout:
                if resp.strip().lower().find('running') != -1:
                    status = "running"
                    break
                elif resp.strip().lower().find('stopped') != -1:
                    status = "stopped"
                    break
                elif resp.strip().lower().find('en cours') != -1:
                    status = "running"
                    break
                elif resp.strip().lower().find('arrêté') != -1:
                    status = "stopped"
                    break
                else:
                    status = "unknown"
            return status
        else:
            data = ""
            for chaine in stderr:
                data = data + chaine.replace("\n", ' ')
            return data

    def manage_service(self, service, action, os):
        service_status = self.get_service_status(service, os)
        if action == "start":
            if service_status == "stopped":
                # self.execute_ssh_shell_cmd("/etc/init.d/" + service + " " + action)
                self.execute_ssh_shell_cmd("service " + service + " " + action)
                return "Service: %s -> started" % service
            elif service_status == "running":
                return "Service: %s -> already running, not need to start it!" % service
            elif service_status == "unknown":
                return "Service: %s -> unknown" % service
            else:
                return service_status
                # pass
                # return "error !! 11"
        elif action == "stop":
            if service_status == "running":
                # self.execute_ssh_shell_cmd("/etc/init.d/" + service + " " + action)
                self.execute_ssh_shell_cmd("service " + service + " " + action)
                return "Service: %s -> stopped" % service
            elif service_status == "stopped":
                return "Service: %s -> already stopped, not need to stop it!" % service
            elif service_status == "unknown":
                return "Service: %s -> unknown" % service
            else:
                return service_status
                # pass
                # return "error !! 22"

    # Parse All xml file and return list of information
    def get_xml_info(self):
        list_serv = list()
        xmldict = dict()
        if not os.path.exists(self.default_xml_file):
            print "File: ' %s ' not found !" % self.default_xml_file
            # raise Exception("File: ' %s ' not found !" % self.default_xml_file)
            sys.exit(-2)
        with open(self.default_xml_file) as file:
            try:
                xmldict = xmltodict.parse(file.read())
            except Exception as ex:
                print "\t\t\t=> Problem on parsing xml file, cause: %s" % str(ex)
                sys.exit(-1)
        if len(xmldict) != 0:
            for server in xmldict['config']['pop']['server']:
                dict_serv = dict()
                list_action_serv = list()
                dict_serv['order'] = server['@order']
                dict_serv['name'] = server['@name']
                dict_serv['os'] = server['@os']
                dict_serv['model'] = server['@model']
                dict_serv['login'] = server['connection']['@login']
                dict_serv['password'] = server['connection']['@password']
                dict_serv['ip'] = server['address']['@ip']
                dict_serv['port'] = server['address']['@port']
                for action in server['actions']['action']:
                    dict_action_serv = dict()
                    dict_action_serv['order'] = action['@order']
                    dict_action_serv['type'] = action['@type']
                    if dict_action_serv['type'] == "service":
                        dict_action_serv['name'] = action['@name']
                    elif dict_action_serv['type'] == "command":
                        dict_action_serv['src'] = action['@src']
                        dict_action_serv['name'] = action['@name']
                        dict_action_serv['use'] = action['@use']
                        dict_action_serv['param'] = action['@param']
                    list_action_serv.append(dict_action_serv)
                    # sort list by order dictionary
                    dict_serv['actions'] = sorted(list_action_serv, key=lambda k: int(k['order']))
                # print sorted(list_action_serv, key=lambda k: k['order'])
                list_serv.append(dict_serv)
        else:
            print "Emty xml file: %s " % self.default_xml_file
            sys.exit(-1)
        return sorted(list_serv, key=lambda k: int(k['order']))

    def display_services_status(self, list_server):
        for server in list_server:
            server_name = server.get('name')
            server_order = server.get('order')
            server_os = server.get('os')
            # print "start connexion to: %s server" % server_name
            print "\n\t[Server: %s] [OS: %s] [Order: %s]" % (server_name, server_os, server_order)
            print "\t|----------------------------------------------------------------------------------------------------"
            print "\t|Type:\t\t|\tName:\t\t|\tOrder:\t|\tCurrent status:\t|\tcount process"
            print "\t|----------------------------------------------------------------------------------------------------"
            if server.get('os').strip().lower() == "windows":
                if self.init_winrm_connection(server.get('ip'), server.get('port'), server.get('login'),
                                              server.get('password')):
                    for action in server.get('actions'):
                        action_type = action.get('type')
                        action_name = action.get('name')  # if action_type == "service" else "----"
                        action_order = action.get('order')
                        # action_current_status = self.get_win_service_status(action_name)
                        action_current_status = self.get_service_status(action_name, os="windows")
                        count_process = "x"
                        if len(action_name) >= 8:
                            print "\t|%s\t|\t%s\t|\t%s\t|\t%s\t\t|\t%s" % (
                                action_type, action_name, action_order, action_current_status, count_process)
                        else:
                            print "\t|%s\t|\t%s\t\t|\t%s\t|\t%s\t\t|\t%s" % (
                                action_type, action_name, action_order, action_current_status, count_process)
                else:
                    print "\t=> WinRM : Connection or Authentication failed"

            elif server.get('os').strip().lower() == "linux":
                if self.init_ssh_connection(server.get('ip'), server.get('port'), server.get('login'),
                                            server.get('password')):
                    for action in server.get('actions'):
                        action_type = action.get('type')
                        action_name = action.get('name')  # if action_type == "service" else "----"
                        action_order = action.get('order')
                        # action_command = "/etc/init.d/" + action_name + " stop" if action_type == "service" else action.get('src')
                        if action_name == "distribHTTPcgm":
                            stdout, stderr = self.execute_ssh_shell_cmd(
                                "ps -ef | grep -v grep | grep centralGetMAI | wc -l")
                        elif action_name == "distribHTTPmmc":
                            stdout, stderr = self.execute_ssh_shell_cmd(
                                "ps -ef | grep -v grep | grep maintenanceMissionC | wc -l")
                        elif action_name == "scenvoitrap":
                            stdout, stderr = self.execute_ssh_shell_cmd(
                                "ps -ef | grep -v grep | grep scEnvoiTrap | wc -l")
                        elif action_name == "ipldist":
                            stdout, stderr = self.execute_ssh_shell_cmd(
                                "ps -ef | grep -v grep | grep -e -gen.pl | wc -l")
                        else:
                            stdout, stderr = self.execute_ssh_shell_cmd(
                                "ps -ef | grep -v grep | grep " + action_name + " | wc -l")
                        count_process = stdout[0].replace("\n", "")
                        if action_name == "crontab":
                            count_process = "x"
                        if action_type == "service":
                            action_current_status = self.get_service_status(action_name, os="linux")
                        elif action_type == "command" and action.get('use') == "like_service":
                            if int(count_process) > 0:
                                action_current_status = "running"
                            else:
                                action_current_status = "stopped"
                        else:
                            action_current_status = "-------"
                        # action_cmd_name =
                        # print "\t%s\t|\t%s\t|\t%s\t\t|\t%s" % (action_type, action_name, action_order, action_command)
                        if len(action_name) >= 8:
                            print "\t|%s\t|\t%s\t|\t%s\t|\t%s\t\t|\t%s" % (
                                action_type, action_name, action_order, action_current_status, count_process)
                        else:
                            print "\t|%s\t|\t%s\t\t|\t%s\t|\t%s\t\t|\t%s" % (
                                action_type, action_name, action_order, action_current_status, count_process)

                    self.close_ssh_connection()
                else:
                    print "\t=> SSH : Connection or Authentication failed"
            else:
                print "\t=> server_config.xml: error type os not managed use (linux or windows)"
            print "\t|----------------------------------------------------------------------------------------------------\n"


if __name__ == "__main__":

    option = None
    console = None
    opts = None
    xml_config_file = None

    argument = sys.argv[1:]
    if len(argument) != 6:
        usage()
    try:
        opts, args = getopt.getopt(argument, "f:o:c:h", ["file=", "option=", "console=", "help="])
    except getopt.GetoptError, e:
        print str(e)
        usage()

    if len(opts) != 0:
        for (opt, arg) in opts:
            if opt in ("-o", "--option"):
                option = arg.lower()
                if option not in ["start", "stop", "status"]:
                    usage()
            elif opt in ("-c", "--console"):
                console = arg.lower()
                if console not in ["on", "off"]:
                    usage()
            elif opt in ("-h", "--help"):
                usage()
            elif opt in ("-f", "--file"):
                xml_config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), arg)
            else:
                usage()
    else:
        usage()

    # create instance
    mange_service = ManageSiteCentralServices()

    if xml_config_file is None:
        print "XML configuration file is None !!"
        sys.exit(-1)
    elif not os.path.exists(xml_config_file):
        print "%s -> Path for XML configuration file NOT FOUND !!" % xml_config_file
        sys.exit(-1)
    else:
        mange_service.set_xml_file(xml_config_file)

    list_server = mange_service.get_xml_info()

    if option == "start":
        list_server = sorted(list_server, key=lambda k: int(k['order']), reverse=True)
        inversed_list_server = list()

        for elt in list_server:
            # print elt
            dict_tmp = dict()
            for k in elt:
                # print k, elt.get(k)
                if k == "actions":
                    dict_tmp[k] = sorted(elt.get(k), key=lambda v: int(v['order']), reverse=True)
                else:
                    dict_tmp[k] = elt.get(k)
            inversed_list_server.append(dict_tmp)

        list_server = inversed_list_server

    start_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    # we use the same log file
    # log_file_name = "ManageScAppli.log"
    log_file_name = "ManageScAppli_" + start_time.split(' ')[0].replace('/', '') + ".log"
    full_path_log_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), log_file_name)

    # backup sys.stdout
    std_out = sys.stdout

    if console == "off":
        print "\nStandard output (stdout) are redirected to : %s" % full_path_log_file
        print "\n begin processing ..."
        sys.stdout = open(full_path_log_file, "w")

        # try:
        # with open(full_path_log_file, "a+") as sys.stdout:
    print "\n"
    print "******************************"
    print "* Start: " + start_time + " *"
    print "******************************"
    print "\n"
    print "[ AFTER ]"
    print "=============================="
    print "= Displaying services status ="
    print "=============================="
    mange_service.display_services_status(list_server)
    if option == "status":
        print "******************************"
        print "* End: " + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " *"
        print "******************************"
        print "success !"
        sys.exit(0)

    # Start managing services
    for server in list_server:
        server_name = server.get('name')
        print "====================================================================================================="
        print "=\t\t\t\t %s SERVICES ON: %s" % (option.upper(), server_name.upper())
        print "====================================================================================================="
        print "(0) Order : %s" % server.get('order')
        print "(1) Start connection to: %s ,@ddr %s:%s" % (server_name.upper(), server.get('ip'), server.get('port'))

        if server.get('os').strip().lower() == "windows":
            conn = mange_service.init_winrm_connection(server.get('ip'), server.get('port'), server.get('login'),
                                                       server.get('password'))
            if conn:
                print "(2) Execute Actions by order:"
                for action in server.get('actions'):
                    action_order = action.get('order')
                    action_type = action.get('type')
                    action_name = action.get('name')  # if action_type == "service" else None
                    action_src = action.get('src')
                    # action_like_service = action.get('like_service')
                    # action_param = action.get('param')
                    # start or stop service
                    if action_type == "service":
                        # resp = mange_service.manage_win_service(action_name, option)
                        resp = mange_service.manage_service(action_name, option, os="windows")
                        print "\t* Order: %s\t%s" % (action_order, str(resp))
                    elif action_type == "command":
                        if action.get('use') == "like_net_service":
                            action_src = action_src + " " + action.get('param') + " " + option + " " + action_name
                        elif action_type('use') == "like_service":
                            action_src = action_src + " " + action.get('param') + " " + option
                        print "\t* Order: %s\tCommand: %s" % (action_order, action_src)
                        stdout, stderr = mange_service.execute_winrm_shell_cmd(action_src)
                        if len(stderr) != 0:
                            print "\t\t\t* stderr:"
                            # for e in stderr:
                            print "\t\t\t\t => stderr: " + stderr
                        if len(stdout) != 0:
                            print "\t\t\t* stdout:"
                            # for e in stdout:
                            print "\t\t\t\t => stdout: " + stdout
                print "(3) Close connection"
                print "(4) End\n"
            else:
                print "\t=> WinRM : Authentication failed"

                # print "***********************************************************************************"

        elif server.get('os').strip().lower() == "linux":
            conn = mange_service.init_ssh_connection(server.get('ip'), server.get('port'), server.get('login'),
                                                     server.get('password'))
            if conn:
                print "(2) Execute Actions by order:"
                for action in server.get('actions'):
                    action_order = action.get('order')
                    action_type = action.get('type')
                    action_name = action.get('name')  # if action_type == "service" else None
                    action_src = action.get('src')
                    # action_like_service = action.get('like_service')
                    # action_param = action.get('param')
                    # start or stop service
                    if action_type == "service":
                        resp = mange_service.manage_service(action_name, option, os="linux")
                        print "\t* Order: %s\t%s" % (action_order, str(resp))
                    elif action_type == "command":
                        if action.get('use') == "like_service":
                            action_src = action_src + " " + action.get('param') + " " + option
                            print "\t* Order: %s\tCommand: %s" % (action_order, action_src)
                            stdout, stderr = mange_service.execute_ssh_shell_cmd(action_src)
                        elif action.get('use') == "simple":
                            print "\t* Order: %s\tCommand: %s" % (action_order, action_src)
                            stdout, stderr = mange_service.execute_ssh_shell_cmd(action_src)
                        elif action.get('use') == "comment_file":
                            exec_cmd = "cut -c 1 %s" % action_src
                            stdout, stderr = mange_service.execute_ssh_shell_cmd(exec_cmd)
                            # print stdout
                            # print stderr
                            allow_comment = False
                            allow_uncomment = False
                            sed = ""
                            if len(stdout) > 0:
                                for elt in stdout:
                                    if str(elt).startswith("#"):
                                        allow_uncomment = True
                                    else:
                                        allow_comment = True
                                        allow_uncomment = False
                                        break
                            if allow_uncomment and option == "start":
                                # comment file
                                sed = "sed -i 's/^#//' " + action_src
                            elif allow_comment and option == "stop":
                                # uncomment file
                                sed = "sed -i 's/^/#/' " + action_src
                            else:
                                stdout = []
                                stderr = ["not necessary to comment or uncomment file"]
                                print "\t* Order: %s\tCommand: comment file -> %s " % (action_order, action_src)
                            action_src = sed
                            if action_src != "":
                                print "\t* Order: %s\tCommand: %s" % (action_order, action_src)
                                stdout, stderr = mange_service.execute_ssh_shell_cmd(action_src)
                        if len(stderr) != 0:
                            print "\t\t\t* stderr:"
                            for e in stderr:
                                print "\t\t\t\t => stderr: " + e.replace("\n", "")
                        if len(stdout) != 0:
                            print "\t\t\t* stdout:"
                            for e in stdout:
                                print "\t\t\t\t => stdout: " + e.replace("\n", "")
                    sleep(1)
                print "(3) Close connection"
                mange_service.close_ssh_connection()
                print "(4) End\n"
                print "\n"
            else:
                print "\t=> SSH : Authentication failed"
                # print "***********************************************************************************"
        else:
            print "\t=> config_server.xml: Unrecognized operating system (use: windows or linux)"

            # print "***********************************************************************************"
    print "\n[ BEFORE ]"
    print "=============================="
    print "= Displaying services status ="
    print "=============================="
    mange_service.display_services_status(list_server)

    print "****************************"
    print "* End: " + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " *"
    print "****************************\n"
    print "success !!"

    if console == "off":
        sys.stdout.close()
    # except Exception as ex:
    #     print str(ex)
    #     print "Erreur lors l'execution du script !! verifiez les droits ..."
    #     sys.exit(0)

    sys.stdout = std_out
    print "\nSuccess !!"
