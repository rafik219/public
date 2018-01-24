#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# rbo
# update : 30/09/2016

import os
import sys
import cx_Oracle
import glob
import getopt
from shutil import copyfile
from subprocess import call
from time import sleep
from datetime import datetime


# Usage
def usage():
    print "---------------------------------------------------------------"
    print "Usage:"
    print "\t %s -o <opt> " % sys.argv[0]
    print "\t %s --option <opt> " % sys.argv[0]
    print "\n <opt> = stop \t: Arrete les services AnalyseCptRendu" \
          "\n\t start \t: Lance les services AnalyseCptRendu" \
          "\n\t calculate : Calculer les AnalyseurCptRendu" \
          "\n\t rebuild : Regenere les services AnalyseCptRendu"
    print "---------------------------------------------------------------"
    sys.exit(1)


""" for display """


def display(res):
    print "Listing :"
    for row in res:
        print "\t %s" % str(row)


"""
backup des fichiers /etc/init/analyseconmpterendu* dans le repertoire ../backupAnalyseCptfile
    - creation du repertoire s'il n'existe pas
    - copies des fichiers /etc/init/analysecompterendu*.conf dans ../backupAnalyseCptfile directory
    - suppression des anciens fichiers dans backupAnalyseCptfile s'ils existent
    - affichage du contenu du repertoire ../backupAnalyseCptfile
    :param src : src -> /etc/init/
    :param dst : ../backupAnalyseCptfile
"""


def backupAnalyseCptRenduFile(src, dst):
    backupdir = os.path.join(dst, "backupAnalyseCptFile")
    if not os.path.exists(backupdir):
        try:
            print "(*) Create backup directory : "
            os.mkdir(backupdir)
            print backupdir + " -> created"
        except Exception, ex:
            print str(ex)
            print "impossible de creer un repetoire de backup"
            sys.exit(6)

    if len(os.listdir(backupdir)) != 0:
        print "(*) Removing old backup file :"
        try:
            for file in glob.glob(backupdir + "/*"):
                os.remove(file)
                print str(file) + " --> removed !!"
        except Exception, ex:
            print str(ex)
            print "impossible de supprimer les fichiers analysecompterendu*.conf dans le repertoire de backup"
            sys.exit(7)

    print "\n(*) Copy files to backup directory :"
    try:
        for file in glob.glob(src + "/analysecompterendu*.conf"):
            # filedestname = os.path.join(backupdir, file)
            file_dest_name = os.path.basename(file)
            full_path_name = os.path.join(backupdir, file_dest_name)
            copyfile(file, full_path_name)
            print str(file) + " --> copied !!"
    except Exception, ex:
        print str(ex)
        print "impossible de copier les fichiers /etc/init/analysecompterendu*.conf vers le repertoire de backup"
        sys.exit(8)

    print "\n(*) Listing %s dir:" % backupdir
    for file in glob.glob(backupdir + "/*"):
        print file


"""
fonction qui permet de lancer la regeneration des fichiers analysecompterendu*.conf dans /etc/init/
   - suppression des anciens fichiers analysecompterendu*.conf dans /etc/init/
   - creation des nouveaux fichiers analysecompterendu*.conf dans /etc/init/
      :param ListAnalyser: la liste des analyseur retourner par la fonction getInfoAnalyser()

:param directory: /etc/init/ repertoire de generation des nouveaux fichiers de configuration.
:return:
"""


def buidAnalyseCptRenduFile(ListAnalyser, directory):
    # delete old analysecompterendu.conf files
    for e, elt in enumerate(glob.glob(directory + "/analysecompterendu*.conf")):
        try:
            os.remove(elt)
            # print elt + "   removed !"
        except Exception, ex:
            print str(ex)
            print "impossible de supprimer les fichiers analysecompterendu*.conf dans le repertoire /etc/init/"
            sys.exit(4)
    for e, (Min, Max) in enumerate(listAnalyser):
        # e = e+1
        # print str(e) + " ->  min: "+str(min) + " -  max: " +str(max)
        filename = "analysecompterendu%s.conf" % (e + 1)
        path_filename = os.path.join(directory, filename)
        print path_filename
        if (e + 1) == len(ListAnalyser):
            Max = 2000000
        ch = 'start on runlevel [3]\n' \
             'respawn\n' \
             'exec /bin/su - iplabel -c "/opt/iplabel/bin/AnalyseCptRendus -deb ' + str(Min) + ' -fin ' + str(
            Max) + ' > /dev/null"\n'
        try:
            with open(path_filename, 'w') as f:
                f.write(ch)
        except Exception, ex:
            print str(ex)
            print "impossible de creer des nouveaux fichiers dans le repertoire %s" % directory
            sys.exit(5)


"""
fonction pour gerer le start/stop des analyseurs
    - le start/stop est gere en mode synchrone.
    :param cmd: command = START ou STOP
    :return:
"""


def initCtlService(cmd):
    isfileExist = False
    try:
        try:
            # we need to change directory to start analysecompterendu services
            os.chdir("/etc/init/")
        except Exception, ex:
            print str(ex)
            print "Error: can't switch directory to : /etc/init/"
            sys.exit(2)
        # start & stop analysecomptrendu services
        for e, elt in enumerate(glob.glob("/etc/init/analysecompterendu*.conf")):
            # synchronous function start and wait process
            call(["/sbin/initctl", cmd, "analysecompterendu" + str((e + 1))])
            # sleep(1)
            isfileExist = True  # True if analysecompterendu is found then

        if not isfileExist:
            print "\t (**) Aucun fichier analysecompterendu trouve dans: /etc/init/"

        if cmd == "stop":
            # we need to kill other process started by iplabel user
            print "kill blocked process ..."
            call(["killall", "AnalyseCptRendus"])

    except Exception, ex:
        print str(ex)
        print "Erreur lors de %s des services AnalyseCptRendu" % cmd
        sys.exit(3)  # def findBlockedProcess():
        # proc = subprocess.Popen(["ps", "-ef" , "|", "grep", "AnalyseCptRendus" , "|", "grep", "-v", "grep", "|", "wc", "-l"])
        # proc.wait()


if __name__ == "__main__":
    
    # force to export ORACLE_HOME envirenment variable
    # os.environ['ORACLE_HOME']="/usr/lib/oracle/11.2/client"

    argument = sys.argv[1:]
    if len(argument) != 2:
        usage()
    try:
        opts, args = getopt.getopt(argument, "-o:h", ["option=", "help="])
    except getopt.GetoptError, e:
        print str(e)
        usage()

    option = ""
    if len(opts) != 0:
	for (opt, arg) in opts:
            if opt in ("-o", "--option"):	     
            	option = arg.lower()
            	if option not in ["start", "stop", "rebuild", "calculate"]:
		    usage()
            elif opt in ("-h", "--help"):
                usage()
            else:
                usage()
    else:
        usage()

    print "******************************"
    print "* Start: " + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " *"
    print "******************************"
    # cwd = os.getcwd()
    # CURRENT_WORK_DIR = os.path.dirname(__file__) # not work  !!!!
    CURRENT_WORK_DIR = os.path.dirname(os.path.realpath(__file__))
    # print cwd
    INITDIR = "/etc/init/"
    # rang ou nbr max des moniteurs gere par chaque analysecompterendu
    MAX_ACTIVE_MONITOR_INTERVAL = 200
    # nbr max de moniteurs g�r�s par le dernier Analyseur d'alert.
    MAX_ACTIVE_MONITOR_LAST_INTERVAL = 200

    # listAnalyser, nbr_active_monitor_last_interval = getInfoAnalyser(MAX_ACTIVE_MONITOR_INTERVAL)
    res = list()
    res2 = list()
    user = "SITECENTRAL"
    pwd = "XXXXXXX"
    # servicename = "MLINUX"
    # servicename = "MLINUX.iplabel.com"
    servicename = "CTRP_prod.iplabel.com"
    srvadr = "0.0.0.0"
    port = "1521"

    if option in ("rebuild", "calculate"):
        try:
            # constr = "%s/%s@%s:%s/%s" % (user, pwd, srvadr, port, servicename)
            # constr = "%s/%s@%s" % (user, pwd, servicename)
            # con = cx_Oracle.connect(user + "/" + pwd + "@" + servicename)
            
	    #con = cx_Oracle.connect(constr)
  	    
            # Added by rbo: 28/12/2016
	    dsn_tns = cx_Oracle.makedsn(srvadr, port, servicename)
	    #print dsn_tns
            dsn_tns = dsn_tns.replace('SID=', 'SERVICE_NAME=')
            #print dsn_tns
            con = cx_Oracle.connect(user=user, password=pwd, dsn=dsn_tns)

            
            cursor = con.cursor()
            # con, cur = connectdb("SITECENTRAL", "lahtdk7", "MLINUX")
            # request 1:
            req1 = "SELECT MIN(idcontrat), MAX(idcontrat)" \
                   "FROM (SELECT idcontrat,ROUND(ROWNUM/%s) rang" \
                   "      FROM ( SELECT idcontrat " \
                   "             FROM sitecentral.CONTRAT " \
                   "             WHERE etatcontrat IN (1,4)" \
                   "             ORDER BY idcontrat))" \
                   "GROUP BY ROLLUP(rang)" % MAX_ACTIVE_MONITOR_INTERVAL
            cursor.execute(req1)
            res = cursor.fetchall()
            # Delete Last TUPLE
            lasttuple = res.pop()
            lastmin, lastmax = res[-1]
            # print str(lastmin) + " - " + str(lastmax)
            # build Request 2:
            req2 = "SELECT count(*) " \
                   " FROM SITECENTRAL.CONTRAT " \
                   " WHERE ETATCONTRAT IN (1,4) " \
                   " AND IDCONTRAT BETWEEN " + str(lastmin) + " AND 2000000"
            # print req2
            cursor.execute(req2)
            res2 = cursor.fetchall()
            # if len(res2) == 0:
            #    print "Exception levee lors de l'execution de la 2�me requete SQL"
            # send mail Error
            # ....
            #    sys.exit(2)
            # print res2
            nbr_active_monitor_last_interval = res2[0][0]
            # print "Nombre de moniteur sur le dernier interval: " + str(nbr_active_monitor_last_interval)

            # return value
            # return res, nbr_active_monitor_last_interval
        except Exception as e:
            # return res, res2
            print e
            sys.exit(-2)
        finally:
            # disconnectdb(cur, con)
            try:
                cursor.close()
                print "disconnect cursor : OK"
                con.close()
                print "disconnect con : OK"
            except Exception, e:
                print e
                pass


        listAnalyser = res
        # nbr_active_monitor_last_interval = res2

        print "(*) Repartition des analyseurs par idmission : "
        display(listAnalyser)

        print "(*) Nombre de moniteurs geres par le dernier analyseur : %s (Seuil Max: %s)" % (
        nbr_active_monitor_last_interval, MAX_ACTIVE_MONITOR_LAST_INTERVAL)

        if option == "calculate":
            #print "Bye !"
            sys.exit(-1)

    else:
        print "\t (*) Not need to request database !!"
        # if option == stop/start : force to execute initCtlService("start/stop")
        nbr_active_monitor_last_interval = MAX_ACTIVE_MONITOR_LAST_INTERVAL + 1

    # si le nbr de moniteur gere par le dernier interval  est superieur ou egal au maximum par defaut fixe au debut : on lance la regeneration.
    if nbr_active_monitor_last_interval >= MAX_ACTIVE_MONITOR_LAST_INTERVAL:
        # initCtlService stop
        print "--------------------------------"
        print "(1) Stopping Analyser services : "
        print "--------------------------------"
        initCtlService('stop')

        if option == "stop":
            print "\nSuccess !"
            sys.exit(-1)

        if option == "rebuild":
            # Start backup AnalyserCptRendu files from /etc/init/.. to ../backupAnalyser/....
            print "--------------------------------"
            print "(2) Backup AnalyseCptRendu File :"
            print "--------------------------------"
            backupAnalyseCptRenduFile(INITDIR, CURRENT_WORK_DIR)
            print "--------------------------------------------"
            print "(3) Create new analysecomptrendu.conf files :"
            print "--------------------------------------------"
            # buildCptdir = "/opt/iplabel/script/createfile"
            # buidAnalyseCptRenduFile(listAnalyser, buildCptdir)
            buidAnalyseCptRenduFile(listAnalyser, INITDIR)

        # initCtlService start
        print "--------------------------------"
        print "(4) Starting Analyser services : "
        print "--------------------------------"

        initCtlService('start')

        if option == "start":
            print "\nSuccess !"
            sys.exit(-1)
    else:
        print "\nPas besoin de lancer la regeneration des analyseurs d'alertes :"
        print "\t - le nombre des moniteurs actifs geres par le dernier AnalyseCptRendu est : %s" % nbr_active_monitor_last_interval + " (Seuil Max : %s)" % MAX_ACTIVE_MONITOR_LAST_INTERVAL

    print "\nSuccess !"
    print "\n********************** END **************************\n\n"

    # exit status
    sys.exit(0)
