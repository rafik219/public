#!/bin/env python2.7
# -*- coding: utf8


import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
import argparse
from datetime import datetime, timedelta
import json
import os
import sqlite3
import sys
from re import compile, match
import logging
import logging.handlers
import requests.packages.urllib3



class BaseConfig:

    CONFIG_FILE_NAME = "config.json"
    CONFIG_FILE_PATH = os.path.join(os.path.join(os.path.dirname(os.path.realpath(__file__)), "conf"), CONFIG_FILE_NAME)
    JENKINS_STDERR = 1 
    
    def __init__(self, **propreties):        
        for property_name, property_value in propreties.items():
            setattr(self, property_name, property_value)
    
    @classmethod
    def get_configuration(cls, property_name):
        properties = json.load(open(BaseConfig.CONFIG_FILE_PATH))        
        return properties.get(property_name)
       
    @staticmethod
    def current_alarm_url(monitor_id):
        return "https://{0}/latest/REST/{1}/?monitor_id={2}".format(BaseConfig.get_configuration('ws_server'),
                                                                    BaseConfig.get_configuration('ws_methode_name'), monitor_id) 



class CustomAlarm:    
    def __init__(self, login, password, monitor_id, logger=None):
        self._login = login
        self._password = password
        self.monitor_id = monitor_id
        self.logger = logger
        self.archiver = os.path.join(os.path.dirname(os.path.realpath(__file__)), BaseConfig.get_configuration('archive_file_name')) 
        # disable https warnings
        requests.packages.urllib3.disable_warnings()    
        
    def get_url_alarm_for_monitor(self):
        return BaseConfig.current_alarm_url(self.monitor_id)
    
    def get_current_alarm_for_monitor(self):
        alarm_content, found, archivage = {}, False, False
        try:
            req = requests.get(self.get_url_alarm_for_monitor(), auth=requests.auth.HTTPBasicAuth(self._login, self._password))
            if req.status_code == 200:
                response = req.json()      
                for key, value in response.get('Ipln_WS_REST_datametrie').iteritems():
                    if key == u"Get_Current_Alarms_Per_Monitor":
                        if value.get('status') == u"success":
                            if value.get('response') != "":
                                for elt in value.get('response'):
                                    if elt.get('MONITOR_ID') == self.monitor_id:
                                        if elt.get('ALARM_TYPE') == "BLACK":
                                            # check if alarm end
                                            if elt.get('ALARM_END_DATE') == "":
                                                self.logger.info("Success: (+) Black Alarm was detected for this monitor: {0}.".format(self.monitor_id))                                            
                                                alarm_content, found, archivage = value, True, False
                                            else:
                                                self.logger.info("Success: (-) End Black Alarm was detected for this monitor: {0}.".format(self.monitor_id))                                            
                                                alarm_content, found, archivage = value, True, True
                                        else:
                                            self.logger.info("{} Alarm detected for this monitor: {0}".format(elt.get('ALARM_TYPE'), self.monitor_id))                                                                                                                                  
                                    else:                                        
                                        self.logger.error("Wrong Alarm detected, given monitor_id = {0} & result monitor_id = {1}".format(self.monitor_id, elt.get('MONITOR_ID')))
                                        self.logger.error("No Alarm detected for this monitor: {0}".format(elt.get('MONITOR_ID')))
                                        sys.exit(BaseConfig.JENKINS_STDERR)                                                                                
                            else:
                                self.logger.info("No Alarm detected for this monitor: {}".format(self.monitor_id))   
                                alarm_content, found, archivage = value, False, True                                                        
                        else:
                            self.logger.error("{0}() method return: {1} for this monitor: {2}".format(BaseConfig.get_configuration('ws_methode_name'), value.get('status'), self.monitor_id))
                            sys.exit(BaseConfig.JENKINS_STDERR)                            
                    elif key == '':
                        self.logger.error("During making web service request: {0}".format(self.get_url_alarm_for_monitor()))
                        sys.exit(BaseConfig.JENKINS_STDERR)                        
            else:
                self.logger.error("Server respond with: {0} for this request: {1}".format(req.status_code, self.get_url_alarm_for_monitor()))
                sys.exit(BaseConfig.JENKINS_STDERR)                
                
        except Exception, ex:
            self.logger.error("During making web service requests, cause : {0}".format(ex))
            sys.exit(BaseConfig.JENKINS_STDERR)
        
        return alarm_content, found, archivage       

    def sendMail(self, from_sender=None, send_to=None, mail_subject=None, mail_content=None, cc_to=None, smtp_login=None, smtp_password=None, tls=False):          
        try:
            msg = MIMEMultipart()
            msg['From'] = from_sender
            msg['To'] = send_to
            msg['Date'] = formatdate(localtime=True)
            msg['Subject'] = mail_subject        
            if cc_to is not None:         
                msg['Cc'] = cc_to
                to_addrs = msg['To'].split(',') + msg['Cc'].split(',')
            else:
                to_addrs = msg['To'].split(',')       
                    
            msg.attach(MIMEText(mail_content))
            
            smtp = smtplib.SMTP(BaseConfig.get_configuration('smtp_server'), BaseConfig.get_configuration('smtp_port'))
                    
            if tls:
                smtp.starttls()
            if smtp_login is not None and smtp_password is not None:
                smtp.login(smtp_login, smtp.password)
            
            smtp.sendmail(from_sender, to_addrs, msg.as_string())        
            smtp.quit()
            self.logger.info("Success: email was send to : {0}".format(to_addrs))
        except Exception as ex:
            self.logger.error("Success: email was send to : {0}".format(to_addrs))
            sys.exit(BaseConfig.JENKINS_STDERR)

 
 
class ArchiveAlarm:
    def __init__(self, client_id, logger=None):
        self.__conn = None
        self.__cur = None
        self.client_id = client_id
        self.logger = logger
        self.custom_table_name = "alarms_{0}".format(self.client_id)
        self.archive_path = os.path.join(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'db'), BaseConfig.get_configuration('archive_file_name'))        
        self.__create_table(self.custom_table_name)
        
     
    def __open(self):
        try:
            self.__conn = sqlite3.connect(self.archive_path)
            self.__cur = self.__conn.cursor()
            
        except sqlite3.Error as ex:
            self.logger.error("Database connection error, cause: {}".format(ex))
            sys.exit(BaseConfig.JENKINS_STDERR)
        
        
    def __close(self):
        self.__cur.close()
        self.__conn.close()
    
        
    def __create_table(self, table_name):        
        try:
            self.__open()
            with self.__conn:
                self.__cur.execute("""CREATE TABLE IF NOT EXISTS {0}
                                     (  MONITORID        INTEGER,
                                        CLIENTID         INTEGER,
                                        ARCHIVED         NUMERIC,
                                        DATEALARM        DATE,
                                        DATEENDALARM     DATE,
                                        ALARMCONTENT     TEXT )""".format(table_name))
                self.logger.info("Table name : {0} created or already exist !!".format(table_name))
        except Exception as ex:
            self.logger.error("During create table {0}, cause: {1}".format(self.custom_table_name, ex))
            sys.exit(BaseConfig.JENKINS_STDERR)
        finally:
            self.__close()
        
    def archive(self, monitor_id, alarm_description, archived=0):
        try:
            self.__open()
            with self.__conn:
                self.__cur.execute("""INSERT INTO {0} VALUES(:MONITORID, :CLIENTID, :ARCHIDED, :DATEALARM, :DATEENDALARM, :ALARMCONTENT)""".format(self.custom_table_name),
                                    {'MONITORID' : monitor_id,
                                     'CLIENTID' : self.client_id, 
                                     'ARCHIDED' : archived,
                                     'DATEALARM' : datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                                     'DATEENDALARM' : None,
                                     'ALARMCONTENT' : json.dumps(alarm_description)})
                self.logger.info("Success: New Alarm inserted for this monitor id : {0}".format(monitor_id))
        except Exception as ex:
            self.logger.error("During archive alarm, cause: {0}".format(ex))
            sys.exit(BaseConfig.JENKINS_STDERR)
        finally:
            self.__close()
    
    
    def update_archive(self, monitor_id, alarm_content=None):
        status = False
        try:
            self.__open()
            with self.__conn:
                if alarm_content is None:
                    self.__cur.execute("""UPDATE {0} SET ARCHIVED = :ARCHIVED, DATEENDALARM = :DATEENDALARM, DATEENDALARM = :DATEENDALARM WHERE MONITORID = :MONITORID AND DATEENDALARM is NULL"""
                                        .format(self.custom_table_name), {'ARCHIVED' : 1,
                                                                          'MONITORID' : monitor_id,
                                                                          'DATEENDALARM': datetime.now().strftime("%d/%m/%Y %H:%M:%S")})
                else:
                    self.__cur.execute("""UPDATE {0} SET ARCHIVED = :ARCHIVED, DATEENDALARM = :DATEENDALARM, ALARMCONTENT = :ALARMCONTENT WHERE MONITORID = :MONITORID AND DATEENDALARM is NULL"""
                                        .format(self.custom_table_name), {'ARCHIVED' : 1,
                                                                          'DATEENDALARM': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                                                                          'ALARMCONTENT' : json.dumps(alarm_content, indent=4),
                                                                          'MONITORID' : monitor_id})                
                status = True
                self.logger.info("Success: Update request for this monitor id : {0}".format(monitor_id))
        except Exception as ex:
            self.logger.error("During updating archived status for this monitor id: {0}, cause: {1}".format(monitor_id, ex))
            sys.exit(BaseConfig.JENKINS_STDERR)
        finally:
            self.__close()
        return status
    
    def check_none_archived_alarm(self, monitor_id):
        found = False
        result = None
        try:
            self.__open()
            with self.__conn:
                self.__cur.execute("""SELECT * FROM {0} WHERE ARCHIVED = 0 AND MONITORID = :MONITORID AND DATEENDALARM is :DATEENDALARM """
                                        .format(self.custom_table_name), {'MONITORID' : monitor_id,
                                                                           'DATEENDALARM' : None})
                result = self.__cur.fetchall()                        
                if len(result) > 0:
                    found = True
                    self.logger.info("Success: None archived alarm was found for this monitor id: {0}".format(monitor_id))
                else:
                    self.logger.info("None archived alarm was not found for this monitor id: {0}".format(monitor_id))
        except Exception as ex:
            self.logger.error("During finding none archived alarm, cause: {0}".format(ex))
            sys.exit(BaseConfig.JENKINS_STDERR)
        finally:
            self.__close()        
        return found, result  
    
    
    def display(self):
        self.__open()
        result = None
        try:
            with self.__conn:
                self.__cur.execute("""SELECT * FROM {0}""".format(self.custom_table_name))
                result = self.__cur.fetchall()
        except Exception as ex:
            self.logger.error("During executing SELECT request, cause: {0}".format(ex))
        self.__close()
        return result
    
    def purge_db(self, retention=15):
        purge_date = datime.today() - timedelta(days=retention)
        purge_date = purge_date.strftime('%d/%m/%Y')        
        try:
            self.__open()
            with self.__conn:
                self.__cur.execute("""DELETE FROM {0} WHERE DATEALARM < :PURGE_DATE""".format(self.custom_table_name), {'PURGE_DATE' : purge_date})
                self.logger.info("Success: Purge table, retention is {0} days.".format(retention))
        except Exception as ex:
            self.logger.error('During purging table: {0}, cause: {1}'.format(self.custom_table_name, ex))
        finally:
            self.__close()
            
                
def main():
    parser = argparse.ArgumentParser(description="This is the description")
    parser.add_argument("--idclient", action="store", dest="idclient", type=int, nargs=1, help="Client ID", required=True)
    parser.add_argument("--login", action="store", dest="login", nargs=1, help="WS login for client account", required=True)
    parser.add_argument("--password", action="store", dest="password", nargs=1, help="WS password for client account", required=True)
    parser.add_argument("--idmonitor", action="store", dest="idmonitor", type=int, nargs=1, help="Monitor ID", required=True)
    parser.add_argument("--customemail", action="store", dest="custom_email", type=argparse.FileType('r'), nargs=1,
                        help="Email configuration file", required=True)
    parser.add_argument("--cc", action="store", dest="copy_email", nargs="*", help="List of copy email (cc)")
    parser.add_argument("--version", action="version", version="v0.1")
    
    args = parser.parse_args()
    
    if args.idclient is None or args.login is None or args.password is None or args.idmonitor is None or args.custom_email is None:
        print("Usage: python %s -h" % sys.argv[0])
        sys.exit(0)
        
    if not os.path.exists(BaseConfig.CONFIG_FILE_PATH):
        print("ERROR: Configuration file not Found : {0}".format(BaseConfig.CONFIG_FILE_PATH))
        sys.exit(0)
        
    if not os.path.exists(args.custom_email[0].name):
        print("ERROR: Configuration file not Found : {0}".format(args.custom_email[0].name))
        sys.exit(0)
       
    idclient = args.idclient[0]
    _login = args.login[0]
    _password = args.password[0]
    idmonitor = args.idmonitor[0]
    custom_email_info = json.load(open(args.custom_email[0].name))
    
    if custom_email_info.get('cc') != "" or custom_email_info.get('cc') is not None:
        list_args_email = ['from', 'to', 'cc']
    else:
        list_args_email = ['from', 'to']
        
    # check formating email address 
    for emails in list_args_email:
        if custom_email_info.get(emails) is not None:
            for mail in custom_email_info.get(emails).split(','):
                regex = compile(r"^[a-z0-9._-]+@[a-z0-9._-]+\.[a-z]+")
                if regex.match(mail) is None:
                    print("ERROR: Invalid email address: %s !!" % mail)
                    sys.exit(-2)
    
    log_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "log")
    log_file_name = "customalarm_{0}.log".format(idclient) 
    log_file_path = os.path.join(log_path, log_file_name)
    
    
    logformater = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    logger = logging.getLogger("customalarm")
    logger.setLevel(logging.INFO)
    
    fileHandler = logging.FileHandler(log_file_path)
    fileHandler = logging.handlers.RotatingFileHandler(log_file_path, mode='a', maxBytes=2000000, backupCount=2)
    fileHandler.setFormatter(logformater)
    logger.addHandler(fileHandler)
    
    consoleHander = logging.StreamHandler()
    consoleHander.setFormatter(logformater)
    logger.addHandler(consoleHander)
          
    customalarm = CustomAlarm(_login, _password, idmonitor, logger=logger)      

    logger.info("-----------  Start at : {0}  --------------".format(datetime.now().strftime("%Y/%m/%d %H:%M:%S")))
    logger.info("Sending GET request : {0}".format(BaseConfig.current_alarm_url(idmonitor)))
    
    alarm_content, found_alarm, archivage = customalarm.get_current_alarm_for_monitor()
    archiver = ArchiveAlarm(idclient, logger=logger)

    if found_alarm:
        logger.info("Check if we have, storing alarm ...")
        found_none_archived_alarm, result = archiver.check_none_archived_alarm(idmonitor)
        if not found_none_archived_alarm:
            if not archivage:
                # New alarm
                logger.info("Insertion alarm ...")
                archiver.archive(idmonitor, alarm_content)
                logger.info("We send email now ...")
                customalarm.sendMail(from_sender=custom_email_info.get('from'),
                                        send_to=custom_email_info.get('to'),
                                        mail_subject=custom_email_info.get('mail_subject'),
                                        mail_content=custom_email_info.get('mail_content'),
                                        cc_to=custom_email_info.get('cc')) 
            else:
                # same alarm
                logger.info("End Black Alarm, Just Update Alarms !!")
                archiver.update_archive(idmonitor, alarm_content=alarm_content)
        else:
            logger.info("Alarm already exist on database !!")
            if archivage:
                # End Alarm
                logger.info("Need to Update Alarms !!")
                archiver.update_archive(idmonitor, alarm_content=alarm_content)
            else:
                logger.info("Not need to archiving !!")
        # purge table
        archiver.purge_db()
        
    else:
        found_none_archived_alarm, result = archiver.check_none_archived_alarm(idmonitor)
        if found_none_archived_alarm:
            if archivage:
                logger.info("Archiving last none archived alarm for this monitor: {0}".format(idmonitor))
                archiver.update_archive(idmonitor)
            else:
                pass
        else:
            logger.info("Not need to make any update !! ")
  
    logger.info("-----------  end at : {0}  --------------".format(datetime.now().strftime("%Y/%m/%d %H:%M:%S")))
    
    
if __name__ == "__main__":
    main()
    print("success !!")
