# -*- coding: utf-8 -*-

#**************************
# author:    rbo
# version:   09/12/2017
# utility:   ditrib HTTP diag
# rbo:       06/07/2018 
#            updating : adding config file
#**************************

from threading import Thread
from socket import gethostname
import logging.handlers
from datetime import datetime
from random import randint
import sys
import urllib3
import hashlib
import os
import bz2
import glob
import time
import xml.dom.minidom


class BaseConfig:
    """ Class to load configuration from distribhttp.xml file """
    VAI_DIR = os.path.join(os.getenv('IPLABEL'), "vai")
    CONFIG_DIR = os.path.join(os.getenv('IPLABEL'), "config")
    CONFIG_FILE = "distribhttp.xml"
    CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, CONFIG_FILE)
    _instances = None
        
    def __new__(cls, *args, **kwargs):
        if not cls._instances:
            cls._instances = object.__new__(BaseConfig)
        return cls._instances
   
    def __init__(self):
        self.config = BaseConfig.load_config()        
        print(self.config, id(self))
        
    @staticmethod
    def load_config():
        config = {}        
        if not os.path.exists(BaseConfig.CONFIG_FILE_PATH):
            raise Exception("{0} File not found !!".format(BaseConfig.CONFIG_FILE_PATH))
        
        etree = xml.dom.minidom.parse(BaseConfig.CONFIG_FILE_PATH)
        
        config['login']         = etree.getElementsByTagName('credentials')[0].getAttribute('login')
        config['password']      = etree.getElementsByTagName('credentials')[0].getAttribute('password')
        config['server']        = etree.getElementsByTagName('server')[0].getAttribute('addr')
        config['port']          = etree.getElementsByTagName('server')[0].getAttribute('port')
        config['endpoint']      = etree.getElementsByTagName('endpoint')[0].getAttribute('filename')
        config['directories']   = etree.getElementsByTagName('directories')[0].getAttribute('list')
        config['retention']     = etree.getElementsByTagName('retention')[0].getAttribute('days')
        config['transfermode']  = etree.getElementsByTagName('transfermode')[0].getAttribute('threshold')
        config['loglevel']      = etree.getElementsByTagName('logging')[0].getAttribute('level')
        
        return config
    

class UploadMode:
    """ Class to select transfer mode, count and delete old files """    
    def __init__(self):        
        self.vaidir = BaseConfig.VAI_DIR
        self.diagfiles_threshold = int(BaseConfig().config.get('transfermode'))
        self.logger = logging.getLogger(__name__)

    def count_diag_files(self):
        count = 0
        for root, dirs, files in os.walk(self.vaidir, topdown=True, onerror=None, followlinks=True):
            if len(files) != 0:
                for file in files:
                    filename = os.path.join(root, file)
                    file_epoch = datetime.fromtimestamp(os.path.getmtime(filename))
                    diff_epoch = datetime.now() - file_epoch
                    if diff_epoch.days >= int(BaseConfig.load_config().get('retention')):
                        try:
                            self.logger.info("Delete file {0}, age > {1} days !!".format(filename, diff_epoch.days))
                            os.remove(filename)
                        except OSError as ex:            
                            self.logger.error("During deleting file: {0}, cause: {1}".format(filename, ex))    
            count += len(files)
        return count

    def get_upload_mode(self):
        countdiagfiles = self.count_diag_files()
        if countdiagfiles < self.diagfiles_threshold:
            return (0, "sequential")
        else:
            return (1, 'parallel')


class Distribdiag(Thread):
    """ Class to send files over http """  
    DIAG_DIRS = map(lambda x: x.strip(), BaseConfig().config.get('directories').split(' '))
    CONFIG = {"server"  : BaseConfig().config.get('server'),
              "port"    : BaseConfig().config.get('port'),
              "login"   : BaseConfig().config.get('login'),
              "password": BaseConfig().config.get('password')}  
    SERVER_FILENAME = BaseConfig().config.get('endpoint')

    def __init__(self, currdir, logger=None, mode=None):
        Thread.__init__(self)
        self.logger = logger or logging.getLogger(__name__)
        self.mode = mode
        self.threadname = "[ th_{0} ]".format(os.path.basename(currdir)).upper()
        self.currentdir = os.path.join(BaseConfig.VAI_DIR, currdir)
        
        self.logger.info("{0} Select current directory '{1}'".format(self.threadname, self.currentdir))
        
        self.url = "{0}:{1}".format(Distribdiag.CONFIG.get('server'), Distribdiag.CONFIG.get('port'))        
        
        self.logger.info("{0} Start dedicated thread on {1}".format(self.threadname, self.currentdir))
        self.logger.info("{0} Opening connection to: {1}".format(self.threadname, self.url))
        
        self.conn = urllib3.connection_from_url(self.url)        
        self.post_url = "{0}/{1}".format(self.url, Distribdiag.SERVER_FILENAME)
        self.headers = urllib3.make_headers(basic_auth='%s:%s' % (Distribdiag.CONFIG.get('login'),
                                                             Distribdiag.CONFIG.get('password')),
                                                             keep_alive=True,
                                                             user_agent=gethostname())        
        # disable warning from InsecureRequestWarning
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.logger.info("{0} OK connection established to {1}".format(self.threadname, self.url))
        

    def upload_diag(self, filename):
        
        with open(filename, 'rb') as diag:
            contentdiag = diag.read()
            md5diag = hashlib.md5(contentdiag).hexdigest()
            fields = {"upload": (os.path.basename(filename), contentdiag),
                      "md5": md5diag}

        statinfo = os.stat(filename)     
          
        try:
            time.sleep(1) # fix Exception : ConnectionResetError 10054, An existing connection was forcibly closed by the remote host
            t0 = time.time()
            response = self.conn.request_encode_body('POST', self.post_url, fields, self.headers)
            t1 = time.time()
            if response.status == 200:
                if response.data.decode().lower().find('ok') >= 0:
                    return (True, "%.2f KB/s" % (int(statinfo.st_size) / (1000 * (t1 - t0))))                
            else:
                self.logger.error("{0} Server tell {1} code for POST request !!".format(self.threadname, response.status))   
            
            return (False, "HTTP %d | %s | %dKB" % (response.status, response.data.decode().lower(), int(statinfo.st_size / 1000)))            
                
        except Exception as ex:
            self.logger.error("{0} When uploading file !!, cause: {1}".format(self.threadname, str(ex)))
            self.logger.info("{0} We will retry to send file !!".format(self.threadname))
             
        return (False, "Can not transfer this file: {0} over http !!".format(filename))

    def zipvai(self, filename):
        try:
            self.logger.info("{0} Create ZIP file for {1}".format(self.threadname, filename))
            zfile = bz2.BZ2File(filename + ".bz2", "wb")
            zfile.write(open(filename, "rb").read())
            zfile.close()
            os.remove(filename)
        except OSError as ex:
            self.logger.error("{0} During Deleting old file for {1}, cause: {2}".format(self.threadname, filename, ex))
        except Exception as ex:
            self.logger.error("{0} During Create ZIP file for {1}, cause: {2}".format(self.threadname, filename, ex))
        
        

    def count_diag_files(self, d):
        count = 0
        for root, dirs, files in os.walk(d, topdown=True, onerror=None, followlinks=True):
            count += len(files)
        return count
    
    def prepare_upload_diag(self, currentdir):
        alldiagfiles = glob.glob(currentdir + "\\*.*")
        if len(alldiagfiles) > 0:
            self.logger.info("{0} Count files: {1} Files on {2}".format(self.threadname, len(alldiagfiles), currentdir))
            if os.path.basename(currentdir) in ('zip', 'hwl'):
                alldiagfiles.sort(key=os.path.getsize)
                alldiagfiles = list(reversed(alldiagfiles))
            else:
                alldiagfiles.sort(key=os.path.getmtime)
            for fullfilename in reversed(alldiagfiles):
                # remove old extension .integer
                if fullfilename.split('.')[-1].isdigit():
                    os.rename(fullfilename, ".".join(fullfilename.split(".")[:-1]))
                date = os.path.basename(fullfilename).split("_")[1]
                if (len(date) == 14) & date.isdigit():
                    filetoupload = fullfilename
                    if fullfilename.split('.')[-1] in ["pcap", "txt", "har", "dbg"]:
                        self.zipvai(fullfilename)
                        filetoupload += ".bz2"
                    upload = self.upload_diag(filetoupload)
                    if upload[0]:
                        self.logger.info("{0} Transfer OK: {1}, Status: {2}".format(self.threadname, filetoupload, upload))
                        try:
                            os.remove(filetoupload)
                        except OSError as ex:
                            self.logger.error("{0} During Deleting file {1}, cause: {2}".format(self.threadname, filetoupload, ex))
                    else:
                        self.logger.error("{0} Transfer KO: {1}, Status: {2}".format(self.threadname, filetoupload, upload))
        else:
            self.logger.info("{0} Nothing to do on {1}, cause: Empty directory".format(self.threadname, currentdir))
    
    
    def start_upload_diag(self, currentdir):       
        if os.path.exists(currentdir):
            if self.mode == "parallel":                
                while True:
                    self.prepare_upload_diag(currentdir)
                    # generate random wait
                    wait = randint(0, 10) + 20
                    self.logger.info("{0} Wait {1}s and scan directory {2} again ...".format(self.threadname, wait, currentdir))    
                    time.sleep(wait)
            elif self.mode == "sequential":
                self.prepare_upload_diag(currentdir)
        else:
            self.logger.info("{0} Nothing to do on {1}, cause: Path does not exist".format(self.threadname, currentdir))
            

    def run(self):
        if self.mode == "sequential":
            for direc in Distribdiag.DIAG_DIRS:
                self.currentdir = os.path.join(BaseConfig.VAI_DIR, direc)
                self.start_upload_diag(self.currentdir)
        elif self.mode == "parallel":
            self.start_upload_diag(self.currentdir)
    
    def __del__(self):
        self.logger.info("{0} Closing connection ...".format(self.threadname))
        self.conn.close()
    


def main():

    logfolder = os.path.join(os.getenv('iplabel'), "log")
    if not os.path.exists(logfolder):
        os.makedirs(logfolder) 
    
    logfilepath = os.path.join(logfolder, os.path.basename(sys.argv[0]).split('.')[0] + ".log")

    handler = logging.handlers.RotatingFileHandler(logfilepath, mode='a', maxBytes=20000000, backupCount=5)
    formater = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formater)

    logger = logging.getLogger(__name__)
    logger.addHandler(handler)
    level = BaseConfig().config.get('loglevel')
    if level.upper() == 'INFO':
        level = logging.INFO
    elif level.upper() == 'WARNING':
        level = logging.WARNING
    elif level.upper() == 'ERROR':
        level = logging.ERROR
    elif level.upper() == 'CRITICAL':
        level = logging.CRITICAL
    else:
        level = logging.DEBUG
    
    logger.setLevel(level)

    logger.info("-----------------------------------------------------")
    logger.info("Start execution at: {}".format(datetime.now().strftime("%Y/%m/%d %H:%M:%S")))
    logger.info("-----------------------------------------------------")

    # Select mode: Sequential or parallel
    uploadmode = UploadMode().get_upload_mode()

    if uploadmode[0] == 0:
        logger.info("Selecting Sequential transfer mode ...")
        distribdiag = Distribdiag(BaseConfig.VAI_DIR, logger=logger, mode=uploadmode[1])
        distribdiag.start()
        distribdiag.join()

    elif uploadmode[0] == 1:
        logger.info("Selecting Parallel transfer mode ...")
        list_thread = list()
        logger.info("Initialization ...")

        for diagdir in Distribdiag.DIAG_DIRS:
            distribdiag = Distribdiag(diagdir, logger=logger, mode=uploadmode[1])
            list_thread.append(distribdiag)
            distribdiag.start()
            time.sleep(1)

        for th in list_thread:
            th.join()

    logger.info("End execution at: {0}".format(datetime.now().strftime("%Y/%m/%d %H:%M:%S")))


if __name__ == "__main__":
    print("Starting ...")
    t0 = time.time()
    main()
    t1 = time.time()
    print("total time: ", (t1 - t0))
    print("success !! ")