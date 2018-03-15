# -*- coding: iso-8859-15 -*-
"""
#############################
# rbo
# version : 07/02/2017
# check job status
#
# require python3.4.0 or >
# require pymssql (v.2.1.1):
#	- pip.exe install pymssql
#
# rbo: 06/12/2017 update 
# rbo: 15/03/2018 unknow job status added
#
#############################
"""

import sys
import datetime
import pymssql

CRITICAL_STATUS = 2
WARNING_STATUS = 1
OK_STATUS = 0

server = "XXXXXXX"
user = "UserNagios"
password = "XXXXXXXX"
database = "XXXXXXXXXX"

result = ""

if __name__ == "__main__"	:
	try:
		conn = pymssql.connect(server, user, password, database)
		cur = conn.cursor()
		cur.execute("exec [PS_ADM_CHECKSQLJOBS]")
		result = cur.fetchall()
		#column = [i[0] for i in cur.description]
	except Exception as ex:
		print("CRITICAL : probleme lors de la connexion a BDD :" + database)
		print("cause:", ex)
		# try to close connection
		try:
			cur.close()
		except Exception as ex:
			print(ex)
		try:
			conn.close()
		except Exception as ex:
			print(ex)
		# exit program
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
		isFailed = False
		failed_jobs = []
		blocked_jobs = []
		canceled_jobs = []

		for line in result:
			failed_job = {}
			blocked_job = {}
			canceled_job = {}
			unknown_job = {}
			jobName = line[0]
			currentStatus = line[2]
			lastRunTime = line[4]
			# print(type(lastRunTime))
			lastRunOutcome = line[5]
			lastRunDuration = line[6]

			if currentStatus.__contains__('Running'):
				# if duration > 05h we asume that the job is blocked
				if int(lastRunDuration.split(':')[0]) >= 5:
					blocked_job['job_name'] = jobName
					blocked_job['status'] = lastRunOutcome
					blocked_job['last_run_time'] = lastRunTime.strftime("%Y-%m-%d %H:%M:%S")
					blocked_jobs.append(blocked_job)

			if lastRunOutcome is None:
				unknown_job['job_name'] = jobName
				unknown_job['status'] = lastRunOutcome
				unknown_job['last_run_time'] = lastRunTime.strftime("%Y-%m-%d %H:%M:%S")
				unknown_job.append(unknown_job)
			else:
				if lastRunOutcome.__contains__('Fail'):
					failed_job['job_name'] = jobName
					failed_job['status'] = lastRunOutcome
					failed_job['last_run_time'] = lastRunTime.strftime("%Y-%m-%d %H:%M:%S")
					failed_jobs.append(failed_job)

				if lastRunOutcome.__contains__('Cancel'):
					canceled_job['job_name'] = jobName
					canceled_job['status'] = lastRunOutcome
					canceled_job['last_run_time'] = lastRunTime.strftime("%Y-%m-%d %H:%M:%S")
					canceled_jobs.append(canceled_job)

		if len(failed_jobs) > 0:
			print("CRITICAL : Failed jobs detected => " + str(failed_jobs))
			sys.exit(CRITICAL_STATUS)
		elif len(blocked_jobs) > 0:
			print("CRITICAL : Blocked jobs detected => " + str(blocked_jobs))
			sys.exit(CRITICAL_STATUS)
		elif len(canceled_jobs) > 0:
			print("CRITICAL : Canceled jobs detected => " + str(canceled_jobs))
			sys.exit(CRITICAL_STATUS)
		elif len(unknown_job) > 0:
			print("CRITICAL : Unknown job status detected => " + str(canceled_jobs))
			sys.exit(CRITICAL_STATUS)
		else:
			print("OK : All jobs end with Success !!")
			sys.exit(OK_STATUS)

	else:
		print("CRITICAL : L'execution de la procedure: PS_ADM_CHECKSQLJOBS renvoie une reponse vide, pas historique du job")
		sys.exit(CRITICAL_STATUS)
