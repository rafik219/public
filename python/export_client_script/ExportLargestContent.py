#!/bin/env python2.7
# -*- coding: utf-8 -*-

##################################
# author: rbo
# utility: export largest content
# require python2.7
#
# need to install:
# pip2.7 install xlsxwriter
# pip2.7 install requests[security]
#
# version: 21/12/2017
# RBO    : 18/01/2018 add Cc option for sending email
# RBO    : 12/02/2018 add size option
# RBO    : 22/03/2018 keep only 24h during request fromdate,todate
# RBO    : 16/04/2018 filter with object type exp: images, css ...
# RBO    : 16/04/2018 bug correction
#
###################################

import argparse
import os
import smtplib
import sys
from datetime import date, datetime, timedelta
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from re import match, compile

import requests
import xlsxwriter


def usage():
    print("""usage: ExportLargestContent.py [-h] [--idclient IDCLIENT] [--login LOGIN] 
                               [--password PASSWORD]                      
                               [--email EMAIL [EMAIL ...]]                
                               [--cc COPY_EMAIL [COPY_EMAIL ...]]         
                               [--fromdate [FROMDATE]] [--todate [TODATE]]
                               [--limit [LIMIT]] [--size [SIZE]] [--version]              
                                                                          
    This is the description:                                                  
                                                                              
    optional arguments:                                                       
      -h, --help                        show this help message and exit                   
      --idclient IDCLIENT               Client ID                                         
      --login LOGIN                     WS login for client account                       
      --password PASSWORD               WS password for client account                    
      --email EMAIL [EMAIL ...]         List of destination email                         
      --cc COPY_EMAIL [COPY_EMAIL ...]  List of copy email (cc)                           
      --fromdate [FROMDATE]             Starting date with format like: YYYY/MM/DD        
      --todate [TODATE]                 End date with format like: YYYY/MM/DD             
      --limit [LIMIT]                   Number of extracting object                       
      --size [SIZE]                     Size of objects, exp: ">400Ko"     
      --objecttype [OBJ_TYPE]           Object type, exp: images or js or css      
      --version                         show program's version number and exit """)
    sys.exit(0)


class ExportContentLargest:
    def __init__(self, idclient, login, password, from_date=None, to_date=None, limit=None):
        self.id_client = idclient
        self._login = login
        self._password = password
        self.from_date = from_date
        self.send_from = "production@ip-label.com"
        self.to_date = to_date
        self.limit = limit
        self.smtp_server = "0.0.0.0"
        self.smtp_port = "25"
        self.ws_server = "webservice.ip-label.net"
        self.url_get_monitors = "https://{}/latest/REST/Get_Monitors/".format(self.ws_server)
        self.url_get_content_largest = "https://{}/latest/REST/Get_Content_Largest_Assets/".format(self.ws_server)
        self.enabled_monitors = []
        self.epoch = datetime.now()
        self.workbook_name = "Export_largest_content_{}_{}.xlsx".format(self.id_client, self.epoch.strftime("%Y%m%d_%H%M%S"))
        self.workbook_path = os.path.join(os.path.dirname(__file__), self.workbook_name)
        self._empty_workbook = True
        self.img_extension = ['jpg', 'png', 'gif', 'jpeg', 'tif', 'tiff', 'webp','svg', 'eps',  'psd', 'ai', 'bmp', 'pct', 'swf']
        self.js_extension = ['js']
        self.css_extension = ['css']

    def get_enable_monitors(self):
        """ Get Enabled Monitors for Client_ID """
        try:
            req = requests.get(self.url_get_monitors, auth=requests.auth.HTTPBasicAuth(self._login, self._password))
            if req.status_code == 200:
                response = req.json()
                for key, value in response.get('Ipln_WS_REST_datametrie').iteritems():
                    if key == u'Get_Monitors':
                        if value.get('status') == u'success':
                            if len(value.get('response')) != 0:
                                for resp in value.get('response'):
                                    if resp.get('MONITOR_STATUS') == u'PROCESSING':
                                        self.enabled_monitors.append(resp)
                            else:
                                print("No enable monitors found for this account ...")
                                sys.exit(-1)
                        else:
                            print("ERROR: Get_Monitirs() method return: {} for this idClient: {}".format(
                                    value.get('status'),
                                    self.id_client))
                    elif key == u'':
                        print("ERROR: Can't get List all Monitors for this idClient %s, cause: " % self.id_client)
                        print("\t => %s" % response.get('Ipln_WS_REST_datametrie').get(key).get('status'))
                        print("\t => %s" % response.get('Ipln_WS_REST_datametrie').get(key).get('message'))
                        sys.exit(-2)
            else:
                print("ERROR: Server responds with: %s code for this request" % req.status_code)
                sys.exit(-3)
        except Exception as ex:
            print("ERROR: During get enable monitors, cause : %s" % ex)
            sys.exit(-4)

        return sorted(self.enabled_monitors, key=lambda k: k['MONITOR_NAME'].lower())

    def split_enable_monitors(self):
        """ Get Different Index Of Enabled Monitors """
        first_chars = []
        index_monitor_list = []
        for e, monitor in enumerate(self.enabled_monitors):
            first_char_name = monitor.get('MONITOR_NAME')[0].lower()
            if first_char_name not in first_chars:
                first_chars.append(first_char_name)
                index_monitor_list.append(e)
            elif e == len(self.enabled_monitors) - 1:
                index_monitor_list.append(e)
        return index_monitor_list

    def get_largest_content(self, monitor_id):
        """ Get List Content Largest for monitor_id """
        largest_object = []
        today = date.today()
        if self.from_date is None and self.to_date is None:
            # self.from_date = (today - timedelta(1)).strftime("%d/%m/%Y %H:%M:%S")
            # self.to_date = today.strftime("%d/%m/%Y %H:%M:%S")
            self.from_date = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y %H:%M:00")
            self.to_date = datetime.now().strftime("%d/%m/%Y %H:%M:00")
            
        elif self.from_date is None:
            # self.from_date = (today - timedelta(1)).strftime("%d/%m/%Y %H:%M:%S")
            self.from_date = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y %H:%M:00")
            
        elif self.to_date is None:
            # self.to_date = today.strftime("%d/%m/%Y %H:%M:%S")
            self.to_date = datetime.now().strftime("%d/%m/%Y %H:%M:00")
            
        if self.limit is None:
            self.limit = 10
            
        url_get_content_largest = "{}?monitor_id={}&date_value1={}&date_value2={}&limit={}".format(
                self.url_get_content_largest, monitor_id, self.from_date, self.to_date, self.limit)
        print("Sending request : %s" % url_get_content_largest)
        try:
            req = requests.get(url_get_content_largest, auth=requests.auth.HTTPBasicAuth(self._login, self._password))
            if req.status_code == 200:
                response = req.json()
                if response.get('Ipln_WS_REST_datametrie') is not None:
                    for key, value in response.get('Ipln_WS_REST_datametrie').iteritems():
                        if key == u'Get_Content_Largest_Assets':
                            if value.get('status') == u'success':
                                if len(value.get('response')) != 0:
                                    for resp in value.get('response'):
                                        largest_object.append(resp)
                                else:
                                    print("ERROR: Largest response is Empty for this monitor")
                            else:
                                print(
                                        "ERROR: Get_Content_Largest_Assets() method return:{} for this monitor_id:{}, message: {}".format(
                                                value.get('status'), monitor_id, value.get('response').get('message')))
                        elif key == u'':
                            print("ERROR: Can't get response largest for this monitor: {}".format(monitor_id))
                else:
                    print("ERROR: Maybe Get_Content_Largest_Assets() Method does not exist on ws api")
            else:
                print("ERROR: Server responds with: %s code for this request" % req.status_code)
        except Exception as ex:
            print("ERROR: During request, cause: %s" % ex)
        return largest_object

    def create_xlsx_file(self, obj_size=None, obj_type=None):
        enable_monitors = self.get_enable_monitors()
        split_enable_monitors = self.split_enable_monitors()
        # import pdb; pdb.set_trace()
        caption = "IP-LABEL Export : Largest Content  {}".format(datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
        workbook = xlsxwriter.Workbook(self.workbook_path, {'strings_to_urls': False})
        format_text = workbook.add_format({'bold': True, 'font_color': 'red'})
        format_text.set_font_size(15)
        list_worksheet = []
        if obj_size is not None:
            operator = obj_size[0]
            object_size = int(obj_size[1:-2])
            size_unit = obj_size[-2:]
            caption = "{},  Object Size {} {}{}".format(caption, operator, object_size, size_unit)

        for k, v in enumerate(split_enable_monitors):            
            draw_worksheet_table = False
            first_row = 2
            first_col = 1
            last_col = 3
            decal_rows = 3

            if k != len(split_enable_monitors) - 1:
                enabled_monitors_range = enable_monitors[split_enable_monitors[k]: split_enable_monitors[k + 1]]
            else:
                enabled_monitors_range = enable_monitors[split_enable_monitors[k]:]

            for monitor in enabled_monitors_range:
                monitor_id = monitor.get('MONITOR_ID')
                print("Monitor ID: %s" % monitor_id)

                largest_content = self.get_largest_content(monitor_id)                  

                if obj_type is not None:
                    # extract object: image or js or css for largest_content list.
                    largest_content_tmp = []
                    search_in = ''
                    if obj_type == "images":
                        search_in = self.img_extension
                    elif obj_type == "js":
                        search_in = self.js_extension
                    elif obj_type == "css":
                        search_in = self.css_extension

                    for e, extension in enumerate(largest_content):                        
                        obj_name = extension.get('URL').split('/')[-1] #.split('.')[1] 
                        if obj_name != '' and obj_name.find('.') != -1:
                            obj_ext = obj_name.split('.')[1]                        
                        # print(obj_ext, extension.get('URL'))
                        if obj_ext in search_in:
                            largest_content_tmp.append(largest_content[e])
                    
                    largest_content = largest_content_tmp

                if obj_size is not None:
                    if operator == ">":
                        largest_content = filter(lambda k: k.get("WEIGHT") > (object_size * 1000), largest_content)
                    elif operator == "<":
                        largest_content = filter(lambda k: k.get("WEIGHT") < (object_size * 1000), largest_content)

                worksheet_name = enable_monitors[v].get('MONITOR_NAME')[0].upper()
                # time.sleep(1)
                if worksheet_name not in list_worksheet and len(largest_content) != 0:
                    print("======================== CREATE WORKSHEET : '%s' ====================" % worksheet_name)
                    list_worksheet.append(worksheet_name)
                    worksheet = workbook.add_worksheet(name=worksheet_name)
                    worksheet.set_column('B:E', 12)
                    worksheet.write('B1', caption, format_text)
                    draw_worksheet_table = True
                    self._empty_workbook = False

                if len(largest_content) != 0:
                    draw_worksheet_table = True
                    for elt, line in enumerate(largest_content):
                        monitor_rows = []
                        if elt == 0:
                            monitor_rows.append(monitor.get('MONITOR_NAME'))
                        else:
                            monitor_rows.append('')
                        monitor_rows.append(line.get('URL'))
                        monitor_rows.append(line.get('WEIGHT'))
                        decal_rows += 1
                        # print  monitor_rows, 'B{}'.format(split_enable_monitors[k] + decal_rows + elt)
                        print(monitor_rows, 'row : B{}'.format(decal_rows))
                        worksheet.write_row('B{}'.format(decal_rows), monitor_rows)
                    print("\n")
                else:
                    if obj_size is not None:
                        print("\t => Empty object for this monitor : %s, with this filter: %s \n" % (monitor_id, obj_size))
                    else:
                        print("\t => Empty object for this monitor : %s \n" % monitor_id)

            if draw_worksheet_table:
                worksheet.add_table(first_row, first_col, decal_rows - 1, last_col, {
                    'columns': [{'header': 'MONITOR NAME'}, {'header': 'URL'}, {'header': 'SIZE'}]})

        workbook.close()

        if os.path.exists(self.workbook_path):
            return True, self.workbook_path
        else:
            return False, "XLSX File is not generated !!"

    def send_mail(self, send_to, subject, text, files, cc_to=None, username='', password='', istls=False):
        msg = MIMEMultipart()
        msg['From'] = self.send_from
        msg['To'] = send_to
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = subject
        if cc_to is not None:
            msg['Cc'] = cc_to
            destination = send_to.split(',') + msg['Cc'].split(',')
        else:
            destination = send_to.split(',')

        msg.attach(MIMEText(text))
        part = MIMEBase('application', "octet-stream")
        part.set_payload(open(files, "rb").read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="{}"'.format(os.path.basename(files)))
        msg.attach(part)
        # context = ssl.SSLContext(ssl.PROTOCOL_SSLv3)
        # SSL connection only working on Python 3+
        smtp = smtplib.SMTP(self.smtp_server, self.smtp_port)
        if istls:
            smtp.starttls()
        if username != '' and password != '':
            smtp.login(username, password)

        smtp.sendmail(self.send_from, destination, msg.as_string())
        smtp.quit()


def main():
    parser = argparse.ArgumentParser(description="This is the description:")
    parser.add_argument("--idclient", action="store", dest="idclient", type=int, nargs=1, help="Client ID")
    parser.add_argument("--login", action="store", dest="login", nargs=1, help="WS login for client account")
    parser.add_argument("--password", action="store", dest="password", nargs=1, help="WS password for client account")
    parser.add_argument("--email", action="store", dest="email", nargs="+", help="List of destination email")
    parser.add_argument("--cc", action="store", dest="copy_email", nargs="+", help="List of copy email (cc)")
    parser.add_argument("--fromdate", action="store", dest="fromdate", nargs="?",
                        help="Starting date with format like: YYYY/MM/DD")
    parser.add_argument("--todate", action="store", dest="todate", nargs="?",
                        help="End date with format like: YYYY/MM/DD")
    parser.add_argument("--limit", action="store", dest="limit", nargs="?", type=int,
                        help="Number of extracting object")
    parser.add_argument("--size", action="store", dest="size", nargs="?", help="Size of objects, exp: \">400Ko\"")
    parser.add_argument("--objecttype", action="store", dest="obj_type", nargs="?", help="Object type, exp: images or js or css")
    parser.add_argument("--version", action="version", version="v0.1")

    args = parser.parse_args()

    if args.idclient is None or args.login is None or args.password is None or args.email is None:
        print("Usage: python %s -h" % sys.argv[0])
        sys.exit(-1)

    # check formating email address 
    if args.email is not None:
        for mail in args.email:
            regex = compile(r"^[a-z0-9._-]+@[a-z0-9._-]+\.[a-z]+")
            if regex.match(mail) is None:
                print("ERROR: Invalid email address: %s !!" % mail)
                sys.exit(-2)
    if args.copy_email is not None:
        for mail in args.copy_email:
            regex = compile(r"^[a-z0-9._-]+@[a-z0-9._-]+\.[a-z]+")
            if regex.match(mail) is None:
                print("ERROR: Invalid Cc address: %s !!" % mail)
                sys.exit(-2)
                # check format for fromdate and todate
    if args.fromdate is not None:
        if match(r"^[0-9]{2}/[0-9]{2}/[0-9]{4}$", args.fromdate) is None:
            print("ERROR: Incorrect formating date, use: DD/MM/YYYY")
            sys.exit(-2)
    if args.todate is not None:
        if match(r"^[0-9]{2}/[0-9]{2}/[0-9]{4}$", args.todate) is None:
            print("ERROR: Incorrect formating date, use: DD/MM/YYYY")
            sys.exit(-2)
    if args.size is not None:
        if match(r"^(<|>)\d+(k|K)(o|O)$", args.size) is None:
            print("ERROR: Invalid format of size, try with this format, exp: \">400Ko\" or \"<400Ko\"")
            sys.exit(-2)

    if args.obj_type is not None:
        if args.obj_type not in ['images', 'js', 'css']:
            print("ERROR: value for objecttype is: images OR js OR css")
            sys.exit(-2)       


    idclient = args.idclient[0]
    _login = args.login[0]
    _password = args.password[0]
    send_to = ",".join(args.email)
    cc_to = ",".join(args.copy_email) if args.copy_email is not None else None
    from_date = args.fromdate
    if from_date is not None:
        from_date += " 00:00:00"
    to_date = args.todate
    if to_date is not None:
        to_date += " 00:00:00"
    limit = args.limit
    size = args.size
    obj_type = args.obj_type

    # rbo: 22/03/2018 
    # disable from_date & to_date option and keep only 24h
    from_date, to_date = (None, None) 

    export = ExportContentLargest(idclient, _login, _password, from_date=from_date, to_date=to_date, limit=limit)

    status, response = export.create_xlsx_file(obj_size=size, obj_type=obj_type)

    if not export._empty_workbook:
        print(status, response)
        subject = "Export Largest Content : {}".format(export.epoch.strftime("%Y/%m/%d %H:%M:%S"))
        text = """
            Bonjour, \n\n
            
            Vous Trouverez ci-joint l'export des tops 10 des objets les plus volumineux.\n\n
                     
            Cordialement,\n\n 
                    
            Support IP-LABEL
        """

        if status:
            export.send_mail(send_to, subject, text, export.workbook_path, cc_to=cc_to)
            print("SUCCESS: Email was sent to : %s" % args.email)
            if cc_to is not None:
                print("SUCCESS: Email was sent to Cc: %s" % args.copy_email)
            try:
                os.remove(response)
                print("SUCCESS: File %s deleted" % response)
            except Exception as ex:
                print("ERROR: during deleting generated files, cause : {}".format(ex))
        else:
            print("ERROR: not need to send email, because: %s" % response)
    else:
        print("ERROR : Empty document, not need to send email")
        if os.path.exists(export.workbook_path):
            os.remove(export.workbook_path)
            print("SUCCESS: empty file %s deleted" % export.workbook_path)
        sys.exit(0)


if __name__ == "__main__":
    main()
    print("success !!")