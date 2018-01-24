#!/usr/bin/python2.7
# -*- coding: iso-8859-15 -*-

# rbo
# version: 18/11/2016

from datetime import datetime
import os
import mmap
import sys



CRITICAL_STATUS = 2
WARNING_STATUS = 1
OK_STATUS = 0

Log_dir = "/home/fwuser/Backup_All_Fw_Config/"
today_date = datetime.now().strftime("%Y%m%d")
current_log_file = os.path.join(Log_dir, "getFwConfiguration_"+today_date+".log")

if os.path.exists(current_log_file):
    with open(current_log_file, "r") as file:
        string = mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ)
        if string.find('KO') != -1:
            print "Un ou pleusieurs backup en echec, pour consulter: http://00.00.00.00/iplabel/firewall_backup_config/%s" % os.path.basename(current_log_file)
            sys.exit(CRITICAL_STATUS)
        else:
            print "Tous les backup sont: OK"
            sys.exit(OK_STATUS)
# else
print "Pas de fichier de log a analyser!"
sys.exit(OK_STATUS)









