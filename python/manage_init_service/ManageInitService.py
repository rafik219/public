#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# @uthor: rbo
# version: 15/12/2016


import os
import sys
import getopt
import glob
import subprocess


def usage():
    print "--------------------------------------------------"
    print "Usage:"
    print "\t %s -s <srv> -o <opt> " % sys.argv[0]
    print "\t %s --service <srv> --option <opt> " % sys.argv[0]
    print "\n<srv> =  service name in /etc/init/"
    print "\n<opt> =  stop \t: Arreter les services" \
          "\n\t start \t: Lancer les services"
    print "--------------------------------------------------"
    sys.exit(1)

def initCtlService(opt, service):
    try:
        os.chdir("/etc/init")
    except Exception, ex:
        print str(ex)
        print "Error: can't switch to '/etc/init' directory."
        sys.exit(-1)
    for serv in glob.glob("/etc/init/" + service + "*.conf"):
        # print "=>" + serv
        serv_name = serv.split(".")[0].split("/")[3]
        try:
            subprocess.call(["/sbin/initctl", opt, serv_name])
        except Exception, ex:
            print "Error: when %s %s services, cause: %s" % (opt, service, str(ex))
            sys.exit(-2)

def checkExistingService(service):
    exist = False
    for serv in glob.glob("/etc/init/" + service + "*.conf"):
        print "(*) Service found, config file : %s" % serv
        exist = True
        break
    if not exist:
        print "(**) service '%s' not Found in /etc/init/*.conf" % service
        print "(**) we found this services : "
        for serv in sorted(glob.glob("/etc/init/*.conf")):
            print "\t\t - " + serv.split(".")[0].split("/")[3]
    return exist

if __name__ == "__main__":

    argument = sys.argv[1:]
    # print argument
    if len(argument) < 4:
        # print "1"
        usage()

    try:
        opts, args = getopt.getopt(argument, "s:o:h", ["service=", "option=", "help="])
    except getopt.GetoptError, ex:
        print str(ex)
        usage()
    # print "opts: " + str(opts)
    # print "args: " + str(args)

    option = ""
    service_name = ""

    if len(opts) != 0:
        for (opt, arg) in opts:
            # print opt, arg
            if opt in ("-s", "--service"):
                service_name = arg
            elif opt in ("-o", "--option"):
                option = arg.lower()
                # print option
                if option not in ("start", "stop", "status"):
                    usage()
            elif opt in ("-h", "--help"):
                usage()
            else:
                usage()
    else:
        usage()

    # check existing service
    if checkExistingService(service_name):
        # manage config file on /etc/init.
        initCtlService(option, service_name)

    print "success !!"
