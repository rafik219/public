# -*- coding: iso-8859-15 -*-
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
import datetime
import pymssql
import getopt

CRITICAL_STATUS = 2
WARNING_STATUS = 1
OK_STATUS = 0

server = "PARALI83"
# server = "PARALI82"
user = "UserNagios"
password = "XXXXXXXXXX"
database = "CloudObserver_DTW"

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

	
if __name__=="__main__"	:

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
		conn = pymssql.connect(server, user, password, database)
		cur = conn.cursor()	
		today = datetime.datetime.now()
		today_day = today.day
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
				print("CRITICAL : Liste des chaines en probl�mes: " + chain_ko_count_zero_str)				
			
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
			
			
			

	
	

	
