#!/usr/bin/env python2.7
# -*- coding: utf-8

#
# @uthor: rbo
# class utulity: update Prob HostName on dtm script 
# version: 30/05/2018
#          25/26/2018 add logging

import sys
import zipfile
import xml.dom.minidom

from oracle.Oracle import *
import base64
import os
import chardet
import shutil
import re

from datetime import datetime
import codecs
import cx_Oracle
from time import sleep
import argparse

import logging
import logging.handlers



def usage():
    print("""usage: %s [-h] [--idcontrat CONTRAT [CONTRAT ...] | --idclient IDCLIENT [IDCLIENT ...]] --run {yes,no}
                
                Script Usage:

                optional arguments:
                    -h, --help                            show this help message and exit
                    --idcontrat CONTRAT [CONTRAT ...]       List of Contrat ID or All
                    --idclient IDCLIENT [IDCLIENT ...]    Client ID
                    --run {yes,no}                        Yes: to run,
                                                          No: to display enabled contrat""" % sys.argv[0])  
    sys.exit(0)
    
    

class ExtractXmlContrat(object):
    """ class to extract and filter active contrat without hostname on run.py script"""
    
    ADD_IMPORT_SYSTEM_LINE = "import System"
    FIND_HOSTNAME_LINE = "System.Environment.GetEnvironmentVariable("
    ADD_HOSTNAME_LINE = "scen.addMessage('Probe: ' + System.Environment.GetEnvironmentVariable('computername'))"
    TMP_DIR = "/opt/iplabel/tmp"
        
    def __init__(self, idclient=None, idcontrat=None, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.__oracle = Oracle()
        self.xml_contrat = []     
        self.current_dir = os.path.dirname(os.path.realpath(__file__))           
        self.idclient=idclient
        self.idcontrat = idcontrat
        self.get_xml_active_contrat()

    
    def get_xml_active_contrat(self):
        if self.idclient is not None:
            _request = r""" SELECT c.idclient, p.idcontrat, p.parametresapplication
                            FROM parametreapplication p
                            INNER JOIN contrat c ON c.idcontrat = p.idcontrat AND c.etatcontrat = 4 AND c.idclient = %s
                            LEFT JOIN descriptioncontrat d ON p.IDCONTRAT = d.IDCONTRAT AND d.TYPEATTRIBUTCONTRAT = 282 AND d.VALEURATTRIBUT = 1
                            WHERE p.TYPEAPPLICATION = 41 AND d.idcontrat IS NULL
                            ORDER BY c.IDCLIENT""" % self.idclient
        elif self.idcontrat is not None:  
            if isinstance(self.idcontrat, list):
                _request = r""" SELECT c.idclient, p.idcontrat, p.parametresapplication
                                FROM parametreapplication p
                                INNER JOIN contrat c ON c.idcontrat = p.idcontrat AND c.etatcontrat = 4 and c.idcontrat in (%s)
                                LEFT JOIN descriptioncontrat d ON p.IDCONTRAT = d.IDCONTRAT AND d.TYPEATTRIBUTCONTRAT = 282 AND d.VALEURATTRIBUT = 1
                                WHERE p.TYPEAPPLICATION = 41 AND d.idcontrat IS NULL
                                ORDER BY c.IDCLIENT""" % (", ".join(self.idcontrat))
            elif isinstance(self.idcontrat, str):          
                if self.idcontrat == "all":            
                    _request = r""" SELECT c.idclient, p.idcontrat, p.parametresapplication
                                    FROM parametreapplication p
                                    INNER JOIN contrat c ON c.idcontrat = p.idcontrat AND c.etatcontrat = 4 --and c.idclient = 18837
                                    LEFT JOIN descriptioncontrat d ON p.IDCONTRAT = d.IDCONTRAT AND d.TYPEATTRIBUTCONTRAT = 282 AND d.VALEURATTRIBUT = 1
                                    WHERE p.TYPEAPPLICATION = 41 AND d.idcontrat IS NULL 
                                    ORDER BY c.IDCLIENT"""        
        self.logger.info('Connect to Oracle database')
        self.__oracle._connect()
        self.xml_contrat = self.__oracle.execute_select_query(_request)
        # !!! self.__oracle._close() # we need to close after processing
        
    
    def extract_filtered_tzip_contrat(self, directory=None):
        
        tzip_without_hostname = []
        path = ""
        if directory is not None:
            path = os.path.join(ExtractXmlContrat.TMP_DIR, directory)
            if not os.path.exists(path):
                os.makedirs(path)
                self.logger.info("Directory created : %s" % path)
            else:
                self.logger.info("Path already exist : %s" % path)
        else:
            path = ExtractXmlContrat.TMP_DIR
        
        i = 0
                       
        for idclient, idcontrat, xml_content in self.xml_contrat:
            i += 1
            tzip_without_hostname_info = {}
            
            self.logger.info("[%s] ------- Select Contrat: %s, idclient: %s ---------" % (i, idcontrat, idclient))  
            
            try:
                current_xml = xml_content.read()
                tzip = xml.dom.minidom.parseString(current_xml).getElementsByTagName("transaction").item(0).getAttribute("tzip")
                decode_zip_file = base64.decodestring(tzip)
                
                tmp_filename = "%s_%s.zip" % (idclient, idcontrat)
                tmp_file_path = os.path.join(path, tmp_filename)
                
                self.logger.info("Extracting zip file: %s" % tmp_file_path)
                with open(tmp_file_path, 'wb') as tmp_file:
                    tmp_file.write(decode_zip_file)
                    
                if os.path.exists(tmp_file_path):
                    zip_file = zipfile.ZipFile(tmp_file_path, mode='r')
                    
                    if 'run.py' in zip_file.namelist():
                        self.logger.info("Reading 'run.py' from %s" % tmp_file_path)
                        runpy = zip_file.read('run.py')
                        runpy_encoding = chardet.detect(runpy).get('encoding')
                        runpy_utf8 = runpy.decode(runpy_encoding).encode('UTF-8')
                        
                        self.logger.info("Check existing Hostname on run.py")
                        if runpy_utf8.find(ExtractXmlContrat.ADD_HOSTNAME_LINE) == -1 and runpy_utf8.find(ExtractXmlContrat.FIND_HOSTNAME_LINE) == -1:
                            self.logger.info('(+) Hostname code not found on run.py, we need update it on : %s' % tmp_file_path)
                            tzip_without_hostname_info['idclient'] = idclient
                            tzip_without_hostname_info['idcontrat'] = idcontrat
                            tzip_without_hostname_info['xml'] = current_xml
                            tzip_without_hostname_info['tzip'] = tzip
                            tzip_without_hostname_info['zip_file_path'] = tmp_file_path
                            tzip_without_hostname.append(tzip_without_hostname_info)
                        else:
                            self.logger.info("(-) Hostname already exist, we delete zip file: %s" % tmp_file_path)
                            zip_file.close()
                            try:
                                os.remove(tmp_file_path)                                
                            except OSError, ex:
                                self.logger.error("Error: During removing tmp file, cause: %s" % ex)
                    else:
                        self.logger.error("File 'run.py' not found on %s" % tmp_file_path)
                    zip_file.close()
                else:
                    self.logger.error('Error: during extraction, %s not found' % tmp_file_path)
                    
            except Exception, ex:                
                self.logger.error("Error: during processing extaract ! idcontrat: %s idclient: %s, cause: %s" % (idcontrat, idclient, ex))
        
        if path != ExtractXmlContrat.TMP_DIR:
            if len(os.listdir(path)) == 0:
                try:
                    os.removedirs(path)
                    self.logger.info("Deleting Emepty directory: %s" % path)
                except OSError, ex:
                    self.logger.error("Error: During deleting directory: %s, cause: %s" % (path, ex))
                
        return tzip_without_hostname

    
    def update_runpy(self, zips, purge_tmp_file=False):
                
        updated_zip_list = []        
        
        for zip in zips:
            updated_zip_temp = {}
            self.logger.info("Update 'run.py' on Contrat: %s, Client: %s" % (zip.get('idcontrat'), zip.get('idclient')))
            zf_origin = zipfile.ZipFile(zip.get('zip_file_path'), mode='r')            
            runpy_extract_path = zf_origin.extract('run.py', os.path.join(ExtractXmlContrat.TMP_DIR, 'tmp'))            
            encoding = chardet.detect(open(runpy_extract_path).read()).get('encoding')          
            
            with codecs.open(runpy_extract_path, 'rb', encoding=encoding) as file_origin:
                runpy_list = file_origin.readlines()
                                    
            runpy_list_strip = [line.strip() for line in runpy_list]
                        
            index = 0
            i = 0
            added_line = 0
            
            try:
                found = False                      
                #if ExtractXmlContrat.ADD_IMPORT_SYSTEM_LINE not in set(runpy_list_strip):
                for line in filter(lambda x: x.startswith('import'), runpy_list_strip):
                    if ExtractXmlContrat.ADD_IMPORT_SYSTEM_LINE in line:
                        found = True
                        break
                if not found:
                    index = runpy_list_strip.index("from iplabel import *")  

                    runpy_list.insert(index + 1, "# Auto insertion: %s\n" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    runpy_list.insert(index + 2, (ExtractXmlContrat.ADD_IMPORT_SYSTEM_LINE + "\n"))
                    added_line = 2
                                   
            except ValueError, ex:
                self.logger.info("Error: during insertion on run.py, mission: %s, cause: %s" %(zip.get('idcontrat'), ex))
            
            while i < len(runpy_list_strip[index:]):
                line = runpy_list_strip[index:][i].encode('UTF-8')
                if re.match(r'^(scen.startStep\()', line) is not None:                    
                # if  re.match(r'^(scen.start\(\))', runpy_list_strip[i]) is not None: 
                    try:
                        space_add = (runpy_list[i + index + added_line]).index('scen.startStep')                        
                        insert_line_auto = (runpy_list[i + index + added_line])[:space_add] +  "# Auto insertion: %s\n" % datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        insert_line_hostname = (runpy_list[i + index + added_line])[:space_add] + ExtractXmlContrat.ADD_HOSTNAME_LINE + "\n"                               
                        runpy_list.insert(i + index + 1 + added_line, insert_line_auto)
                        runpy_list.insert(i + index + 2 + added_line, insert_line_hostname)
                        break
                    except ValueError, ex:
                        self.logger.error("Error : During search 'scen.startStep' on idcontrat : %s for idclient : %s, cause: %s" %(zip.get('idcontrat'), zip.get('idclient'), ex))
                        break
                i += 1
                        
            with codecs.open(os.path.join(os.path.dirname(runpy_extract_path), "run_new.py"), "wb", encoding=encoding) as file_new:
                file_new.writelines(runpy_list)            
            # print(chardet.detect(open(os.path.join(os.path.dirname(runpy_extract_path), "run.py")).read()))
            # print(chardet.detect(open(os.path.join(os.path.dirname(runpy_extract_path), "run_new.py")).read()))            
            try:                
                new_zf_filename = os.path.basename(zip.get('zip_file_path')).split('.')[0] + "_new.zip"  
                new_zf_path = os.path.join(os.path.dirname(zip.get('zip_file_path')), new_zf_filename)
                zf_new = zipfile.ZipFile(new_zf_path, mode='w', compression=zipfile.ZIP_DEFLATED)
                
                for item in zf_origin.infolist():
                    buffer = zf_origin.read(item.filename)
                    #if not item.filename.endswith('.py'):
                    if item.filename != 'run.py':
                        zf_new.writestr(item, buffer)                                                        
                # add new run_new_py to new zip file
                zf_new.write(os.path.join(os.path.dirname(runpy_extract_path), "run_new.py"), arcname="run.py")
                zf_origin.close()
                zf_new.close()
                updated_zip_temp['idcontrat'] = zip.get('idcontrat')
                updated_zip_temp['idclient'] = zip.get('idclient')
                updated_zip_temp['zip_file_path'] = new_zf_path
                updated_zip_list.append(updated_zip_temp)
                
                self.logger.info("-> Success: run.py updated ! %s" % zip.get('idcontrat'))
                
            except Exception, ex:
                self.logger.error("-> Error: during creating new zip file, cause: %s" % ex)
            
            # delete temporary files
            try:
                shutil.rmtree(os.path.join(ExtractXmlContrat.TMP_DIR, 'tmp'))
                if purge_tmp_file:
                    os.remove(zip.get('zip_file_path'))
            except:
                self.logger.error("-> Error: during purging temporary files, cause: %s" % ex)
                
        return updated_zip_list


    def display(self):
        if len(self.xml_contrat) != 0:
            for contrat in self.xml_contrat:
                self.logger.info("idClient : %s -> idContrat: %s" % (contrat[0], contrat[1]))
        else:
            if self.idclient:
                self.logger.info("No enabled contrat found for this idclient : %s" % self.idclient)
            elif self.idcontrat:
                self.logger.info("No enabled contrat found for this idcontrat : %s" % self.idcontrat)

    
    def close(self):
        self.logger.info("Close connection from Oracle database")  
        self.__oracle._close() 
     


class RegenerateXmlContrat(object):
    """class to regenerate Xml contrat with new run.py script"""
        
    CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
    TMP_DIR = "/opt/iplabel/tmp"
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
      
    
    def regenerate_xml_file(self, new_zips, zips, purge_tmp_file=False):
        regenerated_xml = []        
        for nzip in new_zips:
            nzip_idmission = nzip.get('idcontrat')
            try:
                new_tzip = base64.encodestring(open(nzip.get('zip_file_path'), 'rb').read())
                # update zips            
                select_zip = filter(lambda zp: zp.get('idcontrat') == nzip_idmission, zips)
                
                if len(select_zip) > 0:
                    xml_content = select_zip[0].get('xml')
                    tzip = 'tzip="%s"' % new_tzip
                    regex = r'tzip=\"(.+?)\"'
                    # replace tzip on xml file
                    new_xml_content = re.sub(regex, tzip.replace("\n", ""), select_zip[0].get('xml'))
                    
                    select_zip[0].update({'tzip' : new_tzip.replace("\n", ""),
                                           'xml' : new_xml_content})                            
                    
                    regenerated_xml.append(select_zip[0])                                      
                    
                    # purge zip file
                    if purge_tmp_file:
                        try:
                            os.remove(nzip.get('zip_file_path'))
                        except OSError, ex:
                            self.logger.error("Error: during deleting : %s, cause: %s" % (nzip.get('zip_file_path'), ex))
                    
            except Exception, ex:
                self.logger.error("Error: during regenerating xml file for this mission: %s, cause: %s" %(nzip_idmission, ex))
        
        return regenerated_xml

    
    def create_w20m_file(self, regenerated_xml,  directory=None):
        xmlFiles = []
        if len(regenerated_xml) > 0:
            if directory is not None:
                directory = os.path.join(RegenerateXmlContrat.TMP_DIR, directory)
                if not os.path.exists(directory):
                    os.makedirs(directory)
                    self.logger.info("Directory created : %s" % directory)
                else:
                    self.logger.info("Path already exist : %s" % directory)
            else:
                directory = RegenerateXmlContrat.TMP_DIR         
            
            self.logger.info("Create .w20m files:")
            
            for elt in regenerated_xml:
                filename = "%s_%s.w20m" % (elt.get('idclient'), elt.get('idcontrat'))  
                file_path = os.path.join(directory, filename)         
                with open(file_path, "w") as f:
                    f.write(elt.get('xml'))
                    self.logger.info("-> file created: %s !!" % filename)
                    xmlFiles.append(file_path)               
        return xmlFiles



class UpdateXmlContrat(object):
    """class to update new Xml on Oracle database, with restarting contrat """
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.__oracle = Oracle(mode="admin")
        self.__oracle._connect()
        # self.__oracle._close()
    
    def update_xml(self, new_zips):                
        for nzip in new_zips:
            xml_content_clob = nzip.get('xml')
            new_xml_clob = self.__oracle.cursor.var(cx_Oracle.CLOB)
            new_xml_clob.setvalue(0, xml_content_clob)
            
            idcontrat = nzip.get("idcontrat")
            idcontrat_var = self.__oracle.cursor.var(cx_Oracle.NUMBER)
            idcontrat_var.setvalue(0, idcontrat)
            
            # update PARAMETRERAPPLICATION
            self.__oracle.cursor.execute(""" UPDATE SITECENTRAL.PARAMETREAPPLICATION 
                                            SET PARAMETRESAPPLICATION = :parametreapp 
                                            WHERE IDCONTRAT = :idcontrat 
                                            AND TYPEAPPLICATION = 41""", parametreapp = new_xml_clob
                                                                       , idcontrat = idcontrat_var  )
            self.__oracle.connection.commit()
            self.logger.info("Success : Update idcontrat %s !!" % idcontrat) 
        
        # self.__oracle._close()
    
    def restart_contrat(self, idcontrat, idlogin, timeout=1):
        self.__suspend_contrat(idcontrat, idlogin)
        sleep(timeout)
        self.__resume_contrat(idcontrat, idlogin)
    
    def close(self):
        self.__oracle._close()
    
    
    def __suspend_contrat(self, idcontrat, idlogin):  
        idcontrat_var = self.__oracle.cursor.var(cx_Oracle.NUMBER)
        idcontrat_var.setvalue(0, idcontrat)
        idlogin_var = self.__oracle.cursor.var(cx_Oracle.STRING)
        idlogin_var.setvalue(0, idlogin)
        try:
            self.logger.info("-> (-) Suspend contrat : %s" % idcontrat)
            self.__oracle.cursor.callproc("APICONTRAT.SuspendreContrat", [idcontrat_var, idlogin_var])
        except Exception, ex:
            self.logger.error("Error: during suspending contrat : %s, cause: %s" %(idcontrat, ex))
    
    def __resume_contrat(self, idcontrat, idlogin):
        idcontrat_var = self.__oracle.cursor.var(cx_Oracle.NUMBER)
        idcontrat_var.setvalue(0, idcontrat)
        idlogin_var = self.__oracle.cursor.var(cx_Oracle.STRING)
        idlogin_var.setvalue(0, idlogin)
        try:
            self.logger.info("-> (+) Resume contrat : %s" % idcontrat)
            self.__oracle.cursor.callproc("APICONTRAT.ReprendreContrat", [idcontrat_var, idlogin_var])
        except Exception, ex:
            self.logger.error("Error: during resuming contrat : %s, cause: %s" %(idcontrat, ex))
    


def main():
    
    parser = argparse.ArgumentParser(description="Script Usage:")    
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--idcontrat", action="store", dest="contrat", nargs='+', help="List of Contrat ID or All", type=str.lower)
    group.add_argument("--idclient", action="store", dest="idclient", type=int, nargs='+', help="Client ID")
    parser.add_argument("--run", action="store", dest="run", nargs=1, help="Yes: to run , No: to display enabled contrat",
                         choices=('yes', 'no'), required=True, type=str.lower)
        
    args = parser.parse_args()

    idclients = args.idclient
    contrat = args.contrat
    run = args.run[0].lower()        
                
    if idclients is not None:
        try:
            idclients = map(lambda x: int(x), idclients)
        except ValueError, ex:
            print("invalid value in idclient, cause: %s" % ex)
            sys.exit(-1)
     
    if contrat is not None: # and contrat != "all":
        if len(contrat) == 1 and contrat[0] == "all":
            contrat = "all"
        else:
            contrat = map(lambda x: x.lower(), contrat)
            if "all" in contrat:
                contrat.remove('all')                
    
    rootpath = os.getenv('PYTHONPATH')
    if rootpath is None:
        rootpath = "/opt/iplabel/script"
    
    log_path = os.path.join(os.path.dirname(rootpath), "log")      
     
    if not os.path.exists(log_path):
        try:
            os.makedirs(log_path)
        except Exception, ex:
            raise Exception("Error: c'ant create log directory: %s, cause: %s" %(rootpath, ex))
                 
    log_file_name = "{0}.log".format(os.path.basename(sys.argv[0]).split('.')[0])    
    log_file_path = os.path.join(log_path, log_file_name)
    
    logformater = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    fileHandler = logging.FileHandler(log_file_path)
    fileHandler = logging.handlers.RotatingFileHandler(log_file_path, mode='a', maxBytes=2000000, backupCount=2)
    fileHandler.setFormatter(logformater)
    logger.addHandler(fileHandler)
    
    consoleHander = logging.StreamHandler()
    consoleHander.setFormatter(logformater)
    logger.addHandler(consoleHander)
    
    
    
    if contrat is not None:
        logger.info("#===================  +  ======================#")
        if run == "yes":            
            tmpdir = "ProbeHostName_contrats_%s" % datetime.now().strftime("%Y%m%d_%H%M%S")
            extractor = ExtractXmlContrat(idcontrat=contrat)            
            zips = extractor.extract_filtered_tzip_contrat(directory=tmpdir)
            new_zips = extractor.update_runpy(zips)
            extractor.close()
            
            regenerator = RegenerateXmlContrat()
            new_xml = regenerator.regenerate_xml_file(new_zips, zips)
            
            updater = UpdateXmlContrat()
            updater.update_xml(new_xml)
            
            for idcont in [x.get('idcontrat') for x in new_xml]:
                logger.info("Restart idcontrat: %s" % x.get('idcontrat'))
                # ipl599 -> id ordonnanceur account (see personne table on DTM databases)
                updater.restart_contrat(idcont, "ipl599", timeout=2)          
            updater.close()
        
        elif run == "no":            
            extrator = ExtractXmlContrat(idcontrat=contrat)
            extrator.display()
            extrator.close()
                        
        logger.info("#==============================================#")
    
    if idclients is not None:    
        if run == "yes":
            for idclient in idclients: 
                logger.info("#==================  %s =======================#" % idclient)        
                extrator = ExtractXmlContrat(idclient=idclient)
                zips = extrator.extract_filtered_tzip_contrat(directory=str(idclient))
                # print zips
                new_zips = extrator.update_runpy(zips)
                extrator.close()
                
                regenerator = RegenerateXmlContrat()
                reg_xml = regenerator.regenerate_xml_file(new_zips, zips)     
                 
                regenerator.create_w20m_file(reg_xml, directory=str(idclient))
                 
                updater = UpdateXmlContrat()                    
                updater.update_xml(reg_xml)
                 
                for idcont in [x.get('idcontrat') for x in reg_xml]:
                    logger.info("Restart idcontrat: %s" % x.get('idcontrat'))
                    # ipl599 -> id ordonnanceur account (see personne table on DTM databases)
                    updater.restart_contrat(idcont, "ipl599", timeout=2)          
                updater.close()
                
                logger.info("#=================================================#")
                
        elif run == "no":
            for idclient in idclients: 
                logger.info("#===================  %s ======================#" % idclient)
                extrator = ExtractXmlContrat(idclient=idclient)        
                extrator.display()
                extrator.close()
                logger.info("#=================================================#")
  
if __name__ == "__main__":
    main()
    print("SUCCESS !!")