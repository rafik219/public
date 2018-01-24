#!/bin/bash

# ###################
#
# @uthor: rbo
# date: 11/07/2016
#
# ####################



#echo $NBR_ANALYSER_FILE
#INIT_DIR=/tmp/init_test/dev/


# ##################################
# Create query.sql File if not exist
# ##################################
CreateSQLFile(){
	if [ $1 = "REQ_1" ];then
		rang=$(cat ${PARAM_DIR}param.conf | grep "default_rang" | awk -F= '{print $2}')
		#echo $rang
	        #if [ ! -f $QUERY_1 ];then
                	#rm -f $QUERY_2
			echo "query.sql created !!"
	                # build query2.sql file
        	        touch $QUERY_1
                	chmod +rx $QUERY_1
	                echo -e "SET SQLBLANKLINES ON \nset echo off\nset feedback off\nset linesize 1000\nset pagesize 0\nset sqlprompt ''\nset trimspool on\nset headsep off\n\nREM Begin log result into result.csv file\nspool /opt/iplabel/script/result/result.csv\n\nREM request\nSELECT MIN(idcontrat), MAX(idcontrat)  FROM (SELECT idcontrat,ROUND(ROWNUM/${rang}) rang FROM (SELECT idcontrat FROM sitecentral.CONTRAT WHERE etatcontrat IN (1,4)ORDER BY idcontrat))GROUP BY ROLLUP(rang);\n\nREM end Log\nspool off " > $QUERY_1
        	#fi
	elif [ $1 = "REQ_2" ];then
                NBR_LINE=$(cat ${RESULT_FILE_1} | wc -l)
	        echo "query2.sql created !!"
	        touch $QUERY_2
	        chmod +rx $QUERY_2
	        MIN=$(sed -n "$(($NBR_LINE - 1))"p "${RESULT_FILE_1}" | awk '{ print $1 }')
	        echo -e "SET SQLBLANKLINES ON \nset echo off\nset feedback off\nset linesize 1000\nset pagesize 0\nset sqlprompt ''\nset trimspool on\nset headsep off\n\nREM Begin log result into result.csv file\nspool /opt/iplabel/script/result/result2.csv\n\nREM request\n\nSELECT count(*) FROM SITECENTRAL.CONTRAT where ETATCONTRAT in (1,4) and IDCONTRAT BETWEEN "$MIN" and 200000;\n\nREM end Log\nspool off " > $QUERY_2
	else
		echo "command: "$1" not found !"
	fi 
         #cat $QUERY_1
}

# ###############################################################
# Execute query*.sql end write result on : ../result/result*.csv
# ###############################################################
ExecuteSQLFile(){
	 # Get Login & Password
         VAR_USER=$(cat ${PARAM_DIR}DBconfig.ora | grep "SCH_USER" | awk -F= '{print $2}')
         VAR_USER_PWD=$(cat ${PARAM_DIR}DBconfig.ora | grep "SCH_PWD" | awk -F= '{print $2}')
         # Connect to the database and execute
         #       1. ${SQL_DIR}query.sql
         #       2. ${SQL_DIR}query2.sql
	if [ $1 = "REQ_1" ]; then
		sqlplus -s ${VAR_USER}/${VAR_USER_PWD}@MLINUX <<EOF
		REM excute Query and write result on /home/oracle/script/result/result.csv
		@"${SQL_DIR}query.sql";
		REM @${SQL_DIR}query2.sql;
		quit;
EOF
	elif [ $1 = "REQ_2" ];then
		sqlplus -s ${VAR_USER}/${VAR_USER_PWD}@MLINUX <<EOF
		REM excute Query and write result on /home/oracle/script/result/result.csv
		REM @"${SQL_DIR}query.sql";
		@${SQL_DIR}query2.sql;
		quit;
EOF
	else
                echo "command: "$1" not found !"
	fi

}

# ####################################
# AnalyseCptRendu Initialization 
# ####################################
function InitAnalyseCptrenduFile(){
	echo "Nombre de fichier alysecompterendu à créer: "$(($NBR_ANALYSER_RESULT_FILE - 1))
	COUNT=1
	# backup /etc/init/ to backup directory
	if [ ! $NBR_ANALYSER_FILE -eq 0 ];then
		#echo "All ${INIT_DIR}analysecompterendu* -> Deleted"
		#find ${INIT_DIR} -name "analysecompterendu*" -type f -exec rm -f {} \;
		#echo "move ${INIT_DIR}analysecompterendu*.conf to ${BACKUP_DIR}"
		#mv -f ${INIT_DIR}analysecompterendu* ${BACKUP_DIR}
		
		# unalias cp="cp -i" for the current root session to overwirte analysecompterendu*.conf files
		# unalias cp
		# backup inalysecompterendu*.conf files in backup directory
	        echo "backup /etc/init/ -> ${BACKUP_DIR} directory  :	OK"
        	cp -rf "${INIT_DIR}" "${BACKUP_DIR}"
		echo "Delete All Old ${INIT_DIR}analysecompterendu*.conf : 	 OK"
                find ${INIT_DIR} -name "analysecompterendu*" -type f -exec rm -f {} \;
	else
		# $NBR_ANALYSER_FILE = 0 aucun ficheir analysecompterendu*.conf dans le repertoire /etc/init/
		echo "Aucun fichier analysecompterendu*.conf trouvé dans /etc/init/  "
		#InitAnalyseCptrenduFile
	fi 

	sleep 3
	
	echo "Generate new analysecompterendu*.conf files on /etc/init/ :	OK"

        while [ $COUNT -le $(( $NBR_ANALYSER_RESULT_FILE - 1)) ];do
                MIN=$(sed -n "$COUNT"p "${RESULT_FILE_1}" | awk '{ print $1 }')
                MAX=$(sed -n "$COUNT"p "${RESULT_FILE_1}" | awk '{ print $2 }')
                FILE_NAME="analysecompterendu"$COUNT".conf"
                echo $FILE_NAME
                touch ${INIT_DIR}${FILE_NAME}
		#sleep 0.25
               	echo -e "start on runlevel [3]\nrespawn\n" > ${FILE_NAME}
                #echo "respawn" > $FILE_NAME
                #echo "" > $FILE_NAME

                if [ ! $COUNT -eq $(($NBR_ANALYSER_RESULT_FILE - 1)) ];then
                        echo 'exec /bin/su - iplabel -c "/opt/iplabel/bin/AnalyseCptRendus -deb '$MIN' -fin '$MAX' > /dev/null"' >> $FILE_NAME
                else
                        echo 'exec /bin/su - iplabel -c "/opt/iplabel/bin/AnalyseCptRendus -deb '$MIN' -fin '200000' > /dev/null"' >> $FILE_NAME
                fi
                COUNT=$(( $COUNT + 1 ))
        done
        #echo "All new files created!"
}

# ###################################
# purge log file if size > 100 Mo
# ##################################
function ManageLogFile(){
	size=$(wc -c ${LOG_FILE} | awk '{print $1}')
        RoundSize="$((${size}/1024/1024))"
        echo "Log file size : $RoundSize Mo"

        if [ $RoundSize -ge 100 ];then
                rm -f ${LOG_FILE}
        fi
}

# ###################################
# Send specific mail function
# ##################################
function SendMail(){
	declare -A Object
	Object["info"]="info: script de regénération des analyseurs d'alertes"
	Object["critical"]="CRITICAL: script de regénération des analyseurs >> BLOCKED PROCESS FOUND !!"
	Object["start"]="Début d'exécution du script de regénération des analyseurs d'alertes"
	Object["end"]="Fin d'exécution du script de regénération des analyseurs d'alertes"
	Object["cp_rendu"]="Compte Rendu de l'exécution du script de regénération des analyseurs d'alertes"
	Object["error"]="Erreur: Echec d'exécution du script de regénération des analyseurs d'alertes"
	Source="`hostname`"
        #Destination="rbo@ip-label.com"
	Destination=$(cat ${PARAM_FILE} | grep "destinataire" | awk -F= '{ print $2}')
	#start_date="`date +"%d-%m-20%y %H:%M:%S"`"
	end_date="`date +"%d-%m-20%y %H:%M:%S"`"
	
	case "$1" in 
		start)	
			echo -e "Début de l'exécution du script à: "${start_date}"     \n1. nombre de moniteur géré par le dernier intervalle est: `cat $RESULT_FILE_2 `        \n2. résultat de la répartion des intervalles\n `cat ${RESULT_FILE_1}`  \nFin de l exécution du script à: "${end_date}"" | mailx -s "${Object["start"]}" -a ${LOG_FILE_TMP} -r ${Source} ${Destination}
		;;

		critical)
			echo -e "La list des process AnalyseCptRendu bloqués est:\n`ps -ef | grep AnalyseCptRendus | grep -v grep` \n" | mailx -s "${Object["critical"]}" -a ${LOG_FILE_TMP} -r ${Source} ${Destination}
		;;

		end)
			echo -e "Le compte rendu de l'execution du script est:\n" `cat ${LOG_FILE_TMP}` | mailx -s "${Object["end"]}" -a ${LOG_FILE_TMP}  -r ${Source} ${Destination}
		;;

		info)
			echo -e "pas besoin de regénérer les analyseurs d'alertes:\n * nombre de moniteur géré par le dernier AnalyseurCptRendu est : `cat $RESULT_FILE_2 ` 		valeur autorisée :   $nbr_moniteur_last_inter  " |  mailx -s "${Object["info"]}" -a ${LOG_FILE_TMP} -r ${Source} ${Destination}
		;;

		cp_rendu)
			 echo -e "Début de l'exécution du script à: "${start_date}"     \n\n1. nombre de moniteur géré par le dernier AnalyseurCptRendu  est: `cat $RESULT_FILE_2 `        \n2. résultat de la répartion des intervalles\n `cat ${RESULT_FILE_1}`  \n3. nombre de fichier analysecompterendu créé: 	"$(( $NBR_ANALYSER_RESULT_FILE - 1 ))"   \n\nFin de l exécution du script à: "${end_date}"" | mailx -s "${Object["cp_rendu"]}" -a ${LOG_FILE_TMP} -r ${Source} ${Destination}
		;;

		error)
			echo -e "Erreur: Le nombre de fichier AnalyseCptRendu à créer est Null :  $(( $NBR_ANALYSER_RESULT_FILE - 1))" | mailx -s "${Object["error"]}" -a ${LOG_FILE_TMP} -r ${Source} ${Destination}
		;;

		*)	
			echo "command: "$1" not found !" 
		;;
	esac	
	echo "SendMail status: $1 -> OK"
}

# ############################################
# Control AnalyseCptRendu Process [Stop|Start]
# ############################################
function ControlProcess(){
	case "$1" in 
	
		stop)
			COUNT=1;
			NBR_ANALYSER_FILE=$(ls -ltr  ${INIT_DIR}analysecompterendu* | wc -l)
			if [ ! $NBR_ANALYSER_FILE -eq 0 ];then
				while [ $COUNT -le $(($NBR_ANALYSER_FILE)) ];do
	        		        #echo "analysecompterendu$COUNT : stoped"
                	        	initctl stop analysecompterendu$COUNT
	                        	sleep 1
		                        #echo $COUNT
	        	                #echo "stop"
	                	        COUNT=$(( $COUNT + 1))
		                done
			else
				#echo "Génération des fichier AnalyseC"
                                NBR_ANALYSER_FILE_BACKUP_DIR=$(ls -ltr  ${BACKUP_DIR}init/analysecompterendu* | wc -l)
                                echo $NBR_ANALYSER_FILE_BACKUP_DIR
                                if [ ! $NBR_ANALYSER_FILE_BACKUP_DIR -eq 0 ];then
                                        echo "Recover analysecompterend*.conf from backup_dir -> /etc/init/"
                                        cp  ${BACKUP_DIR}init/analysecompterendu*.conf ${INIT_DIR}
					ControlProcess "stop"
                                else
                                        echo "First generation of analysecompterendu*.conf"
                                        InitAnalyseCptrenduFile
                                fi

			fi 
		;;

		start)
			COUNT=1
			#NBR_ANALYSER_FILE=$(ls -ltr  ${INIT_DIR}analysecompterendu* | wc -l)
			NBR_ANALYSER_RESULT_FILE=$(cat "${RESULT_FILE_1}" | wc -l)
			while [ $COUNT -le $(($NBR_ANALYSER_RESULT_FILE - 1)) ];do
                        	#echo "analysecompterendu$COUNT : started"
	                        initctl start analysecompterendu$COUNT
				sleep 1
        	                #echo $COUNT
                	        #echo "start"
                        	COUNT=$(( $COUNT + 1))
	                done		
		;;
	esac

}

# ############################################
# Manage AnalyseCptRendu Services [Stop|Start]
# ############################################
function InitCTLService(){
	COUNT=1
	if [ $1 = "stop" ];then 
		# stop AnalyseCptRendu process
		ControlProcess "stop"		

		# find and kill blocked process
		count=1
		while [ $count -le 5 ]; do
			
			blocked_process=$(ps -ef | grep AnalyseCptRendus | grep -v grep | wc -l)	
			block_process_pid=$(ps -ef | grep AnalyseCptRendus | grep -v grep  | awk '{ print $2 }')
			echo "blocked process: "$block_process_pid
			
			if [ $(($blocked_precess)) -gt 1 ];then
				echo "blocked process found !: "$blocked_precess
				killall AnalyseCptRendus
				echo "sleep 3 ..."
        	                sleep 3
				ControlProcess "stop"
			fi
			
			list_blocked_process_pid=$(echo $block_process_pid | wc -w)
			#echo $list_blocked_process_pid
			
			if [ $(($list_blocked_process_pid)) -gt 1 ];then 
				kill -9 $block_process_pid
				echo "sleep 3 ..."
	                        sleep 3
				ControlProcess "stop"
			fi
			
			sleep 1
			count=$(( $count + 1 ))
		done
			
		# Send Mail if there are any blocked AnalyseCptRendus process After (3 x 5 + ..) seconds
		if [ $(($list_blocked_process_pid)) -gt 1 ];then
		#if true;then
			SendMail "critical"
			echo " launch AnalyseCptRendu service stoped ....."
			InitCTLService "start"
			echo "Exiting program ..."
			sleep 3
			exit 0;
			
	        fi

	elif [ $1 = "start" ];then
		# start AnalyseCptRendu process
		ControlProcess "start"
	else
		echo "command: "$1" not found !"
	fi
}

# ######################
# Main program
# #####################

# defined variables
start_date="`date +"%d-%m-20%y %H:%M:%S"`"
INIT_DIR="/etc/init/"
BASE_DIR="/opt/iplabel/"
SCRIPT_DIR=${BASE_DIR}"script/"
LOG_DIR=${SCRIPT_DIR}"log/"
RESULT_DIR=${SCRIPT_DIR}"result/"
BACKUP_DIR=${SCRIPT_DIR}"backup/"
SQL_DIR=${SCRIPT_DIR}"sql/"
PARAM_DIR=${SCRIPT_DIR}"param/"

LOG_FILE=${SCRIPT_DIR}"log/AnalyseCptRendu.log"
LOG_FILE_TMP=${SCRIPT_DIR}"log/debug_tmp.log"
RESULT_FILE_1=${RESULT_DIR}"result.csv"
RESULT_FILE_2=${RESULT_DIR}"result2.csv"
QUERY_1=${SQL_DIR}"query.sql"
QUERY_2=${SQL_DIR}"query2.sql"
PARAM_FILE=${PARAM_DIR}"param.conf"

# change directory
#cd ${SCRIPT_DIR}
cd ${INIT_DIR}

# create directories if not exists
array=( "${SCRIPT_DIR}" "${RESULT_DIR}" "${LOG_DIR}" "${BACKUP_DIR}" "${SQL_DIR}" "${PARAM_DIR}" )
for dir in "${array[@]}"
do
        #echo $i
        if [ ! -d $dir ]; then
                mkdir -p $dir
                echo "directory ${dir} created"
	#else
	#	echo "dir $dir exist"
        fi
done

array_lo_file=( "${LOG_FILE}" "${LOG_FILE_TMP}" )
for log_file in "${array_log_file[@]}"
do
	# create log_file if not exist
	if [ ! -f $log_file ];then
        	touch $log_file
	        chmod 755 $log_file
	fi
done


# redirect output to LOG_FILE_TMP
#exec 3>&1 1>${LOG_FILE_TMP} 2>&1


echo " ---------------------------------------------------------------"
echo "|Start at: =>  `date`"						
echo " ---------------------------------------------------------------"

#echo "Execute AnalyseCptRendu_part1.sh"
#${SCRIPT_DIR}AnalyseCptRendu_part1.sh
#sleep 2
#echo "Execute AnalyseCptRendu_part2.sh"
#${SCRIPT_DIR}AnalyseCptRendu_part2.sh

echo "Create/Update SQL Files 1	: OK"
CreateSQLFile "REQ_1"
sleep 1
echo "Execute SQL Files 1 : OK"
ExecuteSQLFile "REQ_1"
sleep 2
echo "Create/Update SQL Files 2	: OK"
CreateSQLFile "REQ_2"
sleep 1
echo "Execute SQL Files 2 : OK"
ExecuteSQLFile "REQ_2"
sleep 2

# Get number off active monitors on last interval
NBR_ACTIVE_MONITORS=$(cat "${RESULT_FILE_2}")
#echo ${NBR_ACTIVE_MONITORS}
NBR_ANALYSER_RESULT_FILE=$(cat "${RESULT_FILE_1}" | wc -l)

if [ $(( $NBR_ANALYSER_RESULT_FILE -1 )) -le 0 ];then
	SendMail "error"
	exit 0
fi

NBR_ANALYSER_FILE=$(ls -ltr  ${INIT_DIR}analysecompterendu* | wc -l)
nbr_moniteur_last_inter=$(cat ${PARAM_DIR}param.conf | grep "last_interval_value" | awk -F= '{print $2}')

if [ ${NBR_ACTIVE_MONITORS} -ge $nbr_moniteur_last_inter ];then
	#echo -e "\n"
	#echo  " ------------------------------------------"
	#echo "| Send Mail befor generate AnalyseCptRendu |"
	#echo " ------------------------------------------"
        #SendMail "start"	
	
	sleep 3
	
	echo -e "\n"	
	echo " ----------------------" 
	echo "| initCTLService: stop |"	
	echo " ----------------------"
	InitCTLService "stop"	
	
	sleep 3

	echo -e "\n"
	echo " ------------------------------"
        echo "| Rebuild AnalyseCptRendu files |"
        echo " -------------------------------"
	InitAnalyseCptrenduFile
	
	sleep 3
	
	echo -e "\n"
	echo " ----------------------"
	echo "| initCTLService start |"
	echo " ----------------------"
	InitCTLService "start"

	echo -e "\n"
        echo  "------------------------------------------"
        echo "| Send Mail After generate AnalyseCptRendu |"
        echo " ------------------------------------------"
        SendMail "cp_rendu"
	
else
	echo "Pas besoin de lancer la regénération des AnalyserCptRendu"
	SendMail "info"
fi

#ManageLogFile

echo -e "\n"
echo " ----------------------------------------------------------------"
echo "|End with Success ! at:  =>  `date`"
echo " ----------------------------------------------------------------"

# write LOG_FILE_TMP >> LOG_FILE
# LOG_FILE is usualy all the time created with '>>'
cat ${LOG_FILE_TMP} >> ${LOG_FILE}

ManageLogFile

exit 1
