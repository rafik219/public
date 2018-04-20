/*==============================================================*/
/* Database name:  SITEAGENT                                    */
/* DBMS name:      ORACLE Version 9i                            */
/* Created on:     16/10/2003 09:36:31                          */
/*==============================================================*/



create or replace procedure MAJINTERNETTELECOM
IS
 Scenario VARCHAR2(4000);
 Today VARCHAR2(10);
 mylob CLOB;
 mSize INTEGER := 50000;
BEGIN
	SELECT PARAMETRESAPPLICATION INTO mylob FROM MISSION WHERE idmission=105546 FOR UPDATE;
	SELECT TO_CHAR(SYSDATE + 4/24, 'DDMMYYYY') INTO Today FROM dual;
	Scenario := '<?xml version=''1.0'' encoding=''ISO8859-1''?>'
		|| '<job version="2.0" loadsize="1" frequency="900">'
		|| '<transaction type="1">'
		|| '<request navigate="1" connectiontimeout="10000" objectdownloadtimeout="60000">'
		|| '<action name="navigate">'
		|| '<parameter name="url" value="http://cario.internet-telecom.net/getlogin.asp?ilogin=iplabel0006@ca.tst&amp;Passwd=monpwd&amp;nom= iplabel&amp;prenom=iplabel&amp;codemktg=testmktg&amp;telnum=0101010101&amp;CR=TST&amp;statut=G&amp;date='||Today||'"/>'
		|| '</action>'
		|| '<control name="connectioncontrol"/>'
		|| '<control name="pagedownloadcontrol"/>'
		|| '<measure name="dnstime" object="document"/>'
		|| '<measure name="connectiontime" object="document"/>'
		|| '<measure name="firstbytereception" object="document"/>'
		|| '<measure name="downloadtime" object="document"/>'
		|| '<measure name="objectsize" object="document"/>'
		|| '<measure name="requesttimeoffset" object="document"/>'
		|| '</request>'
		|| '</transaction>'
		|| '</job>';
	dbms_lob.erase(mylob, mSize , 1);
	dbms_lob.WRITE(mylob, LENGTH(Scenario), 1, Scenario);
	COMMIT;
		SELECT PARAMETRESAPPLICATION INTO mylob FROM MISSION WHERE idmission=110225 FOR UPDATE;
	SELECT TO_CHAR(SYSDATE + 4/24, 'DDMMYYYY') INTO Today FROM dual;
	Scenario := '<?xml version=''1.0'' encoding=''ISO8859-1''?>'
		|| '<job version="2.0" loadsize="1" frequency="900">'
		|| '<transaction type="1">'
		|| '<request navigate="1" connectiontimeout="10000" objectdownloadtimeout="60000">'
		|| '<action name="navigate">'
		|| '<parameter name="url" value="http://cario-ed.internet-telecom.net/getlogin_a.asp?ilogin=testit1509031@ca.tst&amp;nom=it&amp;prenom=it&amp;CR=tst&amp;telnum=0101010101&amp;passwd=tst&amp;statut=F&amp;date='||Today||'&amp;codemktg=tst"/>'
		|| '</action>'
		|| '<control name="connectioncontrol"/>'
		|| '<control name="pagedownloadcontrol"/>'
		|| '<measure name="dnstime" object="document"/>'
		|| '<measure name="connectiontime" object="document"/>'
		|| '<measure name="firstbytereception" object="document"/>'
		|| '<measure name="downloadtime" object="document"/>'
		|| '<measure name="objectsize" object="document"/>'
		|| '<measure name="requesttimeoffset" object="document"/>'
		|| '</request>'
		|| '</transaction>'
		|| '</job>';
	dbms_lob.erase(mylob, mSize , 1);
	dbms_lob.WRITE(mylob, LENGTH(Scenario), 1, Scenario);
	COMMIT;
END;
/


