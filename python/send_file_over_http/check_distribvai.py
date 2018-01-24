# -*- coding: utf-8 

#
# rbo 
# 09/12/2017
# check Nagios Distrib vai Http
#

import os
import sys
import mmap

OK_STATUS = 0
WARNING_STATUS = 1
CRITICAL_STATUS = 2

log_dir = os.getenv('iplabel') + "\\log"
log_file_name = "uploadvais3.log"
log_file_path = os.path.join(log_dir, log_file_name)

if os.path.exists(log_file_path):    
    with open(log_file_path, mode='r') as logfile:
        content = mmap.mmap(logfile.fileno(), 0, access=mmap.ACCESS_READ)        
        if content.rfind(b'ERROR') != -1:
            print("Probleme de remontee des VAI vers la machine de rebond, plus de details dans: {}".format(log_file_path))
            sys.exit(WARNING_STATUS)
        else:
            print("Pas de probleme de remontee des VAI vers la machine de rebond")
            sys.exit(OK_STATUS)   
else:
    print("Log file : {} Not found !!".format(log_file_path))
    sys.exit(WARNING_STATUS)
            