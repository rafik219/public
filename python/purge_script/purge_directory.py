#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# rbo
# version: 24/08/2016

import os
import sys
import re
import datetime
import shutil
import getopt
import glob


def usage():
    print "---------------------------------------------------------------"
    print "Usage:"
    print "\t %s -d dir -r <ret> -t <typ> -e <on|off>" % sys.argv[0]
    print "Ou"
    print "\t %s --directory <dir> --retention <ret> --type <typ> --enable <on|off>" % sys.argv[0]
    print "\n- dir : repertoire parent" \
          "\n- ret : retention nombre de mois doit etre >= 0" \
          "\n- typ : type de retention m = months, d = days" \
          "\n- on  : pour activer la supprission des repertoires" \
          "\n- off : pour afficher les repertoires a supprimer"
    print "---------------------------------------------------------------"
    sys.exit(2)


# Permet de renvoyer une liste de repertoire ordonnee qui match l'expression reguliere Regex_days
# Les repertoires sont de type: .../annee/mois/jour
def getlistdirectory_d(regex, cwd, diffyear, diffmonth, diffday):
    list_purge_dir = list()
    for dirpath, dirname, filename in os.walk(cwd):
        if re.match(regex, dirpath):
            path = dirpath.split('/')
            day = path[-1]
            month = path[-2]
            year = path[-3]
            # comparing directory
            if (int(year), int(month), int(day)) < (int(diffyear), int(diffmonth), int(diffday)):
                purgedir = "{0}/{1}/{2}".format(year, month, day)
                # get full path directory
                fullpath_purgedir = os.path.join(cwd, purgedir)
                # append full path purge directory
                list_purge_dir.append(fullpath_purgedir)
    list_purge_dir.sort(reverse=True)
    return list_purge_dir


# Permet de renvoyer une liste des repertoires qui match l'expression reguliere Regex_months
# Les repertoires sont de type: .../annee/mois
def getlistdirectory_m(regex, cwd, diffyear, diffmonth, purgetype=None):
    list_purge_dir_m = list()
    for dirpath, dirname, filename in os.walk(cwd):
        if re.match(regex, dirpath):
            path = dirpath.split('/')
            month = path[-1]
            year = path[-2]
            if purgetype == 'days':
                # comparing directory
                if (int(year), int(month)) <= (int(diffyear), int(diffmonth)) and len(os.listdir(dirpath)) == 0:
                    purgedir = "{0}/{1}".format(year, month)
                    # get full path directory
                    full_path_purgedir = os.path.join(cwd, purgedir)
                    # append full path purge directory
                    list_purge_dir_m.append(full_path_purgedir)
            elif purgetype == 'months':
                if (int(year), int(month)) < (int(diffyear), int(diffmonth)):
                    purgedir = "{0}/{1}".format(year, month)
                    full_path_purgedir = os.path.join(cwd, purgedir)
                    list_purge_dir_m.append(full_path_purgedir)
    list_purge_dir_m.sort(reverse=True)
    return list_purge_dir_m


# Permet de renvoyer une liste des repertoires qui match l'expression reguliere Regex_years
# Les repertoires sont de type: .../annee
def getlistdirectory_y(regex, cwd, diffyear):
    list_purge_dir_y = list()
    for dirpath, dirname, filename in os.walk(cwd):
        if re.match(regex, dirpath):
            path = dirpath.split('/')
            year = path[-1]
            if int(year) <= int(diffyear) and len(os.listdir(dirpath)) == 0:
                fullpath_purgedir = os.path.join(cwd, year)
                # print "==>" + fullpath_purgedir
                list_purge_dir_y.append(fullpath_purgedir)
    # print list_purge_dir_y
    list_purge_dir_y.sort(reverse=True)
    return list_purge_dir_y


# Permet de purger la liste des Paths qu'on lui passe en parametre
# elle renvoie un dictionnaire avec le status de la purge de chaque entree: OK ou NOK
def purgedirectory(list_purge_dir, enable=None):
    print "Count : " + str(len(list_purge_dir))
    purgestatus = dict()
    # start to purge directories:
    if len(list_purge_dir) > 0:
        for path in list_purge_dir:
            try:
                if os.path.exists(path):
                    if enable == 'on':
                        shutil.rmtree(path)
                        print "\t%s --> deleted " % path
                    elif enable == 'off':
                        print "\t%s --> will be deleted " % path
                    purgestatus[path] = 'OK'
                else:
                    print "Le repertoire a supprimer %s n'existe plus" % path
                    purgestatus[path] = 'NOK'
            except Exception as ex:
                print "impossible de supprimer ce repertoire :  " + str(path)
                print "Cause : " + str(ex)
                purgestatus[path] = 'NOK'
    else:
        print "Aucun repertoire a supprimer !!"
    return purgestatus


# Permet d'afficher le resultat de la supprission sur la console avec Trace=trace
# sinon elle affiche que dans le cas d'erreur
def check_purge_directory_status(purgstat, trace=True):
    if len(purgstat) != 0:
        if 'NOK' not in purgstat.values():
            if trace:
                print "\tStatus : Purge OK !\n"
            else:
                pass
        else:
            print "Status : erreur de la suppression des repertoires suivants : "
        for e, elt in purgstat.iteritems():
            if elt == 'NOK':
                print e + " -> " + elt
            else:
                pass


# Permet de supprimer les log files generes s'ils depassent 30 jours.
def manage_log_files(dir, today):
    date_today = today.strftime("%Y%m%d")
    for file in glob.glob(dir + "/purge_*.log"):
        filename = os.path.basename(file)
        date_filename = (filename.split('_')[-1]).split('.')[0]
        # supprimer les log file de plus de 30 jours
        if int(date_today) - int(date_filename) > 30:
            try:
                os.remove(file)
            except Exception as ex:
                print str(ex)
                pass


if __name__ == "__main__":

    argument = sys.argv[1:]
    # print len(argument)

    if len(argument) < 8:
        usage()

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'd:r:t:e:h', ['directory=', 'retention=', 'type=', 'enable='])
        # print opts
    except getopt.GetoptError as e:
        print str(e)
        usage()

    for (opt, arg) in opts:
        if opt in ('-d', '--directory'):
            workdir = arg
        elif opt in ('-r', '--retention'):
            retention = arg
        elif opt in ('-t', '--type'):
            typ = arg.lower()
        elif opt in ('-e', '--enable'):
            enable = arg.lower()

        else:
            usage()

    # defined REGEX to match path format ../20../..
    if typ == "days":
        regex_d = r'^(%s)/(([0-9]){4}){1}(/([0-9]){2}){2}$' % workdir  # regex for: ../year/month/day format
    elif typ == "months":
        pass
    else:
        print "\nveulliez specifier le parametre : \n\t type = months \nou\n\t type = days"
        usage()

    if enable not in ('on', 'off'):
        usage()

    regex_m = r'^(%s)/(([0-9]){4}){1}(/([0-9]){2}){1}$' % workdir  # regex for:  ../year/month format
    regex_y = r"^(%s)/(20([0-9]){2}){1}$" % workdir  # regex for:  ../year format
    # regex_y = r"^(%s)/(([0-9]){4}){1}$" % workdir  # regex for:  ../year format

    today = datetime.datetime.now()
    formated_today = today.strftime("%Y/%m/%d")

    # backup sys.stdout
    stdout = sys.stdout

    # get current work dir
    # currentwd = os.getcwd()
    # create log file by default on /opt/iplabel/purge_script
    # currentwd = "/opt/iplabel/purge_script"
    currentwd = os.path.dirname(__file__)

    # log filename:
    filename = "purge_" + today.strftime("%Y%m%d") + ".log"

    # print filename
    full_path_debugFile = os.path.join(currentwd, filename)
    # print full_path_debugFile

    if os.path.exists(full_path_debugFile):
        try:
            os.remove(full_path_debugFile)
        except Exception as ex:
            print "erreur lors de la suppression du fichier: " + str(full_path_debugFile)
            # print full_path_debugFile + " file removed"

    try:
        # redirect console output on log file
        with open(full_path_debugFile, 'w') as sys.stdout:
            sys_stdout = open(full_path_debugFile, 'w')

            print "-----------------------------"
            print "Debut : " + datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
            print "-----------------------------"

            print "work directory : " + workdir

            print "retention = " + str(retention)

            if typ == 'months':
                retentionday = int(retention) * 365 / 12
                print "retentoin en jour = " + str(retentionday)
            else:
                retentionday = int(retention)

            diff = today - datetime.timedelta(days=retentionday)
            print "today - retention = " + str(diff)

            formateddiff = diff.strftime("%Y/%m/%d")
            print "today - retention Y/M/D = " + str(formateddiff)

            listformateddiff = formateddiff.split('/')
            print str(listformateddiff)

            diffyear = listformateddiff[0]
            diffmonth = listformateddiff[1]
            diffday = listformateddiff[2]

            if typ == "days":
                print "\nListe des repertoires par jour purgees : "
                # Get list purge directory
                listpurgedirectory = getlistdirectory_d(regex_d, workdir, diffyear, diffmonth, diffday)
                # start purge directories:
                purgestatus_d = purgedirectory(listpurgedirectory, enable=enable)
                # check purge status
                check_purge_directory_status(purgestatus_d)

                print "\nListe des repertoires par mois purgees : "
                listpurgedirectory_m = getlistdirectory_m(regex_m, workdir, diffyear, diffmonth, purgetype='days')
                purgestatus_m = purgedirectory(listpurgedirectory_m, enable=enable)
                check_purge_directory_status(purgestatus_m, trace=True)

            elif typ == "months":
                print "\nListe des repertoires par mois purgees : "
                listpurgedirectory_m = getlistdirectory_m(regex_m, workdir, diffyear, diffmonth, purgetype='months')
                purgestatus_m = purgedirectory(listpurgedirectory_m, enable=enable)
                check_purge_directory_status(purgestatus_m, trace=True)

            print "\nList des repertoires par Annees purgees : "
            listpurgedirectory_y = getlistdirectory_y(regex_y, workdir, diffyear)
            purgestatus_y = purgedirectory(listpurgedirectory_y, enable=enable)
            check_purge_directory_status(purgestatus_y, trace=True)

            print "\nend with sucess !"
            print "-----------------------------"
    except Exception, ex:
        print ex
        print "Erreur lors l'execution du script !! verifiez les droits ..."
        sys.exit(0)

    sys.stdout = stdout

    # code en plus
    # cette partie est utilisee pour generer les sorties standards dans le cas d'echec
    # une fois que le script tourne en crontab, la generation de la sortie standard console output
    # provoque l'envoi de mail dans le cas d'echec

    if typ == "days":
        check_purge_directory_status(purgestatus_d, trace=False)

    check_purge_directory_status(purgestatus_m, trace=False)
    check_purge_directory_status(purgestatus_y, trace=False)

    # Manage Log file, delete log files after 30 days
    manage_log_files(os.path.dirname(full_path_debugFile), today)

    # print "end !"
    sys.exit(1)
