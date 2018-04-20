#!/bin/bash

usage(){ echo "Usage: $0 -u USERNAME" 1>&2; exit 1; }

while getopts ":u:" o; do
    case "${o}" in
        u)
            user=${OPTARG}
            ;;
    esac
done

shift $((OPTIND-1))

if [ -z ${user} ]; then
        usage
fi


echo "=============== CREATE ROLE: IPLABEL ============="

sqlplus /nolog @/opt/iplabel/backup_restore_db/oracle_schema/role_cre.sql

echo "=============== CREATE DATAPUMP DIRECTORY ======================="

dmpdir='/home/oracle/dmpdir'

if [ ! -d ${dmpdir} ];then
	su - oracle -c 'mkdir ${dmpdir}'
fi

echo "=============== CREATE USER: ${user} ==================="

sqlplus /nolog @/opt/iplabel/backup_restore_db/oracle_schema/users_cre10g.sql ${user}

echo "=============== INSERT VALUE ======================"

sqlplus ${user}/XXXXXX @/opt/iplabel/backup_restore_db/oracle_schema/obj_cre.sql



exit 0
