#!/usr/bin/python
# -*- encoding: utf-8

# rbo
# version: 15/05/2017
#
# Script de bascule dns sur un liste de domaine
# Note: le script se base sur un script 'switch_to_dns_backup.py' deja existant
# Le 2 scripts doivent etre dans le meme repertoire.


import getopt
import os
import subprocess
import sys
from time import sleep


def usage():
    print "------------------------------------------"
    script_name = sys.argv[0]
    print "Usage:"
    print "\t%s -d <dom> -z <zon> -r <opt>\n" \
          "\t%s --domain <dom> --zone <zon> --run <opt>\n" \
          "\t\nOu\n" \
          "\t <dom>  : Liste des domaines a modifier, séparés par des virgules et sans espace\n" \
          "\t <zon>  : Liste des zones cibles, séparées par des virgules et sans espace\n" \
          "\t <opt>  : ok -> pour lancer la bascule\n" \
          "\t\t: print -> pour afficher des infos" % (script_name, script_name)
    print "------------------------------------------"
    sys.exit(-1)


def main():
    opts = None
    args = None
    run = None
    list_domain_name = []
    list_zone_name = []

    argument = sys.argv[1:]

    # sans utilisation du wait 6 au lieu de 8
    if len(argument) != 6:
        usage()

    try:
        opts, args = getopt.getopt(argument, 'd:z:r:w:h', ['domain=', 'zone=', "run=", "wait=", "help="])
    except getopt.GetoptError, ex:
        print str(ex)
        usage()

    for opt, arg in opts:
        if opt in ("-h", '--help'):
            usage()
        elif opt in ("-d", "--domain"):
            list_domain_name = arg.lower()
            if list_domain_name.find(',') != -1:
                list_domain_name = list_domain_name.split(',')
            else:
                print "Veuillez fournir une list de domaine ..."
                sys.exit(-2)
        elif opt in ("-z", "--zone"):
            list_zone_name = arg.lower()
            if list_zone_name.find(',') != -1:
                list_zone_name = list_zone_name.split(',')
            else:
                print "Veuillez fournir une list de zone ..."
                sys.exit(-2)
        elif opt in ("-r", "--run"):
            run = arg.lower()
            if run not in ("ok", "print"):
                usage()
        # elif opt in ("-w", "--wait"):
        #     wait = arg.lower()
        #     if wait not in ("yes", "no"):
        #         usage()
        else:
            usage()

    # compare between list_domain_name && list_zone_name
    if len(list_domain_name) == len(list_zone_name):
        for i in range(len(list_domain_name)):
            if not list_zone_name[i].startswith(list_domain_name[i]):
                print "Erreur de domaine ou de zone: "
                print " => Domaine: " + list_domain_name[i] + " => Zone: " + list_zone_name[i]
                print "\n => Par convention interne a ip-label, le nom de la zone doit commencer par le nom de domaine suivi par _prod ou _backup \n" \
                      " => Exemple: \n" \
                      "\t\t Domaine: ip-label.net \t\t Zone1: ip-label.net_prod \t Zone2: ip-label.net_backup\n"
                sys.exit(-3)
    else:
        print "Le nombre de domaine doit etre egale au nombre de zone fourni"
        print "Veuillez fournir la liste des domaines et des zones separees par des ',' et sont espace !!"
        print "Exemple:"
        print "\t Liste des domaines : Dom1,Dom2,...,DomX"
        print "\t Liste des zone     : Zon1,Zon2,...,ZonX"
        print "\n"
        print "Liste des domaines   = %s" % list_domain_name
        print "Liste des zones      = %s" % list_zone_name
        sys.exit(-4)

    # start switch zone using: "switch_to_dns_backup.py" script.
    script_name = "switch_to_dns_backup.py"
    work_dir = os.path.dirname(os.path.realpath(__file__))
    full_path_script = os.path.join(work_dir, script_name)
    # print full_path_script
    for i in range(len(list_domain_name)):
        # start switching
        print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
        print "Start switching Domain[%s]: '%s' to Zone[%s]: '%s'" % (i+1, list_domain_name[i], i+1, list_zone_name[i])
        print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
        process = subprocess.Popen(
            ["/usr/bin/python", full_path_script, "-d", list_domain_name[i], "-z", list_zone_name[i], "-r", run, "-w", "no"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = process.communicate()
        print "STDOUT:\t %s " % out
        if len(err) != 0:
            print "STDERR:\t %s " % err
            sys.exit(-5)
        print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
        # sleep 2 seconds
        sleep(2)


if __name__ == "__main__":
    main()
    print "Success !!"
    sys.exit(0)
