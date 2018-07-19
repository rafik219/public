# -*- coding: utf-8 -*-

#**************************
# author:    rbo
# version:   09/12/2017
# utility:   ditrib HTTP diag
# rbo:       06/07/2018 
#            updating : adding config file
#
# rbo:       12/07/2018
#            updating: add resize zip file
#
# rbo:       17/07/2018
#            adding S3 send file
#**************************

import boto
import bz2
import glob
import hashlib
import logging.handlers
import os
import sys
import time
import urllib3
import xml.dom.minidom
import zipfile
from boto.s3.key import Key
from datetime import datetime
from random import randint
from socket import gethostname
from threading import Thread


class BaseConfig:
    """ Class to load configuration from distribvai.xml file """
    VAI_DIR = os.path.join(os.getenv('IPLABEL'), "vai")
    CONFIG_DIR = os.path.join(os.getenv('IPLABEL'), "config")
    CONFIG_FILE = "distribvai.xml"
    CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, CONFIG_FILE)
    _instances = None
        
    def __new__(cls, *args, **kwargs):
        if not cls._instances:
            cls._instances = object.__new__(BaseConfig)
        return cls._instances
   
    def __init__(self):
        self.config = BaseConfig.load_config()      
                
    @staticmethod
    def load_config():
        config = {}        
        if not os.path.exists(BaseConfig.CONFIG_FILE_PATH):
            raise Exception("{0} File not found !!".format(BaseConfig.CONFIG_FILE_PATH))
        
        try:
            etree = xml.dom.minidom.parse(BaseConfig.CONFIG_FILE_PATH)
            # rebound configuration parameters
            config['to_rebound'] = etree.getElementsByTagName('rebound')[0].getAttribute('enable')
            config['login'] = etree.getElementsByTagName('credentials')[0].getAttribute('login')
            config['password'] = etree.getElementsByTagName('credentials')[0].getAttribute('password')
            config['server'] = etree.getElementsByTagName('server')[0].getAttribute('addr')
            config['port'] = etree.getElementsByTagName('server')[0].getAttribute('port')
            config['endpoint'] = etree.getElementsByTagName('endpoint')[0].getAttribute('filename')        
                
            # s3 configuration parameters
            config['to_s3'] = etree.getElementsByTagName('s3')[0].getAttribute('enable')
            config['aws_access_key'] = etree.getElementsByTagName('credentials')[1].getAttribute('aws_access_key')
            config['aws_secret_key'] = etree.getElementsByTagName('credentials')[1].getAttribute('aws_secret_key')            
            
            # diags configuration parameters
            config['directories'] = etree.getElementsByTagName('directories')[0].getAttribute('list')
            config['retention'] = etree.getElementsByTagName('retention')[0].getAttribute('days')
            config['transfermode'] = etree.getElementsByTagName('transfermode')[0].getAttribute('threshold')
            config['loglevel'] = etree.getElementsByTagName('logging')[0].getAttribute('level')                
            config['zip_max_size'] = etree.getElementsByTagName('resize_zip')[0].getAttribute('zip_max_size')
            config['zip_resizign'] = etree.getElementsByTagName('resize_zip')[0].getAttribute('enable')            
                   
        except Exception as ex:
            raise Exception("During parsing {0} configuration file, cause: {1}".format(BaseConfig.CONFIG_FILE_PATH, ex))
        
        return config


class ZipFileResizer:
    """ class to resize zip file if size is great then defined value """
    _instances = None
        
    def __new__(cls, *args, **kwargs):
        if not cls._instances:
            cls._instances = object.__new__(ZipFileResizer)
        return cls._instances
    
    def __init__(self):      
        self.logger = logging.getLogger(__name__)        
        self.do_resizing = BaseConfig().config.get('zip_resizign').strip().lower()
        self.zf_max_size = BaseConfig().config.get('zip_max_size').strip().lower()   
            
    def resize_zip_file(self, zip_file):            
            """ resize zip file if: size is great then zip_max_file and enable parameter is yes """                 
            if self.do_resizing == "yes":
                zf_size = os.path.getsize(zip_file)            
                # check zip_max_size parameter                
                if not self.zf_max_size.endswith('m') or not self.zf_max_size[:-1].isdigit():
                    self.logger.error("unknown value for 'zip_max_size' parameter on configuration file, example for correct value zip_max_size=\"2M\"")
                    raise Exception("Value error for zip_max_size parameter, got: {0}".format(self.zf_max_size))
                else:                
                    zf_max_size = int(self.zf_max_size[:-1]) * 1000000
                    # compare size                    
                    if zf_size > zf_max_size:                       
                        origin_zip_file = zipfile.ZipFile(zip_file, mode='r')
                        origin_zip_content = origin_zip_file.namelist()
                        origin_zip_uniq_content = set(map(lambda x: x.split('-')[0], origin_zip_content))                        

                        # check if there is optimization we create new zip file
                        if len(origin_zip_uniq_content) < len(origin_zip_content):
                            new_list_image = []
                            new_zip_filename = os.path.basename(zip_file).split('.')[0] + "_new.zip"
                            new_zip_filepath = os.path.join(os.path.dirname(zip_file), new_zip_filename)
                            
                            if os.path.exists(new_zip_filepath):
                                try:
                                    os.remove(new_zip_filepath)
                                except OSError as ex:
                                    self.logger.error("Can't remove {0} file, cause: {1}".format(new_zip_filepath, ex))
                            new_zip_file = zipfile.ZipFile(new_zip_filepath, mode='w', compression=zipfile.ZIP_DEFLATED)
                            
                            for uniq_image in sorted(list(origin_zip_uniq_content)):
                                for index, image in enumerate(origin_zip_content):
                                    if uniq_image == image.split('-')[0]:
                                        new_list_image.append(origin_zip_content[index])
                                        break
                        
                            # create new zip basing on new list images
                            for image in new_list_image:
                                buffer = origin_zip_file.read(image)
                                new_zip_file.writestr(image, buffer)                        
                            
                            # close zip files
                            new_zip_file.close()
                            origin_zip_file.close() 

                            # we delete old zip file and replace it with new zip file
                            try:                 
                                origin_file_size = os.path.getsize(zip_file) / 1000000
                                os.remove(zip_file)
                                new_file_size = os.path.getsize(new_zip_filepath) / 1000000
                                os.rename(new_zip_filepath, zip_file)
                                diff_size_percentage = 100 - ((new_file_size * 100) / origin_file_size)
                                self.logger.info("[ {0} ] Old file ({1} M) -> new file {2} ({3} M) (optimization: {4} %)".format("TH_ZIP", origin_file_size, new_zip_filepath, new_file_size, diff_size_percentage))
                            except OSError as ex:
                                self.logger.error("During deleting old file {0} or renaming {1}, cause: {3}".format(zip_file, new_zip_filepath, ex))
                                os.remove(new_zip_filepath)
                                self.logger.info("Delete file {0}".format(new_zip_filepath))
                            except:
                                self.logger.error("Unexpected error:", sys.exc_info()[0])
                                os.remove(new_zip_filepath)
                                self.logger.info("Delete file {0}".format(new_zip_filepath))
                        else:
                            self.logger.info("[ {0} ] File already optimized: {1}".format("TH_ZIP", zip_file))


class UploadMode:
    """ Class to select transfer mode, count and delete old files """    

    def __init__(self):
        self.logger = logging.getLogger(__name__)        
        self.vaidir = BaseConfig.VAI_DIR
        self.diagfiles_threshold = int(BaseConfig().config.get('transfermode'))     
         
    def count_diag_files(self):
        count = 0
        for root, dirs, files in os.walk(self.vaidir, topdown=True, onerror=None, followlinks=True):
            if len(files) != 0:
                for file in files:
                    try:
                        filename = os.path.join(root, file)
                        file_epoch = datetime.fromtimestamp(os.path.getmtime(filename))
                        diff_epoch = datetime.now() - file_epoch                       
                        if diff_epoch.days >= int(BaseConfig.load_config().get('retention')):                            
                            self.logger.info("Delete file {0}, age > {1} days !!".format(filename, diff_epoch.days))
                            try:
                                os.remove(filename)
                            except OSError as ex:            
                                self.logger.error("During deleting file: {0}, cause: {1}".format(filename, ex))
                    except Exception as ex:            
                        self.logger.error("During counting number of files on: {0}, cause: {1}".format(self.vaidir, ex))
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
    DIAGS_TO_S3 = BaseConfig().config.get('to_s3').strip().lower()
    DIAGS_TO_REBOUND = BaseConfig().config.get('to_rebound').strip().lower()
    AWS_ACCESS_KEY = BaseConfig().config.get('aws_access_key').strip()
    AWS_SECRET_KEY = BaseConfig().config.get('aws_secret_key').strip()   
    SERVER_FILENAME = BaseConfig().config.get('endpoint').strip()
    CONFIG = {"server"  : BaseConfig().config.get('server').strip(),
                        "port"    : BaseConfig().config.get('port').strip(),
                        "login"   : BaseConfig().config.get('login').strip(),
                        "password": BaseConfig().config.get('password').strip()}   
    
    def __init__(self, currdir, logger=None, mode=None):
        Thread.__init__(self)
        self.mode = mode          
        self.logger = logger or logging.getLogger(__name__)        
        self.threadname = "[ th_{0} ]".format(os.path.basename(currdir)).upper()
        self.currentdir = os.path.join(BaseConfig.VAI_DIR, currdir)
        
        self.logger.info("{0} Select current directory '{1}'".format(self.threadname, self.currentdir))        
                
        if Distribdiag.DIAGS_TO_S3 == "yes":            
            self.conn = boto.connect_s3(Distribdiag.AWS_ACCESS_KEY, Distribdiag.AWS_SECRET_KEY)
            self.vaibucket = self.conn.get_bucket('vai-znb')
            
        elif Distribdiag.DIAGS_TO_REBOUND == "yes":
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
        else:
            self.logger.error('Invalid parameter for S3 or Rebound transfer mode, put enable="yes" to activate ...')            
            raise
        
    def upload_diag_s3(self, fullfilename):      
        filename = os.path.basename(fullfilename)        
        file_date = filename.split('_')[1]
        file_date_year = file_date[0:4]
        file_date_month = file_date[4:6]
        file_date_day = file_date[6:8]
        file_date_hour = file_date[8:10]
        try:
            # get bucket key      
            bucket_key = Key(self.vaibucket)
            # create bucket if not exist
            bucket_year = self.vaibucket.new_key(file_date_year + "/")
            bucket_year.set_contents_from_string("")
            path_s3 = "{0}/{1}/{2}/{3}/".format(file_date_year, file_date_month, file_date_day, file_date_hour)
            file_path_s3 = os.path.join(path_s3, filename)
            bucket_key = self.vaibucket.new_key(file_path_s3)
            # upload file to bucket
            bucket_key.set_contents_from_filename(fullfilename)        
            # check MD5
            fdiag = open(fullfilename, 'rb')
            Md5_fdiag = hashlib.md5(fdiag.read()).hexdigest()
            fdiag.close()
            
            Md5_fdiag_s3 = bucket_key.etag.strip('"').strip("'")
            
            if Md5_fdiag == Md5_fdiag_s3:                            
                return (True, "OK : {0} File Transfered to S3".format(fullfilename))            
            else:            
                self.logger.error("During upload {0} to S3, cause: Md5 CheckSum different".format(fullfilename))
                bucket_key.delete()     
        except Exception as ex:
            self.logger.error("During uploading file {0} to S3, cause: {1} we will retry again ...".format(fullfilename, ex))
        
        return (False, "KO : {0} File not Transfered to S3".format(fullfilename))       
                
    def upload_diag(self, filename):
        
        with open(filename, 'rb') as diag:
            contentdiag = diag.read()
            md5diag = hashlib.md5(contentdiag).hexdigest()
            fields = {"upload": (os.path.basename(filename), contentdiag),
                      "md5": md5diag}

        statinfo = os.stat(filename)     
          
        try:
            time.sleep(1)  # fix Exception : ConnectionResetError 10054, An existing connection was forcibly closed by the remote host
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
            self.logger.info("{0} Compress file for {1}".format(self.threadname, filename))
            zfile = bz2.BZ2File(filename + ".bz2", "wb")
            zfile.write(open(filename, "rb").read())
            zfile.close()
            os.remove(filename)
        except OSError as ex:
            self.logger.error("{0} During Deleting old file for {1}, cause: {2}".format(self.threadname, filename, ex))
        except Exception as ex:
            self.logger.error("{0} During compressing file for {1}, cause: {2}".format(self.threadname, filename, ex))

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
                    elif os.path.basename(os.path.dirname(fullfilename)) == "zip":
                        # try to resizing file                
                        ZipFileResizer().resize_zip_file(fullfilename)
                    if Distribdiag.DIAGS_TO_S3 == "yes":
                        upload = self.upload_diag_s3(filetoupload)
                    elif Distribdiag.DIAGS_TO_REBOUND == "yes":
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