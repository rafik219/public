#!/bin/bash

usage() { echo "Usage: $0 base_config.conf" 1>&2; exit 1;}

validate_ip() {
        echo "Cheking IP Address format for: $1"
        if [[ $1 =~ ^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-99][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$ ]]; then
                echo -e "\t => OK"
        else
                echo "oops: Bad ip address '$i'"
                exit -1
        fi
}

getConfig() {

        if [ ! -f $1 ];then
                echo "File not found : $1"
                usage
        else
                CONFIG_FILE=$1
                HOSTNAMES=$(cat ${CONFIG_FILE} | grep "HOSTNAME" | awk -F= '{print $2}')
                IPADDRESS=$(cat ${CONFIG_FILE} | grep "IPADDRESS" | awk -F= '{print $2}')
                HWADDR=$(cat ${CONFIG_FILE} | grep "HWADDR" | awk -F= '{print $2}')
                MASK=$(cat ${CONFIG_FILE} | grep "MASK" | awk -F= '{print $2}')
                GATEWAY=$(cat ${CONFIG_FILE} | grep "GATEWAY" | awk -F= '{print $2}')
                DNS1=$(cat ${CONFIG_FILE} | grep "DNS1" | awk -F= '{print $2}')
                DNS2=$(cat ${CONFIG_FILE} | grep "DNS2" | awk -F= '{print $2}')
                IDSITE=$(cat ${CONFIG_FILE} | grep "IDSITE" | awk -F= '{print $2}')
                POPNAME=$(cat ${CONFIG_FILE} | grep "POPNAME" | awk -F= '{print $2}')
                SCHEMA=$(cat ${CONFIG_FILE} | grep "SCHEMA" | awk -F= '{print $2}')

                if [ -z "${HOSTNAMES}" ] || [ -z "${IPADDRESS}" ] || [ -z "${MASK}" ] || [ -z "${GATEWAY}" ]; then
                        usage
                else
                        validate_ip ${IPADDRESS}
                        validate_ip ${MASK}
                        validate_ip ${GATEWAY}
                fi

                if [ -z "${DNS1}" ]; then
                        DNS1="8.8.8.8"
                else
                        validate_ip ${DNS1}
                fi

                if [ -z "${DNS2}" ]; then
                        DNS2="8.8.4.4"
                else
                        validate_ip ${DNS2}
                fi
        fi
}

if [ $# -eq 0 ]; then
        echo "Need Parameters ...."
        usage
else

        echo "get Configuration from: $1 file"
        getConfig $1

fi

NETWORK_FILE="/etc/sysconfig/network"
NETWORK_SCRIPT_FILE="/etc/sysconfig/network-scripts/ifcfg-eth0"
HOST_FILE="/etc/hosts"
RESOLV_FILE="/etc/resolv.conf"

DBCONFIG="/home/dist/DBconfig.conf"
DBCONFIG_CONTENT=$(cat ${DBCONFIG})

echo "${IDSITE}:${POPNAME}:${SCHEMA}" > ${DBCONFIG}


#if [ -z $DBCONFIG_CONTENT ];then
#        echo "0/ configure DBconfig.conf"
#        echo "${IDSITE}:${POPNAME}:${SCHEMA}" > ${DBCONFIG}
#fi

echo "1/ Network interface configuration: ${NETWORK_SCRIPT_FILE}"
if [ ! -z ${HWADDR} ];then
        sed -i "s|^\(HWADDR=\).*|\1${HWADDR}|g" ${NETWORK_SCRIPT_FILE}
        echo "HWADDR=${HWADDR}"
fi

BOOTPROTO_STATIC="STATIC"
sed -i "s|^\(BOOTPROTO=\).*|\1${BOOTPROTO_STATIC}|g" ${NETWORK_SCRIPT_FILE}

FIND_IPADDR=$(grep "IPADDR" ${NETWORK_SCRIPT_FILE})
if [ -z ${FIND_IPADDR} ];then
        echo "IPADDR=${IPADDRESS}" >> ${NETWORK_SCRIPT_FILE}
else
        sed -i "s|^\(IPADDR=\).*|\1${IPADDRESS}|g" ${NETWORK_SCRIPT_FILE}
fi

FIND_MASK=$(grep "NETMASK" ${NETWORK_SCRIPT_FILE})
if [ -z ${FIND_MASK} ];then
        echo "NETMASK=${MASK}" >> ${NETWORK_SCRIPT_FILE}
else
        sed -i "s|^\(NETMASK=\).*|\1${MASK}|g" ${NETWORK_SCRIPT_FILE}
fi
echo "IPADDR=${IPADDRESS}"
echo "NETMASK=${MASK}"


echo "2/ Gateway configuration: ${NETWORK_FILE}"
sed -i "s|^\(HOSTNAME=\).*|\1${HOSTNAMES}|g" ${NETWORK_FILE}
sed -i "s|^\(GATEWAY=\).*|\1${GATEWAY}|g" ${NETWORK_FILE}
echo "HOSTNAME=${HOSTNAMES}"
echo "GATEWAY=${GATEWAY}"

echo "3/ Hosts configuration: ${HOST_FILE}"
echo "127.0.0.1 localhost"                                              > ${HOST_FILE}
echo "${IPADDRESS}      ${HOSTNAMES}.ip-label.com       ${HOSTNAMES}"   >> ${HOST_FILE}
echo "${GATEWAY}        gateway"                                        >> ${HOST_FILE}
cat ${HOST_FILE}



echo "4/ DNS resolever configuration: ${RESOLV_FILE}"
echo "" > ${RESOLV_FILE}
echo "- Set new value"
echo "nameserver ${DNS1}" >> ${RESOLV_FILE}
echo "nameserver ${DNS2}" >> ${RESOLV_FILE}
cat ${RESOLV_FILE}

echo "4.1/ Oracle listener configuration:"
ARCH=`uname -p`
RELEASE=`cat /etc/redhat-release | awk '{print $3}' | cut -d '.' -f 1`
if [ $RELEASE == "5" ];then
        ORACLE_LISTENER="/usr/lib/oracle/xe/app/oracle/product/10.2.0/server/network/admin/listener.ora"
        ORACLE_TNS="/usr/lib/oracle/xe/app/oracle/product/10.2.0/server/network/admin/tnsnames.ora"
        sed -i "s|\(HOST = \).*|\1${IPADDRESS})(PORT=1521))|g" ${ORACLE_TNS}
        sed -i "s|\(HOST=\).*|\1${IPADDRESS})(PORT=1521))|g" ${ORACLE_TNS}
        ORACLE_TNS="/opt/oracle/product/9.2.0/network/admin/tnsnames.ora"
fi

if [ $RELEASE == "6" ];then
        ORACLE_LISTENER="/u01/app/oracle/product/11.2.0/xe/network/admin/listener.ora"
        ORACLE_TNS="/u01/app/oracle/product/11.2.0/xe/network/admin/tnsnames.ora"
fi

# change ip on listner.ora and tnsname.ora
sed -i "s|\(HOST = \).*|\1${IPADDRESS})(PORT=1521))|g" ${ORACLE_LISTENER}
sed -i "s|\(HOST=\).*|\1${IPADDRESS})(PORT=1521))|g" ${ORACLE_LISTENER}

sed -i "s|\(HOST = \).*|\1${IPADDRESS})(PORT=1521))|g" ${ORACLE_TNS}
sed -i "s|\(HOST=\).*|\1${IPADDRESS})(PORT=1521))|g" ${ORACLE_TNS}


# change hostname
OLD_HOSTNAME=`hostname`
sed -i "s/${OLD_HOSTNAME}/${HOSTNAMES}/g" ${ORACLE_TNS}

echo "5/ ifdown/ifup Network interface: ${NETWORK_SCRIPT_FILE}"
ifdown ${NETWORK_SCRIPT_FILE}
ifup ${NETWORK_SCRIPT_FILE}

sleep 5
/etc/init.d/network restart


sleep 5
echo "Restart oracle instance : "
/etc/init.d/oracle-xe restart


echo "SUCCESS !!"
