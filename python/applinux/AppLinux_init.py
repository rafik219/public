#!/usr/bin/env python
# -*- coding: utf_8 -*-

# author: rbo
# version: 02/06/2017
# require python2.6 or python2.7
# require YAML package:
#   -   pip install pyaml
#
# script utility:
#   1/ init ip-label Application Linux: Adaptateur, Traceroute, Executeur,ping ...
#   2/ stop & start service in /etc/init/NAME.conf


import getopt
import glob
import os
import sys
import subprocess
import yaml


def usage():
    print "-------------------------------------------------"
    print "Usage:"
    print "\t %s -f <file> " % sys.argv[0]
    print "\t %s --file <file> " % sys.argv[0]
    print "\n <file> : Fichier de configuration YAML"
    print "\n"
    print "Ou"
    print "\n"
    print "\t %s -s <srv> -o <opt> " % sys.argv[0]
    print "\t %s --service <srv> --action <act> " % sys.argv[0]
    print "\n<srv> =  service name in: /etc/init/"
    print "<act> =  stop \t: Arreter les services" \
          "\n\t start \t: Lancer les services"
    print "-------------------------------------------------"
    sys.exit(0)


def get_yaml_configuration(yaml_file):
    content = list()
    if not os.path.exists(yaml_file):
        print "Configuration File not found: %s " % yaml_file
        sys.exit(-1)
    else:
        with open(yaml_file, 'r') as f:
            try:
                content = yaml.load(f)
            except Exception, ex:
                print "Error on loading or parsing YAML file: %s, cause: %s" % (f, ex)
                sys.exit(-2)
    return content


def delete_applinux_init_file(configuration):
    print "\n"
    print "-------------------------------------------------------"
    print "-    Delete /etc/init/AppLinux_*.conf"
    print "-------------------------------------------------------"
    dict_config = dict()
    for line_config in configuration:
        found = False
        for tool, config in line_config.iteritems():
            tool_type = tool
            print "- %s :" % tool_type
            for param in config:
                for key, value in param.iteritems():
                    # print "\t %s -> %s " % (key, value)
                    dict_config[key] = value
        # delete f in /etc/init/
        for f in glob.glob("/etc/init/" + dict_config['name'] + "*.conf"):
            found = True
            try:
                os.remove(f)
                print "\t %s -> File delete" % f
            except Exception, ex:
                print "Can't remove this f: %s, cause: %s" % (f, ex)
        if not found:
            print "\t No configuration file found for this service"


def create_applinux_init_file(configuration):
    # delete old file in /etc/init/
    delete_applinux_init_file(configuration)
    print "\n\n"
    print "-----------------------------------------------------"
    print "-    Create new file /etc/init/AppLinux_*.conf"
    print "-----------------------------------------------------"
    dict_config = dict()
    for line_config in configuration:
        for tool, config in line_config.iteritems():
            tool_type = tool
            print "- %s :" % tool_type
            for param in config:
                for key, value in param.iteritems():
                    # print "\t %s -> %s " % (key, value)
                    dict_config[key] = value
            if dict_config['activate'] == "yes":
                if isinstance(dict_config['schema'], list):
                    if dict_config['number'] != len(dict_config['schema']):
                        print "Error: Le nombre de '%s' = %s doit etre egale au nombre de 'schema'= %s declares dans le fichier: %s" % (
                            tool_type, dict_config['number'], len(dict_config['schema']), yaml_file)
                        # sys.exit(-3)
                if not os.path.exists(dict_config['exec']):
                    print "\t => Error: %s file not found" % dict_config['exec']
                    continue
                for i in range(dict_config['number']):
                    file_name = dict_config['name'] + "%s.conf" % (i + 1)
                    dest_file_name = os.path.join("/etc/init/", file_name)
                    if tool_type == "Adaptateur":
                        if isinstance(dict_config['schema'], list):
                            if dict_config['schema'][i] != "":
                                schema = "-%s" % dict_config['schema'][i]
                            else:
                                schema = dict_config['schema'][i]
                        else:
                            if dict_config['schema'] != "":
                                schema = "-%s" % dict_config['schema']
                            else:
                                schema = ""
                        type_appli = ["-g" + str(elt) for elt in dict_config['type_appli'][i]]

                        file_content = 'start on runlevel [3]\n' \
                                       'respawn\n' \
                                       'exec /bin/su - -c "' + dict_config['exec'] + ' ' + schema + ' ' + " ".join(
                            type_appli) + ' > ' + dict_config['redirect'] + '"\n'
                        try:
                            with open(dest_file_name, 'w') as file:
                                file.write(file_content)
                                print "\t %s -> File created" % dest_file_name
                        except Exception, ex:
                            print "Can't create file: %s, cause: %s" % (dest_file_name, ex)

                    else:
                        if isinstance(dict_config['schema'], list):
                            if dict_config['schema'][i] != "":
                                schema = "-%s" % dict_config['schema'][i]
                            else:
                                schema = dict_config['schema'][i]
                        else:
                            if dict_config['schema'] != "":
                                schema = "-%s" % dict_config['schema']
                            else:
                                schema = ""
                        file_content = 'start on runlevel [3]\n' \
                                       'respawn\n' \
                                       'exec /bin/su - -c "' + dict_config['exec'] + ' ' + schema + ' > ' + \
                                       dict_config['redirect'] + '"\n'
                        try:
                            with open(dest_file_name, 'w') as file:
                                file.write(file_content)
                                print "\t %s -> File created" % dest_file_name
                        except Exception, ex:
                            print "C'ant create file: %s, cause: %s" % (dest_file_name, ex)
            else:
                print "\t => Service disabled"


def initctl_service(opt, service):
    try:
        os.chdir("/etc/init")
    except Exception, ex:
        print str(ex)
        print "Error: can't switch to '/etc/init' directory, cause: %s" % ex
        sys.exit(-1)
    for serv in glob.glob("/etc/init/" + service + "*.conf"):
        # print "=>" + serv
        serv_name = serv.split(".")[0].split("/")[3]
        try:
            subprocess.call(["/sbin/initctl", opt, serv_name])
        except Exception, ex:
            print "Error: when %s %s services, cause: %s" % (opt, service, str(ex))
            sys.exit(-2)


def check_existing_service(service):
    exist = False
    for serv in glob.glob("/etc/init/" + service + "*.conf"):
        print "(*) Service found, centreon_config file : %s" % serv
        exist = True
        break
    if not exist:
        print "(**) service '%s' not Found in /etc/init/*.conf" % service
        print "(**) we found this services : "
        for serv in sorted(glob.glob("/etc/init/*.conf")):
            print "\t\t - " + serv.split(".")[0].split("/")[3]
    return exist


if __name__ == '__main__':

    argument = sys.argv[1:]

    if len(argument) not in (2, 4):
        usage()
    try:
        opts, args = getopt.getopt(argument, "f:s:a:h", ["file=", "service=", "action=", "help="])
    except getopt.GetoptError, e:
        print str(e)
        usage()

    yaml_file = None
    service_name = None
    do_action = None

    if len(opts) != 0:
        for (opt, arg) in opts:
            if opt in ("-f", "--file"):
                yaml_file = arg
            elif opt in ("-s", "--service"):
                service_name = arg
            elif opt in ("-a", "--action"):
                do_action = arg.lower()
                if do_action not in ('start', 'stop'):
                    usage()
            elif opt in ("-h", "--help"):
                usage()
            else:
                usage()
    else:
        usage()

    if yaml_file is not None:
        if service_name is not None or do_action is not None:
            usage()
        else:
            applinux_config = get_yaml_configuration(yaml_file)
            create_applinux_init_file(applinux_config)
    elif service_name is not None and do_action is not None:
        # check existing service_name
        if check_existing_service(service_name):
            # manage centreon_config file on /etc/init.
            initctl_service(do_action, service_name)
    else:
        usage()

    print "success !!"
