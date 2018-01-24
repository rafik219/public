# -*- conding: utf-8 -*-

#
# rbo 
# 09/12/2017
# install new http distrib chine
#

import os
import subprocess
import urllib.request
import time
import shutil

tmp_dir = r"C:\\tmp_install"
pip_path = r"C:\iplabel\python\Python34\Scripts\pip3.4.exe"
urllib3_path = r"C:\iplabel\python\Python34\Lib\site-packages\urllib3"
ipl_repo_url = "https://0.0.0.0/iplabel/SA/outils/distribution/linux/"
distribhttp_path = os.getenv('iplabel') + "\\bin\\distrib\\"
distribhttp_name = "uploadvais3.py"
distribhttp_full_path = os.path.join(distribhttp_path, distribhttp_name)
distribhttp_full_path_old = distribhttp_full_path + ".old"
nrpe_dir = r"C:\Program Files\NSClient++\scripts"
distrib_check_name = "check_distribvai.py"
distrib_check_path = os.path.join(nrpe_dir, distrib_check_name)
nclient_file = r"C:\Program Files\NSClient++\NSC.ini"
add_nsclient_line = r'check_distrib_diag=python "C:\Program Files\NSClient++\scripts\check_distribvai.py"'
script_dist = "uploadvais3_chine_rebond.py"
script_check_dist = "check_distribvai.py"

def downloadfile_on_repo(filename, dst=None):
    url_file = ipl_repo_url + filename
    if dst is not None:
        local_file_path = os.path.join(dst, filename)
    else:
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)
        local_file_path = os.path.join(tmp_dir, filename)
    password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(None, ipl_repo_url, "exploit", "XXXXXXXXX") 
    handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
    opner = urllib.request.build_opener(handler)
    response = opner.open(url_file)        
    if response.status == 200:
        f = open(local_file_path, 'w')
        f.write(response.read().decode('utf-8'))
        f.close()
        if os.path.exists(local_file_path):
            print("OK: {} file download !!".format(local_file_path))
            return True
        else:
            print("KO: {} file is not download !!")
    else:
        print("KO: {} error during download !!, code: {}".format(url_file, response.status))
    return False

def execute_shell_cmd(command):
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = proc.communicate()
    if out != b'':
        print("Success: ", out.decode('utf-8'))
        return True
    if err != b'':
        print("Error: ", err.decode('utf-8'))
    return False

print("Starting ...")
print("\n1) Check existing pip command:")
print("--------------------------------")
# download pip if not exist
if not os.path.exists(pip_path):
    if downloadfile_on_repo("get_pip.py"):
        if execute_shell_cmd(["python", os.path.join(tmp_dir, "get_pip.py")]):
            print("OK: pip is available now....")
else:
    print("OK: pip already exist")

print("\n2) Check existing urllib3 module:")
print("-----------------------------------")
# download urllib3 if not exist
if not os.path.exists(urllib3_path):
    if execute_shell_cmd([pip_path, "install", "urllib3"]):
        print("OK: urllib3 is available now.....")
else:
    print("OK: urllib3 already exist")

print("\n3) Download script from repository :")
print("--------------------------------------")
if not os.path.exists(distribhttp_full_path_old):
    print('\t=> Try to stop "dtm - diag" task":')
    execute_shell_cmd(["schtasks", "/End", "/TN", r'"\iplabel\dtm - diags"'])
    time.sleep(2)
    try:
        os.rename(distribhttp_full_path, distribhttp_full_path + ".old")
        print("remaning ok {} to {}".format(distribhttp_full_path, distribhttp_full_path + ".old"))
    except Exception as ex:
        print("rename error, cause: ", ex)
    
    print("\n=> Download dist scripts")
    if downloadfile_on_repo(script_dist, dst=distribhttp_path):
        print("OK: {} download with success !!".format(script_dist))
        try:
            distrib_download_path = os.path.join(distribhttp_path, script_dist)
            os.rename(distrib_download_path, distribhttp_full_path)
            print("remaning ok {} to {}".format(distrib_download_path, distribhttp_full_path))
        except Exception as ex:
            print("rename error, cause: ", ex)
    time.sleep(2)
    print("\t=> Run task:")
    execute_shell_cmd(["schtasks", "/Run", "/TN", r'"\iplabel\dtm - diags"'])
else:
    print("Distribdiag script exists: ", distribhttp_full_path_old)

if not os.path.exists(distrib_check_path):
    print("\n=> Download check script")
    if downloadfile_on_repo(script_check_dist, dst=nrpe_dir):
        print("OK: {} download ".format(distrib_check_path))
        
    print("update NSC.ini")
    if os.path.exists(nclient_file):
        with open(nclient_file, 'a') as f:
            f.write(add_nsclient_line)
        print("OK: NSC.ini File updated : ", nclient_file)
    else:
        print("KO: File does not exist: ", nclient_file)  
    
    print("restart NSClient ++")
    for action in ("stop", "start"):
        if execute_shell_cmd(["net", action, "NSClientpp"]):
            print("OK : NSClientapp ", action)
        else:
            print("KO: NSClientapp ", action)
else:
    print("Distrib check exist: ", distrib_check_path)

print("\n4) remove {} directory".format(tmp_dir))
print("--------------------------------------")
if os.path.exists(tmp_dir):
    try:
        shutil.rmtree(tmp_dir)
        print("OK: {} removed !!".format(tmp_dir))
    except Exception as ex:
        print(ex)
else:
    print("{} not found !!".format(tmp_dir))

print("Success !!")
    
    