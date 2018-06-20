#!/usr/bin/env python2.7
# -*- coding: utf-8

# @uthor: rbo
# class utulity: request DTM Oracle database
# version: 30/05/2018
#

import cx_Oracle
from config.InitConfig import *


class Oracle:
    def __init__(self, mode="readonly"):
        if mode == "readonly":                
            self.oracle_config = InitConfig.get_config_by_section_name(file_name="oracle.ini", section="oracle_readonly")
        elif mode == "admin":
            self.oracle_config = InitConfig.get_config_by_section_name(file_name="oracle.ini", section="oracle_admin")
        self.connection = None
        self.cursor = None        
    
        
    def _connect(self):
        isconnet = False
        try:
            dsn_tns = cx_Oracle.makedsn(self.oracle_config.get('server'), self.oracle_config.get('port'), self.oracle_config.get('servicename'))            
            dsn_tns = dsn_tns.replace('SID=', 'SERVICE_NAME=')            
            self.connection = cx_Oracle.connect(user=self.oracle_config.get('user'), password=self.oracle_config.get('password'), dsn=dsn_tns)
            self.cursor = self.connection.cursor()
            isconnet = True            
        except Exception, ex:
            isconnet = False
            print("Error: during connection, cause : %s" % str(ex))
            self._close()            
        return isconnet
    
    
    def _close(self):        
        if self.cursor is not None:
            try:
                self.cursor.close()
            except Exception, ex:
                print("Error: during closing cursor, cause: %s" % ex)
        if self.connection is not None:
            try:
                self.connection.close()
            except Exception, ex:
                print("Error: during closing connection, cause: %s" % ex)
    
    
    def execute_select_query(self, request):
        res = None
        try:            
            self.cursor.execute(request)            
            res = self.cursor.fetchall()             
        except Exception, ex:                        
            raise Exception('Error: during executing Query, cause: %s' % ex)        
        return res