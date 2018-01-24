#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

# rbo
# version: 02/08/217
#
# pip install paramiko
# pip install pycrypto
#

import getopt
import glob
import logging.handlers
import os
import shutil
import sys
import xml.dom.minidom
from datetime import datetime
from threading import Thread

import paramiko
from Crypto.Cipher import DES


def usage():
    print "--------------------------------------------"
    script_name = sys.argv[0]
    print "Usage : \n" \
          "\t {0} -e <pass>\n" \
          "\t {0} --encrypt_pwd <pass>\n" \
          "OU \n" \
          "\t {0} -d <pass>\n" \
          "\t {0} --decrypt <pass>\n" \
          "OU\n" \
          "\t {0} -a <run> \n" \
          "\t {0} --action <run>\n\n" \
          "- pass : Le password a chiffrer\n" \
          "- pass : Le password a dechiffrer\n" \
          "- run  : RUN pour demarrer le script\n" \
          "".format(script_name)
    print "--------------------------------------------"
    sys.exit(1)


def encrypt_pass(message):
    # static keys for encryption and decryption
    # KEYS = "\xad\xc5\xa8\x84%\xc1#@".encode('hex')
    KEYS = "IP-LABEL"
    if len(message) < 8:
        new_msg = message.ljust(8)
    elif len(message) in range(8, 16):
        new_msg = message.ljust(16)
    elif len(message) in range(16, 32):
        new_msg = message.ljust(32)
    else:
        new_msg = message
    return ((DES.new(KEYS, DES.MODE_ECB)).encrypt(new_msg)).encode('hex')


def decrypt_pass(message):
    # static keys for encryption and decryption
    # KEYS = "\xad\xc5\xa8\x84%\xc1#@".encode('hex')
    KEYS = "IP-LABEL"
    try:
        dec = ((DES.new(KEYS, DES.MODE_ECB)).decrypt(message.decode('hex'))).strip()
    except Exception as ex:
        print " * Error: impossible de dechiffrer cette chaine, cause: %s " % str(ex)
        sys.exit(-1)
    return dec


class FwConfig():
    def __init__(self):
        self.xmlpath = os.path.join(os.path.dirname(__file__), "firewallConfig.xml")
        self.list_firewall = list()

    def get_fw_config(self):
        # Parse All xml file and return list of information
        index = 0
        dict_firewall_info = dict()
        if not os.path.exists(self.xmlpath):
            print "\t => %s : fichier introuvable !!" % self.xmlpath
            sys.exit(-2)
        with open(self.xmlpath, "rt") as f:
            try:
                etree = xml.dom.minidom.parse(f)
            except Exception as ex:
                print "\t => Erreur lors de lecture du fichier firewallConfig.xml, cause: %s" % str(ex)
        while index < len(etree.getElementsByTagName('firewall')):
            dict_firewall_info["firewall"] = index
            dict_firewall_info["name"] = etree.getElementsByTagName('firewall')[index].getAttribute('name')
            dict_firewall_info["modele"] = etree.getElementsByTagName('type')[index].getAttribute('modele')
            dict_firewall_info["login"] = etree.getElementsByTagName('connection')[index].getAttribute('login')
            dict_firewall_info["password"] = etree.getElementsByTagName('connection')[index].getAttribute('password')
            dict_firewall_info["ip"] = etree.getElementsByTagName('address')[index].getAttribute('ip')
            dict_firewall_info["port_ssh"] = etree.getElementsByTagName('address')[index].getAttribute('port_ssh')
            self.list_firewall.append(dict_firewall_info)  # add dict_firewall_info to list
            dict_firewall_info = dict()  # reset dict_firewall_info
            index += 1
        return self.list_firewall


class SSHConnect(Thread):
    def __init__(self, firewall):
        Thread.__init__(self)
        self.ftp_server = "x.x.x.x"
        self.ftp_user = "fwuser"
        self.ftp_password = "xxxxxxxx"
        self.backup_type = "backup"  # for simple config backup
        # self.backup_type = "full-backup" # for full config backup
        self.fw_ip = firewall.get('ip')
        self.fw_name = firewall.get('name')
        self.fw_port_ssh = firewall.get('port_ssh')
        self.fw_login = firewall.get('login')
        self.fw_password = firewall.get('password')
        self.fw_model = firewall.get('modele')
        self.fw_num = firewall.get('firewall')

    def run(self):
        ssh = paramiko.SSHClient()  # init SSHClient
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # auto add ssh keys.

        date = datetime.now().strftime("%Y%m%d")

        logger.info(
            "[%s] [Step 0] : Select Firewall num: %s with name: %s" % (self.fw_name, (self.fw_num + 1), self.fw_name))
        logger.info("[%s] [Step 1] : Start SSH connection to %s:%s" % (self.fw_name, self.fw_ip, self.fw_port_ssh))
        try:
            ssh.connect(hostname=self.fw_ip, port=int(self.fw_port_ssh), username=self.fw_login,
                        password=decrypt_pass(self.fw_password), timeout=60)
        except Exception as ex:
            logger.error("%s\t => Error when establishing ssh connection, cause: %s" % (self.fw_name, str(ex)))

        config_file_name = self.fw_name + "_" + date + ".conf"

        command = "execute %s config ftp Backup_All_Fw_Config/%s %s %s %s" % (
            self.backup_type, config_file_name, self.ftp_server, self.ftp_user, self.ftp_password)

        # transport = ssh.get_transport()
        # transport.set_keepalive(60)

        logger.info("[%s] [Step 2] : Start execute command : %s" % (self.fw_name, command))
        try:
            stdin, stdout, stderr = ssh.exec_command(command)
            # wait channel to receive exit status == 0 (wait executing command)
            stdout.channel.recv_exit_status()
            # print stdin
            # print stderr
        except Exception as ex:
            logger.error("[%s] \t => Error when executing ssh command, cause: %s" % (self.fw_name, str(ex)))

        config_file_path = os.path.join("/home/fwuser/Backup_All_Fw_Config/", config_file_name)
        if os.path.exists(config_file_path):
            logger.info("[%s] [Step 3] : File : %s Found!" % (self.fw_name, config_file_path))
            logger.info("[%s] [Step 4] : Backup OK" % self.fw_name)
        else:
            logger.error("[%s]\t * File : %s Not Found!" % (self.fw_name, config_file_path))
            logger.error("[%s]\t * Backup KO" % self.fw_name)

        # close ssh connection
        logger.info("[%s] [Step 5] : Close SSH connection from %s" % (self.fw_name, self.fw_name))
        ssh.close()
        logger.info("[%s] [Step 6] : SSH connection closed!" % self.fw_name)


if __name__ == "__main__":

    argv = sys.argv[1:]
    opts = ""

    if len(argv) < 2:
        if len(argv) != 0:
            if sys.argv[1:][0] not in ('-v', '--version'):
                usage()
        else:
            usage()
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'a:e:d:h:v', ["help", "encrypt=", "decrypt=", "action="])
    except getopt.GetoptError as ex:
        usage()

    for opt, arg in opts:
        if opt == '-h':
            usage()
        elif opt in ('-v', '--version'):
            print "version: 1.0"
            sys.exit(0)
        elif opt in ('-e', '--encrypt'):
            print "\t * Password : %s => Encryption : %s" % (arg, encrypt_pass(arg))
            sys.exit(0)
        elif opt in ('-d', '--decrypt'):
            print "\t * Encryption : %s => Password : %s" % (arg, decrypt_pass(arg))
            sys.exit(0)
        elif opt in ('-a', '--action'):
            action = arg.lower()
            if action != 'run':
                print "use 'run' to start run the script"
                sys.exit(-3)
        else:
            usage()

    fw_source_dir = "/home/fwuser/Backup_All_Fw_Config"
    backupConfig_old = os.path.join(fw_source_dir, "BackupConfig_old")
    log_file_name = "getFwConfiguration_%s.log" % datetime.now().strftime("%Y%m%d")
    log_file_path = os.path.join(fw_source_dir, log_file_name)

    paramiko_log = os.path.join(fw_source_dir, "paramiko.log")
    paramiko.util.log_to_file(paramiko_log)

    if os.path.exists(log_file_path):
        os.remove(log_file_path)
    handler = logging.FileHandler(log_file_path)
    handler = logging.handlers.RotatingFileHandler(log_file_path, mode='a', maxBytes=2000000, backupCount=2)
    formater = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formater)
    # handler.setLevel(logging.INFO)
    logger = logging.getLogger("Firewall")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    logger.info("*****************************************")
    logger.info("* Start Execution at: %s" % datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
    logger.info("*****************************************")

    fw_cfg = FwConfig()

    list_fw = fw_cfg.get_fw_config()

    logger.info("Nombre de FireWall : %s" % len(list_fw))
    if len(list_fw) == 0:
        logger.info("\t\t => Error when getting information from firewallConfig.xml")
        sys.exit(-2)
    else:
        # print backupConfig_old
        if not os.path.exists(backupConfig_old):
            try:
                os.mkdir(backupConfig_old)
            except Exception as ex:
                logger.error("Error when creating %s directory, cause: %s" % (backupConfig_old, str(ex)))
                sys.exit(-1)

        logger.info("Removing old configuration files :")
        # for file in glob.glob(backupConfig_old + "/*.conf"):
        # print file
        # if len(os.listdir(backupConfig_old)) != 0:
        for file_bc in glob.glob(backupConfig_old + "/*.conf"):
            sub_file_bc = os.path.basename(file_bc).split('_')[1]
            for file_fs in glob.glob(fw_source_dir + "/*.conf"):
                sub_file_fs = os.path.basename(file_fs).split('_')[1]
                if sub_file_bc == sub_file_fs:
                    try:
                        os.remove(file_bc)
                        logger.info("* * file: %s -> removed from backupConfig_old directory" % file_bc)
                    except Exception as ex:
                        logger.error("=> Error when deleting %s file, cause: %s" % (file_bc, str(ex)))

        logger.info("* Backup configuration files :")
        for file in glob.glob(fw_source_dir + "/*.conf"):
            # print file
            try:
                shutil.move(file, backupConfig_old)
                logger.info("* * file: %s -> moved to backupConfig_old directory" % file)
            except Exception as ex:
                logger.error("=> Error when moving % file, cause: %s" % (file, str(ex)))

    # starting get firewall configuration
    list_thread = list()
    logger.info("Starting connection on Firewalls : ")
    for firewall in list_fw:
        fw = SSHConnect(firewall)
        list_thread.append(fw)
        fw.start()

    for th in list_thread:
        th.join()
    logger.info("End getting backup file configuration")
    # log files management:
    date_now = int(datetime.now().strftime("%Y%m%d"))
    for logfile in glob.glob(fw_source_dir + "/*.log"):
        date_mtime_logfile = int(datetime.fromtimestamp(os.path.getmtime(logfile)).strftime("%Y%m%d"))
        if date_now - date_mtime_logfile > 30:
            try:
                os.remove(logfile)
                logger.info("* LogFile: %s are removed, age > 30 days" % logfile)
            except Exception as ex:
                logger.error("=> Error when deleting %s file, cause: %s" % (logfile, str(ex)))

    logger.info("Success !!")
    logger.info("*****************************************")
    logger.info("* End Execution at: %s" % datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
    logger.info("*****************************************")

    sys.exit(2)
