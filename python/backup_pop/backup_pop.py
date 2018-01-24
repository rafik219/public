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

import paramiko
import yaml


def copy_file(filepath, dest):
    copied_status = False
    if os.path.exists(filepath):
        try:
            shutil.copy2(filepath, dest)
            copied_status = True
        except Exception, ex:
            print "Error: Can't copy file: %s to %s, cause: %s" % (filepath, dest, ex)
    return copied_status


def main():
    # try to get linux os distribution
    lsb_release = ""
    try:
        import platform
        lsb_release = platform.linux_distribution()[1][0]
    except Exception, ex:
        print "unable to get OS distribution, cause: %s" % ex

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

    # Listing backup files
    list_backup_file = {
        "network": {
            "/etc/resolv.conf",
            "/etc/hosts",
            "/etc/sysconfig/network",
            "/etc/sysconfig/network-scripts/ifcfg-eth0"
        },
        "oracle": {
            tnsnames,
            listner
        },
        "dist": {
            "/home/dist/DBconfig.conf",
            "/home/dist/dist.conf",
            "/home/dist/mo.conf",
            "/home/dist/site.conf"
        },
        "dns": {
            "/etc/named.caching-nameserver.conf"
        },
        "nagios": {
            "/etc/nagios/nrpe.cfg"
        },
        "filesystem": {
            "/etc/fstab"
        },
        "applinux": {
            "/home/dist/tools/appLinux_config.yml",
            "/etc/inittab"
        }
    }

    dbconfig = "/home/dist/DBconfig.conf"
    schema = None
    dbpassword = "lyd7ugp"
    alias_idsite = None
    idsite = None
    tmp_backup_table_dir = "/tmp"
    copy_status_dict = dict()
    backup_dir = "/root/backup_bdd_config/backup_files"
    yaml_file_name = "backup_config_status.yml"
    yaml_file = os.path.join(backup_dir, yaml_file_name)

    sftp_server = "0.0.0.0"
    sftp_port = 22
    sftp_login = "backupdb"
    sftp_passwd = "xxxxxxxxxxx"
    retry = 0
    # create logger file
    log_file_name = "backup_pop.log"
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

    logger.info("------------- Starting backup: %s -------------" % now)

    # Create backup directory.
    # or
    # purge it if already exist
    if not os.path.exists(backup_dir):
        try:
            os.makedirs(backup_dir)
            logger.info("backup directory : %s created." % backup_dir)
        except OSError, ex:
            logger.error("Can't create %s directory, cause: %s" % (backup_dir, ex))
            sys.exit(-1)
    else:
        logger.info("backup dir : %s already exist, deleting content" % backup_dir)
        for root, dirs, files in os.walk(backup_dir):
            for d in dirs:
                try:
                    os.rmdir(os.path.join(root, d))
                    logger.info("directory : %s -> deleted" % d)
                except OSError, ex:
                    logger.error("Can't remove %s directory, cause: %s" % (d, ex))
            for f in files:
                try:
                    os.remove(os.path.join(root, f))
                    logger.info("file : %s -> deleted" % f)
                except OSError, ex:
                    logger.error("Can't remove %s file, cause: %s" % (f, ex))

    # get schema, site and alias (from backup_dir)
    # and
    # backup database tables.
    if os.path.exists(dbconfig):
        logger.info("reading %s ..." % dbconfig)
        with open(dbconfig, "r") as fconf:
            for line in fconf.readlines():
                if line != "\n":
                    idsite = line.strip().split(":")[0]
                    alias_idsite = line.strip().split(":")[1]
                    schema = line.strip().split(":")[2]
                    logger.info("idsite: %s, alias: %s, schema: %s" % (idsite, alias_idsite, schema))

                    db_connection = "%s/%s" % (schema, dbpassword)
                    backup_table_file_name = "%s/%s_%s_%s_TABLES_%s.dmp" % (
                        tmp_backup_table_dir, alias_idsite, idsite, schema, now.split(' ')[0].replace('/', ''))
                    list_backup_table = "PARAMETRESAPPLICATION,SCHEMA"
                    log_backup_file_name = "backup_BDD_%s_%s.log" % (idsite, schema)

                    sub_cmd = "exp %s FILE=%s TABLES=%s LOG=%s" % (
                        db_connection, backup_table_file_name, list_backup_table, log_backup_file_name)
                    command = "su - oracle -c '{}'".format(sub_cmd)
                    try:
                        subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE).communicate()
                        logger.info("table backup generated with success on: %s" % backup_table_file_name)
                    except Exception, ex:
                        logger.error(
                            "Can't export Tables: {} from XE database, cause: {}".format(list_backup_table, ex))
    else:
        logger.error("%s file not found" % dbconfig)
        sys.exit(-3)

    # copy list_backup_files
    # and
    # format dictionary with status after copying
    for sub_dict in list_backup_file.keys():
        copy_file_status = list()
        for file_config in list_backup_file[sub_dict]:
            tmp_copy_file_status1 = dict()
            tmp_copy_file_status1["path"] = file_config
            if copy_file(file_config, backup_dir):
                tmp_copy_file_status1["status"] = "OK"
            else:
                tmp_copy_file_status1["status"] = "KO"

            copy_file_status.append(tmp_copy_file_status1)
            copy_status_dict[sub_dict] = copy_file_status

    # move dmp_file to backup_dir
    # and
    # add backup table status in copy_status_dict
    backup_tables_status = list()
    for dmp_file in glob.glob(tmp_backup_table_dir + "/*.dmp"):
        status = "KO"
        if dmp_file.endswith("TABLES_" + now.split(' ')[0].replace('/', '') + ".dmp"):
            try:
                shutil.move(dmp_file, backup_dir)
                logger.info("moving file : %s -> %s" % (dmp_file, backup_dir))
                status = "OK"
            except OSError, ex:
                logger.error("Can't move %s -> %s directory, cause: %s" % (dmp_file, backup_dir, ex))

            backup_tables_status.append({"path": dmp_file, "status": status})

    # print backup_tables_status
    copy_status_dict["backupdb"] = backup_tables_status

    # get service status.
    list_service = ["oracle", "httpd", "nfs", "named", "ipldist"]
    dict_service_status = dict()
    logger.info("check status of services:")
    for service in list_service:
        if service == 'oracle':
            cmd = "ps -ef | grep -v grep | grep -c pmon"
            out, err = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).communicate()
            if out != "" and int(out) > 0:
                logger.info("+ service '%s' is running" % service)
                dict_service_status[service] = "OK"
            else:
                logger.error("unknown service status for '%s' service, my be service is not started" % service)
                dict_service_status[service] = "KO"
        else:
            cmd = "service %s status" % service
            out, err = subprocess.Popen(cmd.split(" "), stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
            if out != "" and (out.strip().lower().find('running') != -1 or out.strip().lower().find('en cours') != -1):
                logger.info("+ service '%s' is running" % service)
                dict_service_status[service] = "OK"
            else:
                logger.error("unknown service status for '%s' service, my be service is not started" % service)
                dict_service_status[service] = "KO"

    # add to copy_status_dict
    copy_status_dict["services"] = dict_service_status

    # create yml file using result dictionary
    with open(yaml_file, "w") as file_dumper:
        logger.info("dumping result on YAML file: %s" % yaml_file)
        try:
            yaml.dump(copy_status_dict, file_dumper)
            # yaml.dump(copy_status_dict, file_dumper, default_flow_style=False)
            logger.info("dump end with success !!")
        except Exception, ex:
            logger.error("when dumping result on: %s file, cause: %s" % (yaml_file, ex))
            sys.exit(-2)

    # compress all backup files on backup_dir
    # and
    # create zip file
    compress_file_name = "%s_%s_BACKUP_%s" % (alias_idsite, idsite, now.split(' ')[0].replace('/', ''))
    compress_file = os.path.join(os.path.dirname(os.path.abspath(backup_dir)), compress_file_name)
    archive_file_path = ""

    # supported_format = shutil.get_archive_formats()
    supported_format = [('zip', 'zip'), ('gztar', 'tar.gz'), ('bztar', 'tar.bz2')]

    for compress_format in supported_format:
        try:
            shutil.make_archive(compress_file, compress_format[0], backup_dir, logger=logger)
            archive_file_path = "%s.%s" % (compress_file, compress_format[1])
            logger.info("compressing end with success : %s" % archive_file_path)
            break
        except Exception, ex:
            logger.error("'%s' archive format not supported, cause: %s" % (compress_format[0], ex))
            logger.info("supported format: %s" % supported_format)
            logger.info("try with '%s' format" % compress_format[0])
            continue

    # purge backup directory after compression
    if os.path.exists(archive_file_path) and os.path.getsize(archive_file_path) > 0:
        try:
            shutil.rmtree(backup_dir)
            logger.info("Purge local backup directory: %s" % backup_dir)
        except shutil.Error, ex:
            logger.error("Can't delete %s directory, cause: %s" % (backup_dir, ex))

    # upload compressed file to the repository.
    while retry < 5:
        transport = paramiko.Transport((sftp_server, sftp_port))
        transport.connect(username=sftp_login, password=sftp_passwd)

        sftp = paramiko.SFTPClient.from_transport(transport)

        new_dir = "%s_%s" % (alias_idsite, idsite)

        try:
            if new_dir not in sftp.listdir():
                sftp.mkdir(new_dir)
                logger.info("directory : '%s' created on sftp server : '%s'" % (new_dir, sftp_server))
            else:
                # delete old backup files, and keep at least 3 backup
                logger.info("try to purge old backup files on the server")
                for backup_file in sftp.listdir(new_dir):
                    generation_date = backup_file.split(".")[0].split("_")[3]
                    if int(now.split(' ')[0].replace('/', '')) - int(generation_date) >= 3:
                        try:
                            sftp.remove(os.path.join(new_dir, backup_file))
                            logger.info("old backup '%s' -> deleted from the server" % backup_file)
                        except Exception, ex:
                            logger.error("unable to deleted %s backup on server, cause: %s" % (backup_file, ex))
        except Exception, ex:
            logger.error("when trying to list directory on sftp server, cause: %s" % ex)
            sys.exit(-4)

        sftp_archive_path = "%s/%s" % (new_dir, os.path.basename(archive_file_path))

        try:
            # Put file on the sftp server
            sftp.put(archive_file_path, sftp_archive_path)
            logger.info("archive transferred with success !")
        except Exception, ex:
            logger.error("when sending archive to the server, cause: %s" % ex)
            retry += 1
            sftp.close()
            sleep(3)
            continue

        try:
            logger.info("try to comparing size between file transferred and local file")
            # comparing size between local archive and remote archive
            local_archive_size = os.stat(archive_file_path).st_size
            remote_archive_size = sftp.stat(sftp_archive_path).st_size

            # we tolerate 5 bytes between them
            if abs(local_archive_size - remote_archive_size) not in range(0, 5):
                logger.error("transfer not properly completed, retry sending archive !!")
                retry += 1
                sleep(3)
                continue
            else:
                logger.info("we transferred the same size, difference : %s bytes" % abs(
                    local_archive_size - remote_archive_size))
                sftp.close()
                try:
                    # delete local archive file after transfer
                    os.remove(archive_file_path)
                    logger.info("deleting local archive file : %s" % archive_file_path)
                except OSError, ex:
                    logger.error("we can't delete local archive file : %s , cause: %s " % (local_archive_size, ex))
                break
        except Exception, ex:
            logger.error("we can't comparing archive size, cause: %s" % ex)
            sys.exit(-5)

    logger.info("backup end with success ...")
    logger.info("---------------------------------------------------------------")


if __name__ == '__main__':
    main()
