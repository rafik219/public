# -*- coding: utf-8 -*-

#**************************
# author:    rbo
# version:   09/12/2017
# utility:   ditrib HTTP diag
#
#**************************

from threading import Thread
from socket import gethostname
import logging.handlers
from datetime import datetime
import sys
import urllib3
import hashlib
import os
import bz2
import glob
import time


class UploadMode:

    def __init__(self):
        self.vaidir = Distribdiag.vaidir
        self.diagfiles_threshold = 500

    def countdiagfiles(self):
        count = 0
        for root, dirs, files in os.walk(self.vaidir, topdown=True, onerror=None, followlinks=True):
            count += len(files)
        return count

    def getuploadmode(self):
        countdiagfiles = self.countdiagfiles()
        if countdiagfiles < self.diagfiles_threshold:
            return (0, "sequential")
        else:
            return (1, 'parallel')


class Distribdiag(Thread):

    vaidir = os.getenv('IPLABEL') + "\\vai"
    diagdirs = ["jpg", "hwl", "zip", "avi", "pcap", "txt", "har", "dbg"]
    config = {"server": "up-asia.colx.ip-label.net",
                   "login": "AAAAAAAAAA",
                   "password": "XXXXXXXXX"
                   }
    serverfilename = "upload_diag.php"

    def __init__(self, currdir, logger=None, mode=None):
        Thread.__init__(self)
        self.logger = logger
        self.mode = mode
        self.threadname = "[ th_{} ]".format(os.path.basename(currdir)).upper()
        self.currentdir = os.path.join(Distribdiag.vaidir, currdir)
        self.logger.info("{} Select current directory '{}'".format(
            self.threadname, self.currentdir))

        self.url = "https://{}".format(Distribdiag.config.get('server'))
        self.logger.info("{} Start dedicated thread on {}".format(self.threadname, self.currentdir))
        self.logger.info("{} Opening connection to: {}".format(self.threadname, self.url))

        self.conn = urllib3.connection_from_url(self.url)

        # disable warning from InsecureRequestWarning
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.logger.info("{} OK connection established to {}".format(
            self.threadname, self.url))

    def uploaddiag(self, filename):
        post_url = "{}/{}".format(self.url, Distribdiag.serverfilename)
        headers = urllib3.make_headers(basic_auth='%s:%s' % (Distribdiag.config.get('login'),
                                                             Distribdiag.config.get('password')),
                                                             keep_alive=True,
                                                             user_agent=gethostname())
        with open(filename, 'rb') as diag:
            contentdiag = diag.read()
            md5diag = hashlib.md5(contentdiag).hexdigest()
            fields = {"upload": (os.path.basename(filename), contentdiag),
                      "md5": md5diag}

        statinfo = os.stat(filename)     
          
        try:
            t0 = time.time()
            response = self.conn.request_encode_body('POST', post_url, fields, headers)
            t1 = time.time()
            if response.status == 200:
                if response.data.decode().lower().find('ok') >= 0:
                    return (True, "%.2f KB/s" % (int(statinfo.st_size) / (1000 * (t1 - t0))))
            else:
                self.logger.error("{} Server tell {} code for POST request !!".format(self.threadname, response.status))   
            
            return (False, "HTTP %d | %s | %dKB" % (response.status, response.data.decode().lower(), int(statinfo.st_size / 1000)))            
                
        except Exception as ex:
            self.logger.error("{} When uploading file !!, cause: {}".format(self.threadname, str(ex)))
            self.logger.info("{} We will retry to send file !!".format(self.threadname))
             
        return (False, "Can not transfer http file !!")

    def zipvai(self, filename):
        self.logger.info("{} Create ZIP file for {}".format(self.threadname, filename))
        zfile = bz2.BZ2File(filename + ".bz2", "wb")
        zfile.write(open(filename, "rb").read())
        zfile.close()
        os.remove(filename)

    def countdiagfiles(self, d):
        count = 0
        for root, dirs, files in os.walk(d, topdown=True, onerror=None, followlinks=True):
            count += len(files)
        return count

    def startuplaoddiag(self, currentdir):
        if os.path.exists(currentdir):
            alldiagfiles = glob.glob(currentdir + "\\*.*")
            if len(alldiagfiles) > 0:
                self.logger.info("{} Count files: {} Files on {}".format(self.threadname, len(alldiagfiles), currentdir))
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
                        upload = self.uploaddiag(filetoupload)
                        if upload[0]:
                            self.logger.info("{} Transfer OK: {}, Status: {}".format(self.threadname, filetoupload, upload))
                            os.remove(filetoupload)
                        else:
                            self.logger.error("{} Transfer KO: {}, Status: {}".format(self.threadname, filetoupload, upload))
            else:
                self.logger.info("{} Nothing to do on {}, cause: Empty directory".format(self.threadname, currentdir))
        else:
            self.logger.info("{} Nothing to do on {}, cause: Path does not exist".format(self.threadname, currentdir))

    def run(self):
        if self.mode == "sequential":
            for direc in Distribdiag.diagdirs:
                self.currentdir = os.path.join(Distribdiag.vaidir, direc)
                self.startuplaoddiag(self.currentdir)
        elif self.mode == "parallel":
            self.startuplaoddiag(self.currentdir)


def main():

    logfolder = os.path.join(os.getenv('iplabel'), "log")
    if not os.path.exists(logfolder):
        os.makedirs(logfolder) 
    
    logfilepath = os.path.join(logfolder, os.path.basename(sys.argv[0]).split('.')[0] + ".log")

    handler = logging.handlers.RotatingFileHandler(logfilepath, mode='a', maxBytes=2000000, backupCount=2)
    formater = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formater)

    logger = logging.getLogger("Distribdiag")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    logger.info("-----------------------------------------------------")
    logger.info("Start execution at: {}".format(
        datetime.now().strftime("%Y/%m/%d %H:%M:%S")))
    logger.info("-----------------------------------------------------")

    # Select mode: Sequential or parallel
    uploadmode = UploadMode().getuploadmode()

    if uploadmode[0] == 0:
        logger.info("Selecting Sequential transfer mode ...")
        distribdiag = Distribdiag(Distribdiag.vaidir, logger=logger, mode=uploadmode[1])
        distribdiag.start()
        distribdiag.join()

    elif uploadmode[0] == 1:
        logger.info("Selecting Parallel transfer mode ...")
        list_thread = list()
        logger.info("Initialization ...")

        for diagdir in Distribdiag.diagdirs:
            distribdiag = Distribdiag(diagdir, logger=logger, mode=uploadmode[1])
            list_thread.append(distribdiag)
            distribdiag.start()

        for th in list_thread:
            th.join()

    logger.info("End execution at: {}".format(datetime.now().strftime("%Y/%m/%d %H:%M:%S")))


if __name__ == "__main__":
    print("Starting ...")
    t0 = time.time()
    main()
    t1 = time.time()
    print("total time: ", (t1 - t0))
    print("success !! ")
