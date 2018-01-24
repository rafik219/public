# -*- coding: utf-8 -*-
"""
##############################
# rbo
# version : 15/02/2017
# check control chain

# require python3.4.0 or >
# require pymssql (v.2.1.1):
#	- pip.exe install pymssql
# Frequence : 60 min
##############################
"""

import sys
import pymssql
import getopt
import os
import subprocess

from xml.etree import ElementTree
from datetime import datetime

CRITICAL_STATUS = 2
WARNING_STATUS = 1
OK_STATUS = 0

"""
# Connexion mssql PARALI83
"""
server = "PARALI83"
# server = "PARALI82"
user = "UserNagios"
password = "XXXXXXXXX"
database = "CloudObserver_DTW"

"""
# Azure credential file.
"""
azure_cred_file = "F:\SSIS\DataTransfert_Azure_001.dtsConfig"
package_connection = "DS_CloudObserver_REF_Azure"

# nbr_chain_file_name = "nbr_azure_chain.txt"
nbr_chain_file_name = "nbr_azure_chain.xml"
today = datetime.now()
today_day = today.day
result = ""

def usage():
	print("---------------------------------------------------------------")
	print("Usage:")
	print("\t %s -s <seuil>" % sys.argv[0])
	print("Ou")
	print("\t %s --seuil <seuil>" % sys.argv[0])
	print("\n - <seuil> : Le seuil max de retard d'insertion en Minute.")
	print("---------------------------------------------------------------")
	sys.exit(-1)

def get_azure_creadentiel():
	credential = dict()
	if os.path.exists(azure_cred_file):
		etree = ElementTree.parse(azure_cred_file)
		root = etree.getroot()
		for elt, config in enumerate(root.findall('Configuration')):
			# print(elt, config)
			if config.get('Path').find(package_connection) != -1:				
				connection_info_list = config.find('ConfiguredValue').text.replace('\n', '').split(';')
				for info in connection_info_list:
					if info != "":
						var_tmp = info.split('=')
						credential[var_tmp[0].lower().replace(' ', '_')] = var_tmp[1]					
				return credential
				break	
	
def get_azure_active_chain():
	nbr_chain = list()
	# get_azure_creadentiel()		
	azure_cred = get_azure_creadentiel()
	azure_data_source = azure_cred.get('data_source')
	azure_user = azure_cred.get('user_id')
	azure_password = azure_cred.get('password')
	azure_database = azure_cred.get('initial_catalog')
						
	azure_req = u"""SELECT DISTINCT 'ODS_001_'+ azp_channel FROM dbo.AZURE_PARAMETER WHERE azl_id = 1 AND azp_isactif = 1 AND azp_channel <> '000'"""
							
	try:
		nbr_chain_file = os.path.join(os.path.dirname(__file__), nbr_chain_file_name)
	except Exception as ex:
		nbr_chain_file = "C:\\{}".format(nbr_chain_file_name)
	
	"""	
	# Method 1: Generate .txt output file
	sqlcmd_cmd = ["SQLCMD.exe", "-W", "-u", "-h-1", "-S", azure_data_source,
					"-d", azure_database, "-U", azure_user, "-P", azure_password, "-Q", azure_req,
					"-o", nbr_chain_file, "-f", "65001", "-I"]
	"""	
	# Method 2: Generate .xml output file
	bcp_cmd = ["bcp.exe",
				azure_req + " FOR XML AUTO, ELEMENTS, ROOT('chain')",
				"queryout", nbr_chain_file,
				"-S", azure_data_source,
				"-d",  azure_database,
				"-U", azure_user,
				"-P", azure_password,
				"-c"]	
	out = None 
	err = None
	# use sqlcmd to query azure database and output result on: nbr_chain_file
	if not os.path.exists(nbr_chain_file):
		try:
			out, err = subprocess.Popen(bcp_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).communicate()
		except Exception as ex:
			nbr_chain = ["ODS_001_001", "ODS_001_002", "ODS_001_003", "ODS_001_004", "ODS_001_005"]
			return nbr_chain
	else:
		# check if file age is old then 1 day	
		file_age = datetime.fromtimestamp(os.path.getmtime(nbr_chain_file))
		file_epoch = today - file_age
		if file_epoch.days >= 1:
			# print('regenerate file')
			try:
				out, err = subprocess.Popen(bcp_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).communicate()
			except Exception as Ex:
				pass
	# read xml output file
	etree_root = ElementTree.parse(nbr_chain_file).getroot()
	nbr_chain = [ elt.text for elt in etree_root.iter('dbo.AZURE_PARAMETER') ]
	return nbr_chain
	
	
def main():
	argument = sys.argv[1:]
	# print len(argument)

	if len(argument) < 2:
		usage()
	try:
		opts, args = getopt.getopt(sys.argv[1:], 's:h', ['seuil=', 'help='])
		# print opts
	except getopt.GetoptError as e:
		print(str(e))
		usage()

	for (opt, arg) in opts:
		if opt in ('-s', '--seuil'):
			max_threshold_delay = int(arg) * 60			
		else:
			usage()
			
	try:		
		# get chain status
		conn = pymssql.connect(server, user, password, database)
		cur = conn.cursor()	
		
		req ="""
				select AZP_CHANNEL,
						max(OBS_INSERTTIME) MAX_INSERTIME, 
						count(obs_refid) ROW_COUNT,
						GETDATE() CURRENT_UTC_TIME 
				from OBSERVER_DATA 
				where OBS_day=""" + str(today_day) + """ 
				group by AZP_CHANNEL
			 """			
		#print(req)
		
		#cur.execute("select * from [dbo].[CONTROL_AZURE_TRANSFERT]")
		cur.execute(req)
		result = cur.fetchall()			
		# column = [i[0] for i in cur.description]			
		
		# Not work: need drivers version 13.1
		# azure_conn = pymssql.connect(server=azure_data_source, user=azure_user, password=azure_password, database=azure_database)
		# azure_cur = azure_conn.cursor()
		# azure_cur.execute(azure_req)
		# azure_result = azure_cur.fetchall()					
		# print(azure_result)
		
		azure_active_chain = get_azure_active_chain()	
					
	except Exception as ex:
		print("probleme lors de la connexion")
		print("cause:", ex)	
		try:			
			cur.close()			
		except Exception as ex:
			print(ex)		
		try:			
			conn.close()
		except Exception as ex:
			print(ex)	
		sys.exit(CRITICAL_STATUS)		
	finally:
		try:			
			cur.close()
		except Exception as ex:
			print(ex)		
		try:			
			conn.close()
		except Exception as ex:
			print(ex)	
			
	if len(result) != 0:		
		if len(azure_active_chain) == 0:
			print("KO: nombre de chaine active est null, erreur de la generation/lecture du fichier .xml")
			sys.exit(CRITICAL_STATUS)
		
		# detect problem on some distribution chain
		list_chain_with_problem = list()
		if len(result) < len(azure_active_chain):
			chains = [chain[0] for chain in result]
			for active_chain  in azure_active_chain:
				if active_chain not in chains:
					list_chain_with_problem.append(active_chain)
						
		if len(list_chain_with_problem) != 0:
			print("CRITICAL: Liste des chaines en probleme: %s " % [ ch for ch in list_chain_with_problem ])
			sys.exit(CRITICAL_STATUS)
		
		# [print(i) for i in column]
		chain_ko_count_zero = []
		chain_ko_delay = []
								
		for entry in result:
			chain_info_ko = {}
			chain_info_ko['AZP_CHANNEL'] = entry[0]
			max_insertime = entry[1]
			chain_info_ko['MAX_INSERTIME'] = max_insertime.strftime('%Y-%m-%d %H:%M:%S')
			chain_info_ko['ROW_COUNT'] = entry[2]
			current_utc_time = entry[3]
			chain_info_ko['CURRENT_UTC_TIME'] = current_utc_time.strftime('%Y-%m-%d %H:%M:%S')					
			delta_time = abs(current_utc_time - max_insertime)						
			delta_time_sec = delta_time.total_seconds()
			chain_info_ko['DELTA_TIME'] = delta_time_sec
			
			# seuil max retard insertion: 30 minutes.
			# max_threshold_delay = 30 * 60
			
			if chain_info_ko['ROW_COUNT'] == 0:
				chain_ko_count_zero.append(chain_info_ko)
			else:
				if int(delta_time_sec) > max_threshold_delay:
					chain_ko_delay.append(chain_info_ko)		
			
		if len(chain_ko_count_zero) > 0 or len(chain_ko_delay) > 0:	
			if len(chain_ko_count_zero) > 0:			
				chain_ko_count_zero_str = ">>"
				chain_disp = ""
				for e, ch in enumerate(chain_ko_count_zero):
					# print(ch['AZP_CHANNEL'])
					chain_disp = "\t(" + str(e) + ")" + " => [Name:" + str(ch['AZP_CHANNEL']) + ",  Count:" + str(ch['ROW_COUNT']) + "]"
					# print(e, ch)
					# chain_ko_count_zero_str += str(ch['AZP_CHANNEL'])
					chain_ko_count_zero_str += chain_disp									
				print("CRITICAL : Liste des chaines en problemes: " + chain_ko_count_zero_str)				
			
			#if 1:
			if len(chain_ko_delay) > 0:			
				chain_ko_delay_str = ">>"
				chain_disp= ""
				#chain_ko_delay = chain_ko_count_zero # for test
				for e, ch in enumerate(chain_ko_delay):
					chain_disp = "\t(" + str(e) + ")" + " => [Name:" + str(ch['AZP_CHANNEL']) + ",  Delay:" + str(ch['DELTA_TIME']) + "]"
					chain_ko_delay_str += chain_disp
				print('CRITICAL : Liste des chaines en retard: ' + chain_ko_delay_str)				
			sys.exit(CRITICAL_STATUS)
		else:
			print("OK : Pas de probleme sur les chaines de traitements !!")
			sys.exit(OK_STATUS)	
	else:
		print("CRITICAL : Probleme de transfert de donnees Azure vers le DWH")
		sys.exit(CRITICAL_STATUS)
			
if __name__=="__main__"	:
	main()
	
			

	
	

	
