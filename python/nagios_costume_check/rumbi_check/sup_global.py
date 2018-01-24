# -*- coding: iso-8859-15 -*-
"""
##############################
# rbo
# version : 15/02/2017
# check global chain
#
# require python3.4.0 or >
# require pymssql (v.2.1.1):
#	- pip.exe install pymssql
#	- pip.exe install pytz
#	- pip.exe install tzlocal
# Frequence : 30 min
##############################
"""

import sys
import getopt
import pymssql

from datetime import datetime, timedelta, time
from pytz import timezone
from tzlocal import get_localzone

CRITICAL_STATUS = 2
WARNING_STATUS = 1
OK_STATUS = 0

server = "PARALI83"
#server = "PARALI82"
user = "UserNagios"
password = "XXXXXXXXXXX"
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

def convert_to_europe_paris_tz(local_date):
	fmt = "%Y-%m-%d %H:%M:%S"
	# now = datetime.now()
	tz_local = get_localzone()		
	local_tz = timezone(str(tz_local))	
	local = local_tz.localize(local_date)	
	paris_tz = timezone('Europe/Paris')	
	paris = paris_tz.localize(local_date)	
	return paris_tz.normalize(local.astimezone(paris_tz))
		
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
		# req = "select AZP_CHANNEL, max(OBS_INSERTTIME) MAX_INSERTIME, count(obs_refid) ROW_COUNT,  GETDATE() CURRENT_UTC_TIME from OBSERVER_DATA where OBS_day=" + str(today_day) + " group by AZP_CHANNEL"			
		req =""" 
				select count(s.obs_refid) NbRow,  max(HOU_FullHour) MaxHour
				from OBSERVER_DATA_SUP d
				inner join OBSERVER_METRIC_SUP s on d.obs_refid = s.OBS_REFID and d.AZP_CHANNEL = s.AZP_CHANNEL
				inner join CALENDAR_HOUR h on h.hou_id = d.HOU_ID
				where TRC_ID = 201 and PRS_ID = 1615
			 """
		# print(req)		
		cur.execute(req)
		result = cur.fetchall()			
		# column = [i[0] for i in cur.description]
	except Exception as ex:
		print("probleme lors de la connexion a la base " + database)
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
		# print(result)
		NbrRow = result[0][0]
		MaxHour = result[0][1]		
			
		if int(NbrRow) == 0:
			print('CRITICAL : Probleme de transfert de donnees Azure vers le DWH')
			sys.exit(CRITICAL_STATUS)
		else:
			# convert to Europe/Paris TimeZone
			today = convert_to_europe_paris_tz(datetime.now())
			# reformat today object
			datetimeformat = "%Y-%m-%d %H:%M:%S"
			today = datetime.strptime(today.strftime(datetimeformat), datetimeformat)
					
			# create datetime.datetime object with MaxHour value
			MaxHour_to_date = datetime(int(today.year), int(today.month), int(today.day), int(MaxHour[:2]), int(MaxHour[2:]), 0)			
			
			diff = today - MaxHour_to_date	
			# print("diff : ", diff)
			
			# max_threshold_delay = 30 * 60
			
			if int(diff.total_seconds()) > max_threshold_delay:			
				print("CRITICAL : Retard de transfert de donnees Azure vers le DWH, [delta-time: " + str(diff) + "]")
				sys.exit(CRITICAL_STATUS)
			else:
				print("OK : Transfert de donnees Azure vers le DWH, [delta-time: " + str(diff) + "]")
				sys.exit(OK_STATUS)
			
			
		

		