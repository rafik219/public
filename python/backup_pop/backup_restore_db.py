#!/usr/bin/env python2.7
# -*- coding: utf-8

# ---------------------------------------------
#
# author: rbo
# version: 26/06/2017
# utility: backup network + database 11g XE configuration
#
# rbo : 04/07/2017 add database 10g XE configuration
#
# rbo : 20/30/2018 : - backup database 10g XE.
#                    - restore database 10g XE.
#                    - restore database 11g XE.
#
# rbo : 18/04/2018 : - changing backup restore mode
# rbo : 19/04/2018 : - add ConfigParam class
# rbo : 20/04/2018 : - migrate oracle 10g to 11g
#
# ----------------------------------------------

import glob
import logging
import logging.handlers
import os
import shutil
import subprocess
import sys
from datetime import datetime
from time import sleep
import argparse
import paramiko
import yaml
import urllib2
from re import findall
from zipfile import ZipFile
from yaml import load
import ssl
from socket import gethostname


class ConfigParam:
    
    DBCONFIG                = "/home/dist/DBconfig.conf"
    DB_PASSWORD             = "XXXXX"
    TMP_BACKUP_TABLE_DIR    = "/home/oracle/dmpdir"
    BACKUP_DIR              = "/root/backup_bdd_config/backup_files"
    YAML_FILE_NAME          = "backup_config_status.yml"
    SFTP_SERVER             = "0.0.0.0"
    SFTP_SERVER_PORT        = 22
    SFTP_SERVER_LOGIN       = "AAAAAAA"
    SFTP_SERVER_PASSWORD    = "XXXXXXX"
    HTTP_SERVER_LOGIN       = "XXXXXXX"
    HTTP_SERVER_PASSWORD    = "XXXXXXX"
    HTTP_SERVER_URL         = "https://XXXXXXX/iplabel/SA/backup/BDD"
    
    @property
    def hostname(self):
        return gethostname()

    @property
    def lsb_release(self):
        # try to get linux os distribution
        lsb_release = ""
        try:
            import platform
            lsb_release = platform.linux_distribution()[1][0]
        except Exception, ex:
            print "unable to get OS distribution, cause: %s" % ex
        self.logger.info('Database OS Release : %s' % lsb_release)
        return lsb_release
    


class Backupdb:
    
    def __init__(self, popname=None, idsite=None, logger=None):
        self.logger = logger       
        self.alias_idsite = popname
        self.idsite = idsite        
        self.copy_status_dict = dict()        
        self.yaml_file = os.path.join(ConfigParam.BACKUP_DIR, ConfigParam.YAML_FILE_NAME)        
        self.list_backup_file = self.get_list_backup_file()
        self.now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")  

    def get_list_backup_file(self):
        # try to get linux os distribution
        lsb_release = ConfigParam.lsb_release
        # if platform is: Centos 5.x
        # else: Centos 6.x
        if lsb_release == "5":
            oracle_base = "/usr/lib/oracle/xe/app/oracle"
            oracle_home = os.path.join(oracle_base, "product/10.2.0/server")            
        else:
            oracle_base = "/u01/app/oracle"
            oracle_home = os.path.join(oracle_base, "product/11.2.0/xe")       
        
        tnsnames = os.path.join(oracle_home, "network/admin/tnsnames.ora")
        listner = os.path.join(oracle_home, "network/admin/listener.ora")

        list_backup_file = {            
            "network":    [
                "/etc/resolv.conf",
                "/etc/hosts",
                "/etc/sysconfig/network",
                "/etc/sysconfig/network-scripts/ifcfg-eth0"
            ],
            "oracle":     [
                tnsnames,
                listner
            ],
            "dist":       [
                "/home/dist/DBconfig.conf",
                "/home/dist/dist.conf",
                "/home/dist/mo.conf",
                "/home/dist/site.conf"
            ],
            "dns":        [
                "/etc/named.caching-nameserver.conf",
                "/etc/named.conf"
            ],
            "nagios":     [
                "/etc/nagios/nrpe.cfg"
            ],
            "filesystem": [
                "/etc/fstab"
            ],
            "applinux":   [
                "/home/dist/tools/appLinux_config.yml",
                "/etc/inittab"
            ]
        }
        return list_backup_file

    def copy_file(self, file_path, dest):
        copied_status = False
        if os.path.exists(file_path):
            try:
                shutil.copy2(file_path, dest)
                copied_status = True
            except Exception, ex:
                print "Error: Can't copy file: %s to %s, cause: %s" % (file_path, dest, ex)
        return copied_status

    def start_backup(self):
        # Create backup directory.
        # or
        # purge it if already exist
        if not os.path.exists(ConfigParam.BACKUP_DIR):
            try:
                os.makedirs(ConfigParam.BACKUP_DIR)
                self.logger.info("backup directory : %s created." % ConfigParam.BACKUP_DIR)
            except OSError, ex:
                self.logger.error("Can't create %s directory, cause: %s" % (ConfigParam.BACKUP_DIR, ex))
                sys.exit(-1)
        else:
            self.logger.info("backup dir : %s already exist, deleting content" % ConfigParam.BACKUP_DIR)
            for root, dirs, files in os.walk(ConfigParam.BACKUP_DIR):
                for d in dirs:
                    try:
                        os.rmdir(os.path.join(root, d))
                        self.logger.info("directory : %s -> deleted" % d)
                    except OSError, ex:
                        self.logger.error("Can't remove %s directory, cause: %s" % (d, ex))
                for f in files:
                    try:
                        os.remove(os.path.join(root, f))
                        self.logger.info("file : %s -> deleted" % f)
                    except OSError, ex:
                        self.logger.error("Can't remove %s file, cause: %s" % (f, ex))

        # get schema, site and alias (from backup_dir)
        # and
        # backup database tables.
        if os.path.exists(ConfigParam.DBCONFIG):
            self.logger.info("reading %s ..." % ConfigParam.DBCONFIG)
            with open(ConfigParam.DBCONFIG, "r") as fconf:
                for line in fconf.readlines():
                    if line != "\n":
                        idsite = line.strip().split(":")[0]
                        alias_idsite = line.strip().split(":")[1]
                        schema = line.strip().split(":")[2]
                        self.logger.info("idsite: %s, alias: %s, schema: %s" % (idsite, alias_idsite, schema))

                        # db_connection = "%s/%s" % (schema, ConfigParam.DB_PASSWORD)
                        db_connection = "%s/%s@%s" % (schema, ConfigParam.DB_PASSWORD, ConfigParam.hostname)
                        # backup_table_file_name = "%s/%s_%s_%s_TABLES_%s.dmp" % (
                        # ConfigParam.TMP_BACKUP_TABLE_DIR, alias_idsite, idsite, schema,
                        # self.now.split(' ')[0].replace('/', ''))
                        backup_table_file_name = "%s_%s_%s_TABLES_%s.dmp" % (alias_idsite, idsite, schema, self.now.split(' ')[0].replace('/', ''))
                        list_backup_table = "PARAMETRESAPPLICATION,SCHEMA,MISSION,MAINTENANCEMISSION"
                        log_backup_file_name = "backup_BDD_%s_%s.log" % (idsite, schema)

                        # sub_cmd = "exp %s FILE=%s TABLES=%s LOG=%s" % (db_connection, backup_table_file_name, list_backup_table, log_backup_file_name)     
                        
                        # dmpdir is directory created for datapump storage for oracle XE users
                        sub_cmd = "expdp %s DIRECTORY=dmpdir DUMPFILE=%s TABLES=%s LOGFILE=%s" % (
                            db_connection, backup_table_file_name, list_backup_table, log_backup_file_name)
                        
                        print(sub_cmd)
                        
                        command = "su - oracle -c '%s'" % sub_cmd                        
                        try:
                            subprocess.Popen(command, stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE, shell=True).communicate()                            
                            self.logger.info("table backup generated with success on: %s" % backup_table_file_name)
                        except Exception, ex:
                            self.logger.error(
                                    "Can't export Tables: {} from XE database, cause: {}".format(list_backup_table, ex))
                        sleep(3)
        else:
            self.logger.error("%s file not found" % ConfigParam.DBCONFIG)
            sys.exit(-3)

        # copy list_backup_files
        # and
        # format dictionary with status after copying
        for sub_dict in self.list_backup_file.keys():
            copy_file_status = list()
            for file_config in self.list_backup_file[sub_dict]:
                tmp_copy_file_status1 = dict()
                tmp_copy_file_status1["path"] = file_config
                if self.copy_file(file_config, ConfigParam.BACKUP_DIR):
                    tmp_copy_file_status1["status"] = "OK"
                else:
                    tmp_copy_file_status1["status"] = "KO"

                copy_file_status.append(tmp_copy_file_status1)
                self.copy_status_dict[sub_dict] = copy_file_status

        # move dmp_file to backup_dir
        # and
        # add backup table status in copy_status_dict
        backup_tables_status = list()
        for dmp_file in glob.glob(ConfigParam.TMP_BACKUP_TABLE_DIR + "/*.dmp"):
            status = "KO"
            if dmp_file.endswith("TABLES_" + self.now.split(' ')[0].replace('/', '') + ".dmp"):
                try:
                    shutil.move(dmp_file, ConfigParam.BACKUP_DIR)
                    self.logger.info("moving file : %s -> %s" % (dmp_file, ConfigParam.BACKUP_DIR))
                    status = "OK"
                except OSError, ex:
                    self.logger.error("Can't move %s -> %s directory, cause: %s" % (dmp_file, ConfigParam.BACKUP_DIR, ex))

                backup_tables_status.append({"path": dmp_file, "status": status})

        # print backup_tables_status
        self.copy_status_dict["backupdb"] = backup_tables_status

        # get service status.
        list_service = ["oracle", "httpd", "nfs", "named", "ipldist"]
        dict_service_status = dict()
        self.logger.info("check status of services:")
        for service in list_service:
            if service == 'oracle':
                cmd = "ps -ef | grep -v grep | grep -c pmon"
                out, err = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                            shell=True).communicate()
                if out != "" and int(out) > 0:
                    self.logger.info("+ service '%s' is running" % service)
                    dict_service_status[service] = "OK"
                else:
                    self.logger.error("unknown service status for '%s' service, my be service is not started" % service)
                    dict_service_status[service] = "KO"
            else:
                cmd = "service %s status" % service
                out, err = subprocess.Popen(cmd.split(" "), stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE).communicate()
                if out != "" and (
                        out.strip().lower().find('running') != -1 or out.strip().lower().find('en cours') != -1):
                    self.logger.info("+ service '%s' is running" % service)
                    dict_service_status[service] = "OK"
                else:
                    self.logger.error("unknown service status for '%s' service, my be service is not started" % service)
                    dict_service_status[service] = "KO"

        # add to copy_status_dict
        self.copy_status_dict["services"] = dict_service_status
        
        # add os release to copy_status_dict
        self.copy_status_dict["centos_release"] = ConfigParam.lsb_release

        # create yml file using result dictionary
        with open(self.yaml_file, "w") as file_dumper:
            self.logger.info("dumping result on YAML file: %s" % self.yaml_file)
            try:
                yaml.dump(self.copy_status_dict, file_dumper)
                # yaml.dump(copy_status_dict, file_dumper, default_flow_style=False)
                self.logger.info("dump end with success !!")
            except Exception, ex:
                self.logger.error("when dumping result on: %s file, cause: %s" % (self.yaml_file, ex))
                sys.exit(-2)

    def upload_to_sftp_server(self):
        # compress all backup files on backup_dir
        # and
        # create zip file
        compress_file_name = "%s_%s_BACKUP_%s" % (
            self.alias_idsite, self.idsite, self.now.split(' ')[0].replace('/', ''))
        compress_file = os.path.join(os.path.dirname(os.path.abspath(ConfigParam.BACKUP_DIR)), compress_file_name)
        archive_file_path = ""

        # supported_format = shutil.get_archive_formats()
        supported_format = [('zip', 'zip'), ('gztar', 'tar.gz'), ('bztar', 'tar.bz2')]

        for compress_format in supported_format:
            try:
                shutil.make_archive(compress_file, compress_format[0], ConfigParam.BACKUP_DIR, logger=self.logger)
                archive_file_path = "%s.%s" % (compress_file, compress_format[1])
                self.logger.info("compressing end with success : %s" % archive_file_path)
                break
            except Exception, ex:
                self.logger.error("'%s' archive format not supported, cause: %s" % (compress_format[0], ex))
                self.logger.info("supported format: %s" % supported_format)
                self.logger.info("try with '%s' format" % compress_format[0])
                continue

        # purge backup directory after compression
        if os.path.exists(archive_file_path) and os.path.getsize(archive_file_path) > 0:
            try:
                shutil.rmtree(ConfigParam.BACKUP_DIR)
                self.logger.info("Purge local backup directory: %s" % ConfigParam.BACKUP_DIR)
            except shutil.Error, ex:
                self.logger.error("Can't delete %s directory, cause: %s" % (ConfigParam.BACKUP_DIR, ex))
        retry = 0
        # upload compressed file to the repository.
        while retry < 5:
            transport = paramiko.Transport((ConfigParam.SFTP_SERVER, ConfigParam.SFTP_SERVER_PORT))
            transport.connect(username=ConfigParam.SFTP_SERVER_LOGIN, password=ConfigParam.SFTP_SERVER_PASSWORD)

            sftp = paramiko.SFTPClient.from_transport(transport)

            new_dir = "%s_%s" % (self.alias_idsite, self.idsite)

            try:
                if new_dir not in sftp.listdir():
                    sftp.mkdir(new_dir)
                    self.logger.info("directory : '%s' created on sftp server : '%s'" % (new_dir, ConfigParam.SFTP_SERVER))
                else:
                    # delete old backup files, and keep at least 3 backup
                    self.logger.info("try to purge old backup files on the server")
                    for backup_file in sftp.listdir(new_dir):
                        generation_date = backup_file.split(".")[0].split("_")[3]
                        if int(self.now.split(' ')[0].replace('/', '')) - int(generation_date) >= 3:
                            try:
                                sftp.remove(os.path.join(new_dir, backup_file))
                                self.logger.info("old backup '%s' -> deleted from the server" % backup_file)
                            except Exception, ex:
                                self.logger.error(
                                    "unable to deleted %s backup on server, cause: %s" % (backup_file, ex))
            except Exception, ex:
                self.logger.error("when trying to list directory on sftp server, cause: %s" % ex)
                sys.exit(-4)

            sftp_archive_path = "%s/%s" % (new_dir, os.path.basename(archive_file_path))

            try:
                # Put file on the sftp server
                sftp.put(archive_file_path, sftp_archive_path)
                self.logger.info("archive transferred with success !")
            except Exception, ex:
                self.logger.error("when sending archive to the server, cause: %s" % ex)
                retry += 1
                sftp.close()
                sleep(3)
                continue

            try:
                self.logger.info("try to comparing size between file transferred and local file")
                # comparing size between local archive and remote archive
                local_archive_size = os.stat(archive_file_path).st_size
                remote_archive_size = sftp.stat(sftp_archive_path).st_size

                # we tolerate 5 bytes between them
                if abs(local_archive_size - remote_archive_size) not in range(0, 5):
                    self.logger.error("transfer not properly completed, retry sending archive !!")
                    retry += 1
                    sleep(3)
                    continue
                else:
                    self.logger.info("we transferred the same size, difference : %s bytes" % abs(
                            local_archive_size - remote_archive_size))
                    sftp.close()
                    try:
                        # delete local archive file after transfer
                        os.remove(archive_file_path)
                        self.logger.info("deleting local archive file : %s" % archive_file_path)
                    except OSError, ex:
                        self.logger.error(
                            "we can't delete local archive file : %s , cause: %s " % (local_archive_size, ex))
                    break
            except Exception, ex:
                self.logger.error("we can't comparing archive size, cause: %s" % ex)
                sys.exit(-5)


class Restoredb:
    
    def __init__(self, logger=None, popname=None, idsite=None):
        self.logger = logger      
        self.pop_name = popname
        self.pop_id = idsite
        self.url_access = "%s/%s_%s" % (ConfigParam.HTTP_SERVER_URL, self.pop_name, self.pop_id)
        self.last_file_name = "%s_%s_BACKUP_%s.zip" % (self.pop_name, self.pop_id, datetime.now().strftime("%Y%m%d"))

    def send_http_request(self, url):
        response = None
        try:
            # ignore certification check, error on CentOS 5.9 because SSL is not updated
            if (not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None)):
                ssl._create_default_https_context = ssl._create_unverified_context
            manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
            manager.add_password(None, self.url_access, ConfigParam.HTTP_SERVER_LOGIN, ConfigParam.HTTP_SERVER_PASSWORD)
            auth = urllib2.HTTPBasicAuthHandler(manager)
            opener = urllib2.build_opener(auth)
            urllib2.install_opener(opener)
            response = urllib2.urlopen(url)
        except Exception, ex:
            self.logger.error("Problem during connection to this url: %s, cause: %s" % (self.url_access, ex))
        return response

    def get_list_backup_file(self):
        list_file = []
        resp = self.send_http_request(self.url_access)
        if resp is not None:
            if resp.code == 200:
                content = resp.read()
                regex = r'href="(.+?)">'
                match_all = findall(regex, content)
                list_file = filter(lambda k: k.endswith(".zip"),
                                   filter(lambda k: k.startswith("%s_%s" % (self.pop_name, self.pop_id)), match_all))
        return list_file

    def download_last_backup(self):
        is_download = False
        file_download = ""
        files_on_server = self.get_list_backup_file()
        if len(files_on_server) != 0:
            if self.last_file_name in files_on_server:
                file_download = self.last_file_name
            else:
                file_download = files_on_server[-1]

            local_file_download = open(file_download, 'wb')

            full_url_download_file = self.url_access + "/" + file_download
            resp = self.send_http_request(full_url_download_file)

            if resp is not None:
                metadata = resp.info()
                file_size = int(metadata.getheaders('Content-Length')[0])
                self.logger.info('Downloading: %s Bytes: %s' % (full_url_download_file, file_size))
                file_sz_dl = 0
                block_sz = 8192
                while True:
                    _buffer = resp.read(block_sz)
                    if not _buffer:
                        break
                    file_sz_dl += len(_buffer)
                    local_file_download.write(_buffer)
                    status = r"%10d [%3.2f%%]" % (file_sz_dl, file_sz_dl * 100 / file_size)
                    self.logger.info(status)

                if os.path.exists(file_download):
                    self.logger.info("SUCCESS: file %s downloaded !" % file_download)
                    is_download = True
                else:
                    self.logger.error("ERROR: file not downloaded !")
            local_file_download.close()
        return is_download, file_download

    def extract_downloaded_file(self, compress_file=None):
        is_extract = False
        extract_dir = ""
        if compress_file is not None:
            is_download, file_download = True, compress_file
        else:
            is_download, file_download = self.download_last_backup()
        if is_download and file_download != "":
            try:
                extract_dir = file_download.split(".")[0]
                extract_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), extract_dir)
                zip_ref = ZipFile(file_download, 'r')
                zip_ref.extractall(extract_dir)
                zip_ref.close()
                if os.path.exists(extract_dir) and os.path.isdir(extract_dir):
                    is_extract = True
            except Exception, ex:
                self.logger.error("ERROR: during extracting %s file, cause: %s" % (file_download, ex))
        return is_extract, extract_dir

    def get_linux_release(self):
        import platform
        linux_release = platform.linux_distribution()[1][0]
        return linux_release

    def mange_service(self, service, action):
        self.logger.info("Launch command : service %s %s" % (service, action))
        proc = subprocess.Popen("service %s %s" % (service, action), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                shell=True)
        out, err = proc.communicate()
        return out, err

    def start_restoration(self, zip_file=None):
        if zip_file is not None:
            is_extract, extract_dir = self.extract_downloaded_file(compress_file=zip_file)
        else:
            is_extract, extract_dir = self.extract_downloaded_file()
        # is_extract, extract_dir = True, "STOIPO_1255_BACKUP_20180131"
        if is_extract and extract_dir != "":
            backup_config = os.path.join(extract_dir, "backup_config_status.yml")
            if os.path.exists(backup_config):
                with open(backup_config, 'r') as stream:
                    yaml_file = load(stream)   
                    current_linux_release = ConfigParam.lsb_release
                    backup_db_os_release = yaml_file.get('centos_release')                                          
                    for service, result in sorted(yaml_file.items()):
                        self.logger.info("\n- %s configuration :" % service)
                        if service not in ("services", "backupdb", "centos_release", "network"):
                            for opt in result:
                                if opt.get('status') == "OK":
                                    local_config_file = opt.get('path')
                                    source_config_file = os.path.join(extract_dir, os.path.basename(opt.get('path')))
                                    # local_config_file_dir = os.path.dirname(local_config_file)
                                    # rename local_config_file
                                    if os.path.exists(local_config_file):
                                        # if True:
                                        # detecting same os_version: CentOs5 -> CentOs5 or CentOs6 -> CentOs6
                                        if current_linux_release == backup_db_os_release:
                                            try:
                                                # rename origin file
                                                os.rename(local_config_file, local_config_file + "-orig")
                                                self.logger.info("\t OK : Renaming %s - %s" % (local_config_file,
                                                                                               local_config_file + "-orig"))
                                                # move local file
                                                os.rename(source_config_file, local_config_file)
                                                self.logger.info(
                                                        "\t OK : Moving %s -> %s" % (source_config_file, local_config_file))
                                            except Exception, ex:
                                                self.logger.error("ERROR : when rename/move %s file, cause: %s" % (
                                                    local_config_file, ex))
                                        else:
                                            # different OS: CentOs5 -> CentOs 6
                                            # allow copying dist, nagios, dns
                                            if service in ("dist", "nagios", "dns") or (service == "network" and opt.get('path').find("ifcfg-eth0") == -1):
                                                try:
                                                    # rename origin file
                                                    os.rename(local_config_file, local_config_file + "-orig")
                                                    self.logger.info("\t OK : Renaming %s - %s" % (local_config_file,
                                                                                                   local_config_file + "-orig"))
                                                    # move local file
                                                    os.rename(source_config_file, local_config_file)
                                                    self.logger.info(
                                                            "\t OK : Moving %s -> %s" % (source_config_file, local_config_file))
                                                except Exception, ex:
                                                    self.logger.error("ERROR : when rename/move %s file, cause: %s" % (local_config_file, ex))                                            
                                            elif service == "oracle":
                                                self.logger.info("Not Need to copy listner.ora & tnsnames.ora !!")
                                            elif service == "filesystem":
                                                self.logger.info("Not Need to copy listner.ora & tnsnames.ora !!")
                                            else:
                                                self.logger.info("==> not treated: %s - %s " % (service, opt))                                                                               
                                    else:
                                        self.logger.error("\t KO : File not found %s" % local_config_file)
                                else:
                                    self.logger.info("\t No configuration need for : %s" % opt.get('path'))

                        elif service == "backupdb":
                            linux_release = ConfigParam.lsb_release
                            dmpdir = "/home/oracle/dmpdir"
                            for res in result:
                                schema_name = os.path.basename(res.get('path')).split('_')[2]
                                if res.get('status') == 'OK':
                                    # full_path_current_dir = os.getcwd()
                                    full_path_current_dir = os.path.dirname(os.path.realpath(__file__))
                                    self.logger.info("-----------------------------------")
                                    self.logger.info(full_path_current_dir)
                                    self.logger.info("-----------------------------------")
                                    dmp_file_location = os.path.join(os.path.dirname(full_path_current_dir), os.path.join(extract_dir, os.path.basename(res.get('path'))))                                    
                                    user_schema = os.path.basename(res.get('path')).split('_')[2]                                                                        
                                    oracle_schema_script_dir = os.path.join(full_path_current_dir, os.path.join(os.path.dirname(extract_dir), "oracle_schema"))
                                    create_user_sh_script = os.path.join(oracle_schema_script_dir, "create_users10g.sh")
                                    if os.path.exists(create_user_sh_script):                                        
                                        create_user_sh_command = "/bin/bash %s -u %s" % (create_user_sh_script, user_schema)
                                        cmd = 'su - oracle -c "%s"' % create_user_sh_command                                                                       
                                        # try to delete all rows on tables
                                        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                                        out, err = proc.communicate()
                                        self.logger.info("out : %s" % out)
                                        self.logger.info("err : %s" % err)
                                        
                                        # move dmp_file_current_dir to dmpdir = '/home/oracle/dmpdir'
                                        dmp_file_location_new_path = os.path.join(dmpdir, os.path.basename(dmp_file_location))
                                        cmd1 = "mv %s %s" % (dmp_file_location, os.path.join(dmpdir, dmp_file_location_new_path))
                                        cmd2 = "chown oracle:dba %s" %  dmp_file_location_new_path
                                        
                                        self.logger.info("Moving : %s to %s" % (dmp_file_location, dmp_file_location_new_path))
                                        proc = subprocess.Popen(cmd1, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                                        out, err = proc.communicate()
                                        self.logger.info("out : %s" % out)
                                        self.logger.info("err : %s" % err)
                                        
                                        self.logger.info("Changing owner to oracle:dba for : %s" % dmp_file_location_new_path)
                                        proc = subprocess.Popen(cmd2, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                                        out, err = proc.communicate()
                                        self.logger.info("out : %s" % out)
                                        self.logger.info("err : %s" % err)
                                        
                                        # command = 'su - oracle -c "imp %s/lyd7ugp FILE=%s COMMIT=y IGNORE=y"' % (user_schema, dmp_file_location)
                                        command = 'su - oracle -c "impdp %s/lyd7ugp@%s DIRECTORY=dmpdir DUMPFILE=%s TABLES_EXISTS_ACTIION=REPLACE"' % (user_schema, ConfigParam.hostname, dmp_file_location)
                                        self.logger.info("Launch cmd : %s" % command)
                                        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                                        out, err = proc.communicate()
                                        self.logger.info("out : %s" % out)
                                        self.logger.info("err : %s" % err)
                                        sleep(1)
                                        
                                        if err == "":
                                            # purge dmp_file_location_new_path                                            
                                            cmd = "rm -f %s" % dmp_file_location_new_path
                                            self.logger.info("Launch cmd : %s" % cmd)
                                            proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                                            out, err = proc.communicate()
                                            self.logger.info("out : %s" % out)
                                            self.logger.info("err : %s" % err)
                                        
                                    else:
                                        self.logger.error("File Not Found !! : %s" % create_user_sh_script)
                                        self.logger.error("can't import content of tables: PARAMETRESAPPLICATION, MISSION, SCHEMA !! : %s" % create_user_sh_script)                                        

                        elif service == "services":
                            self.logger.info(result)
                            for serv, stat in result.iteritems():
                                if serv == "oracle":
                                    serv += "-xe"
                                if stat == "OK":
                                    self.logger.info("- Starting services '%s':" % serv)
                                    out, err = self.mange_service(serv, "start")
                                    if out != "":
                                        self.logger.error("INFO : %s" % out)
                                    if err != "":
                                        self.logger.error("ERR : %s " % err)
                                if stat == "KO":
                                    self.logger.info("- Stopping services '%s':" % serv)
                                    out, err = self.mange_service(serv, "stop")
                                    if out != "":
                                        self.logger.error("INFO : %s" % out)
                                    if err != "":
                                        self.logger.error("ERR : %s " % err)

def main():
    parser = argparse.ArgumentParser(description="Script usage description")
    parser.add_argument("--popname", action="store", dest="popname", nargs=1, help="POP NAME", required=True)
    parser.add_argument("--idsite", action="store", dest="idsite", type=int, nargs=1, help="SITE ID", required=True)
    parser.add_argument("--run", action="store", dest="run", nargs=1, help="Backup or Restore", required=True)
    parser.add_argument("--backup", action="store", dest="backup", nargs=1, help="BACKUP ZIP FILE", default=None)
    
    args = parser.parse_args()

    popname = args.popname[0].upper()
    idsite  = args.idsite[0]
    run     = args.run[0].lower()
    backup  = args.backup
            
    if len(popname) < 5:
        print("Invalid site name >= 5 characters")
        sys.exit(-1)

    if idsite <= 0:
        print("Invalid Site ID")
        sys.exit(-1)
    
    if run not in ['backup', 'restore']:
        print("Choose between [backup, restore]")
        sys.exit(-1)
    
    if backup is not None:
        if not os.path.exists(backup[0]):
            print("Backup File not Found! : %s" % backup[0])
            sys.exit(-1)
    
    if run == "restore":    
        # create logger file
        log_file_name = "restoredb.log"
        log_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), log_file_name)
    
        # file_handler = logging.FileHandler("backup_pop.log")
        handler = logging.handlers.RotatingFileHandler(log_file, mode='a', maxBytes=2000000, backupCount=2)
        formater = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formater)
        # handler.setLevel(logging.INFO)
        logger = logging.getLogger("restoredb")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
        now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        
        print("Log file generated on: %s" % log_file)
    
        logger.info("------------- Starting restoration: %s -------------" % now)
    
        restoredb = Restoredb(logger=logger, popname=popname, idsite=idsite)
        # print(r.get_list_backup_file())
        # r.download_last_backup()
        # r.extract_downloaded_file()
        if backup is not None:
            logger.info("Using compressed file : %s" % backup[0])
            restoredb.start_restoration(zip_file=backup[0])
        else:
            restoredb.start_restoration()    
        logger.info("----------------------------------------------------")
    
    elif run == "backup":
        # create logger file
        log_file_name = "backupdb.log"
        log_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), log_file_name)
    
        # file_handler = logging.FileHandler("backup_pop.log")
        handler = logging.handlers.RotatingFileHandler(log_file, mode='a', maxBytes=2000000, backupCount=2)
        formater = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formater)
        # handler.setLevel(logging.INFO)
        logger = logging.getLogger("backup_pop")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
        now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        
        print("Log file generated on : %s" % log_file)
        
        logger.info("------------- Starting backup: %s -------------" % now)
    
        backup = Backupdb(popname=popname, idsite=idsite, logger=logger)
    
        backup.start_backup()
        backup.upload_to_sftp_server()
        logger.info("backup end with success ...")
        logger.info("---------------------------------------------------------------")

    


if __name__ == '__main__':
    main()
    print("SUCCESS !!")