#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
#
# rbo
# version: 28/05/2017
# recover xml file from dist log (di_MO...log)
#
# require python2.6
#
"""

import getopt
import glob
import grp
import os
import pwd
import shutil
import subprocess
import sys
import xml.parsers.expat


def usage():
    print("----------------------------------------------------------------------------")
    print("Usage:")
    print("\t %s -f <file> -a <act>" % sys.argv[0])
    print("\t %s --file <file> --action <act>" % sys.argv[0])
    print("Ou")
    print("\t %s -d <dir> -a <act>" % sys.argv[0])
    print("\t %s --directory <file> --action <act>" % sys.argv[0])
    print("\n")
    print("\n- <file> : Le fichier de log generer par la distribution exp: di_MO_ ...")
    print("- <dir>  : Le repertoire temporaire des fichiers XML extraits ")
    print("\n")
    print("- <act>  = 'extract' => Pour extraire les fichiers XML a partir du fichier log")
    print("         = 'move'    => Pour deplacer les fichiers XML dans les bons repertoires")
    print("         = 'all'     => Pour extraire les XML et faire le move")
    print("----------------------------------------------------------------------------")
    sys.exit(-1)


def parse_xml_file(file):
    parser = xml.parsers.expat.ParserCreate()
    parser.ParseFile(open(file, "r"))


def recover_xml_file(log_file, dir_name):
    nbr_file_recovered = 0
    with open(log_file, "r") as file:
        for nbr, line in enumerate(file):
            if line.__contains__("<?xml"):
                recov_filename = line.split(',')[0].split('/')[-1]
                # print recov_filename
                start = "<?xml"
                end = "</log>"
                s = line.find(start)
                e = line.find(end)
                # result = re.search(deb + "(.+?)" + fin, line, re.IGNORECASE).group(1)
                # result = re.match("<.*?>", line).group()
                # print result
                recov_xml = line[s:(e + len(end))]
                # print recov_xml
                # rename recov_filename if not found
                if len(recov_filename) == 0:
                    recov_filename = "%s.xml" % nbr
                elif not recov_filename.endswith('.xml'):
                    recov_filename = "%s-%s.xml" % (nbr, recov_filename)

                recov_filename = os.path.join(dir_name, recov_filename)

                with open(recov_filename, "w") as recov_xml_file:
                    recov_xml_file.write(recov_xml)
                    print "(0) %s => file recovered " % recov_filename
                    nbr_file_recovered += 1
    return nbr_file_recovered


def move_file_to_directory(dir_name, dst_dir, uid, gid):
    nbr_file_ok = 0
    nbr_file_exist = 0
    nbr_file_bad = 0
    for file in glob.glob(dir_name + "/*.xml"):
        print file
        # check validity of xml file
        try:
            parse_xml_file(file)
            print "(1) %s => OK : valid xml format" % file
        except Exception, ex:
            print "(1bis) %s => bad xml format, cause: %s" % (file, ex)
            # rename file to bad
            try:
                # shutil.move(file, os.path.join(file, ".bad"))
                os.rename(file, file + ".bad")
                nbr_file_bad += 1
                continue
            except Exception, ex:
                print "%s => can't rename file" % file
        # change uid and gid for recovered xml file
        try:
            os.chown(file, uid, gid)
            print "(2) %s => OK : change mode to dist:dist" % file
        except Exception, ex:
            print "(2bis) can't not change owner:group for this file: %s, cause: %s " % (file, ex)
            # sys.exit(-3)

        file_name = os.path.basename(file)
        mission = file_name.split('-')[0]
        timestamp = file_name.split('-')[1]
        step = file_name.split('-')[2].split('.')[0]

        g_day = timestamp[:2]
        g_month = timestamp[2:4]
        g_year = timestamp[4:8]
        g_hour = timestamp[8:10]
        g_minute = timestamp[10:]

        sub_dir = "%s/%s/%s" % (g_month, g_day, g_hour)
        move_file_to = os.path.join(dst_dir, sub_dir)

        dst_dir_month = os.path.join(dst_dir, g_month)
        dst_dir_month_day = os.path.join(dst_dir_month, g_day)
        dst_dir_month_day_hour = os.path.join(dst_dir_month_day, g_hour)

        if not os.path.exists(dst_dir_month):
            os.makedirs(move_file_to)
            os.chown(dst_dir_month, uid, gid)
            os.chown(dst_dir_month_day, uid, gid)
            os.chown(dst_dir_month_day_hour, uid, gid)
        elif not os.path.exists(dst_dir_month_day):
            os.makedirs(dst_dir_month_day_hour)
            os.chown(dst_dir_month_day, uid, gid)
            os.chown(dst_dir_month_day_hour, uid, gid)
        elif not os.path.exists(dst_dir_month_day_hour):
            os.mkdir(dst_dir_month_day_hour)
            os.chown(dst_dir_month_day_hour, uid, gid)

        if os.path.exists(move_file_to):
            check_exist_file = os.path.join(move_file_to, file_name)
            if os.path.exists(check_exist_file):
                print "(3) %s => WARNING : file already exist" % check_exist_file
                os.rename(file, file + ".exist")
                nbr_file_exist += 1
                print "(4) %s => Rename file to: %s.exist" % (file, file)
            else:
                shutil.move(file, move_file_to)
                nbr_file_ok += 1
                print "(3) %s => OK : file moved with success to %s" % (file, move_file_to)
        else:
            print "(3) %s => ERROR : directory not found" % move_file_to
    return nbr_file_ok, nbr_file_exist, nbr_file_bad


def main():
    argument = sys.argv[1:]
    opts = None

    if len(argument) < 4:
        usage()

    try:
        opts, args = getopt.getopt(argument, 'f:d:a:h', ["file=", "directory=", "action=", "help="])
    except getopt.GetoptError, ex:
        print ex
        usage()

    log_file = None
    tmp_dir = None
    action = None
    nbr_file_recovered = 0
    file_ok = 0
    file_exist = 0
    file_bad = 0

    for (opt, arg) in opts:
        if opt in ('-f', '--file'):
            log_file = arg
            # print log_file
            if not os.path.exists(log_file):
                print "%s => File not found" % log_file
                sys.exit(-2)
        elif opt in ('-d', '--directory'):
            tmp_dir = arg
            # print tmp_dir
            if not os.path.exists(tmp_dir):
                print "%s => directory not found" % tmp_dir
                sys.exit(-2)
        elif opt in ('-a', '--action'):
            action = arg.lower()
            # print action
            if action not in ('extract', 'move', 'all'):
                usage()
            elif action == "extract" and log_file is None:
                usage()
            elif action == "move" and tmp_dir is None:
                usage()
            elif action == "all" and tmp_dir is not None:
                usage()
        else:
            usage()

    try:
        # create folder to save xml file
        current_dir = os.path.dirname(os.path.realpath(__file__))
        dir_name = os.path.join(current_dir, "tmp_recovering_xml")
        dst_dir = "/var/www/html/MOxml"
        user_id = "dist"  # user id (owner)
        group_id = "dist"  # group id
        uid = pwd.getpwnam(user_id).pw_uid
        gid = grp.getgrnam(group_id).gr_gid

        if action == "extract":
            if not os.path.exists(dir_name):
                try:
                    os.makedirs(dir_name)
                except Exception, ex:
                    print "can't create recover xml folder, cause: %s " % ex
                    sys.exit(0)
            # extract xml files from log files
            nbr_file_recovered = recover_xml_file(log_file, dir_name)
            print "\n- Extracting MO files end with success in: %s folder" % dir_name
            print "\n- Result:"
            print "\t- Recovered files: %s" % nbr_file_recovered
            print "Success !!"
            sys.exit(0)
        elif action == "move":
            # move xml file to the specific directories
            file_ok, file_exist, file_bad = move_file_to_directory(tmp_dir, dst_dir, uid, gid)
        elif action == "all":
            if not os.path.exists(dir_name):
                try:
                    os.makedirs(dir_name)
                except Exception, ex:
                    print "can't create recover xml folder, cause: %s " % ex
                    sys.exit(0)
            # extract xml files from log files
            nbr_file_recovered = recover_xml_file(log_file, dir_name)
            # move xml file to the specific directories
            file_ok, file_exist, file_bad = move_file_to_directory(dir_name, dst_dir, uid, gid)

        # ERROR : when files are moved owners changed to root:root
        # corrected here
        # proc = subprocess.Popen(["chown", "-R", user_id, ":", group_id, dst_dir], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # print "\n- Change owners to %s:%s on %s directories" % (user_id, group_id, dst_dir)
        # subprocess.call(["chown", "-R", user_id + ":" + group_id, dst_dir, "&"])

        print "\n- Result:"
        print "\t - Recovered files: %s" % nbr_file_recovered
        print "\t - Transferred files: %s" % file_ok
        print "\t - Existing files: %s" % file_exist
        print "\t - Bad files: %s" % file_bad
    
    except KeyboardInterrupt, ex:
        print "\nExecution interrupted ..."
        sys.exit(0)


if __name__ == "__main__":
    main()
    print "success !!"