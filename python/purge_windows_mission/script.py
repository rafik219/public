# author: rbo
# version: 06/10/2016


import os
import sys
import glob
import cx_Oracle
import xml.etree.ElementTree
import shutil
from datetime import datetime

config_path = os.path.join(os.getenv("iplabel"),"config")
xmldoc_path = os.path.join(config_path, "siteagent.xml")
print(xmldoc_path)
tree = xml.etree.ElementTree.parse(xmldoc_path)
siteagentconf = tree.getroot()
user =  siteagentconf.find("./db/user").text
srvaddr =  siteagentconf.find("./db/srvaddr").text
srvport =  siteagentconf.find("./db/srvport").text
servicename =  siteagentconf.find("./db/servicename").text

def display(List):
	for e in List:
		print(e)


try:
	constr = '%s/xxXXxx@%s:%s/%s' % (user,srvaddr,srvport,servicename)    
	print(constr)
	con = cx_Oracle.connect(constr)
	cur = con.cursor()
	sql = "SELECT IDMISSION FROM mission where TYPEAPPLICATION=41 and ETATMISSIONSITE = 1"
	cur.execute(sql)
	res = cur.fetchall()
	listidmission_req = []
	for elt in res:
		listidmission_req.append(elt[0])
	listidmission_req.sort()
	#display(listidmission_req)
	
except Exception as e:
	print(e)
	print("Probmeme lors de la connexion a la base ")
	sys.exit(-1)
finally:
	con.close()

dirMission = os.path.join(os.getenv("iplabel"), "mission")
print(dirMission)
nbrmission = 0
listidmission_rep = []

for directory in glob.glob(dirMission + "/*"):
	# print(directory)
	for d in glob.glob(directory + "/*"): 
		# print("\t" + d)
		idmission = d.split("\\")[-1]
		# print(idmission)
		listidmission_rep.append(idmission)
		nbrmission += 1
listidmission_rep.sort()

diff = []
cwd = os.path.dirname(__file__)

"""
with open(os.path.join(cwd, "mission_active.log"), "w") as file:
	file.write("Liste des idmission active sur la base: %s \n\n" % str(len(listidmission_req)))
	for i in listidmission_req:
		file.write(str(i) + "\n")

with open(os.path.join(cwd, "mission_local.log"), "w") as file:
	file.write("Liste des idmission Local sur la sonde: %s \n\n" % str(len(listidmission_rep)))
	for i in listidmission_rep:
		file.write(str(i) + "\n")
#"""

# delete mission from the list
for q in listidmission_req:
	for p in listidmission_rep:
		# print(str(q) +" <-> "+str(p))
		if int(q) == int(p):
			listidmission_rep.remove(p)
			diff.append(q)
			break

with open(os.path.join(cwd, "mission_to_delete.log"), "w") as file:
	start = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
	file.write("*****************************\n")
	file.write("* Start: %s \n" % start)
	file.write("*****************************\n\n")
	file.write("nbr mission local : %s \n" % str(nbrmission))
	file.write("nbr misison active : %s \n" % str(len(diff)))
	file.write("nbr mission deleted : %s \n\n" % str(len(listidmission_rep)))
	file.write("Liste des repertoires a supprimer: %s \n\n" % str(len(listidmission_rep)))
	for i in listidmission_rep:
		stri = str(i)
		full_path = dirMission + "\\" + stri[len(stri)-2:] + "\\" + stri
		file.write(str(full_path) + "\n")

# delete rep
if len(listidmission_rep) > 0 :
	for d in listidmission_rep:
		full_path = dirMission + "\\" + d[len(d)-2:] + "\\" + d
		if os.path.exists(full_path):
			print(full_path)
			shutil.rmtree(full_path)
			pass
else:
	print("pas de repertoire a supprimer..")	

"""
print("----------------------------")
print("nbr mission total : " + str(nbrmission))
print("nbr misison active : " + str(len(diff)))
print("nbr mission deleted : " + str(len(listidmission_rep)))
print("----------------------------")
"""
print("success !!!")
sys.exit(0)
