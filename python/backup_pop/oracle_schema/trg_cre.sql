/*==============================================================*/
/* Database name:  SITEAGENT                                    */
/* DBMS name:      ORACLE Version 9i                            */
/* Created on:     16/10/2003 09:35:15                          */
/*==============================================================*/


create or replace trigger TUPD_TACHEAGENT
BEFORE UPDATE of ETATREALISATION on TACHEAGENT
FOR EACH ROW
BEGIN
  IF :NEW.etatrealisation > 1 THEN
    :NEW.datetentative := SYSDATE;
  END IF;
END;
/


create or replace trigger TUPD_TACHEAGENT_CONNECT BEFORE
UPDATE of ETATREALISATION on TACHEAGENT_CONNECT
FOR EACH ROW
BEGIN
  IF :NEW.etatrealisation > 1 THEN
    :NEW.datetentative := SYSDATE;
  END IF;
END;
/


create or replace trigger VALEURMIB_TINS
BEFORE INSERT on VALEURMIB
FOR EACH ROW
  BEGIN SELECT valeurmib_SEQ.NEXTVAL INTO :NEW.idvaleurmib FROM DUAL;  
END valeurmib_TINS;
/

CREATE OR REPLACE TRIGGER Mission_TUPDATE
BEFORE UPDATE OF EtatMission ON Mission FOR EACH ROW 
BEGIN
  :NEW.ETATMISSIONSITE:=1-:NEW.EtatMission;
END;
/
