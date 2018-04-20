/*==============================================================*/
/* Database name:  SITEAGENT                                    */
/* DBMS name:      ORACLE Version 9i                            */
/* Created on:     16/10/2003 09:37:15                          */
/* Modifie le:     18/09/2007 15:29:20                          */
/* Procedure de ConsoALL des Mesures                            */
/*==============================================================*/


/*==============================================================*/
/* Database package: TACHES                                     */
/*==============================================================*/
create or replace package TACHES as
   procedure SUPPRESSIONTACHE;
end TACHES;
/


create or replace package body TACHES as
   procedure SUPPRESSIONTACHE as
   BEGIN

   DELETE FROM TACHEAGENT WHERE daterealisation < SYSDATE - (6/24);
   DELETE FROM TACHEAGENT_CONNECT WHERE daterealisation < SYSDATE -1 ;
   DELETE FROM MISSION WHERE etatmission = 1;
   COMMIT;
   END;
end TACHES;
/


/*==============================================================*/
/* Database package: ConsoALL                                     */
/*==============================================================*/

CREATE OR REPLACE PACKAGE APP_CONSO_EXPLOIT AS
 
   PROCEDURE   ConsoTacheTA(Typeappli   number);
   PROCEDURE ConsoTache;
  PROCEDURE ConsoTacheALLTA;
  
     PROCEDURE   ConsoTache_ConnectTA(Typeappli   number);
   PROCEDURE ConsoTache_Connect;
  PROCEDURE ConsoTache_ConnectALLTA;
  Procedure DerniereTache_Connect(Typeappli  number);
   
   PROCEDURE   ConsoMissionTA(Typeappli   number);
   PROCEDURE ConsoMission;
  PROCEDURE ConsoMissionALLTA;
  
  PROCEDURE DerniereTacheALLTA;
  PROCEDURE  DerniereTache(Typeappli   number);
  PROCEDURE DerniereTache_ConnectALLTA;
  
  
   PROCEDURE ConsoALL ;
 
END APP_CONSO_EXPLOIT;
/

CREATE OR REPLACE PACKAGE BODY APP_CONSO_EXPLOIT  IS
 
 --- CONSOLIDATION DES TACHEAGENT ----------------
 --- type applicattion inféeur à0000
 
 
   PROCEDURE ConsoTacheALLTA  IS
 --- Puis par Type applications
 CURSOR var_cur IS
   Select distinct typeapplication  from mission where typemodem=-1;
     BEGIN
  FOR var_rec IN var_cur LOOP
       ConsoTacheTA(var_rec.typeapplication);
     END LOOP;
    END ConsoTacheALLTA;
 
 PROCEDURE   ConsoTacheTA(Typeappli   number)  IS
 datemax date;
 datemin date;
 --typeapplication number;
 idmission number;
 donnee number;
 valeur number;
  idsite number;
  statei number;
 BEGIN
 select trunc(sysdate,'HH') into datemax  from dual;
 select trunc(sysdate -1/24,'HH') into datemin  from dual;
  select valeur into idsite from parametresapplication where nomapplication like 'IPLABEL' and parametre like 'IDSITE';
 select count(*) into valeur from tacheagent where datefin < =  datemax and daterealisation > = datemin and idagentsite= Typeappli;
 insert into Exploit (DATECONSO,TYPEAPPLICATION,IDMISSION,DONNEE,VALEUR,IDSITE,DONNEEMESURE) values ( datemax, Typeappli,'',4, valeur,idsite,'');
 FOR  state in 0..3 LOOP
 
 select count(*) into valeur from tacheagent where etatrealisation= state and datefin <= datemax and daterealisation > =  datemin and idagentsite= Typeappli;
 insert into Exploit (DATECONSO,TYPEAPPLICATION,IDMISSION,DONNEE,VALEUR,IDSITE,DONNEEMESURE) values ( datemax, Typeappli,'', state , valeur,idsite,'');
 
 END LOOP;
 END ConsoTacheTA;
 
 
   PROCEDURE ConsoTache  IS
 datemax date;
 datemin date;
 --typeapplication number;
 idmission number;
 donnee number;
 valeur number;
 idsite number;
 BEGIN
 select trunc(sysdate,'HH') into datemax  from dual;
 select trunc(sysdate -1/24,'HH') into datemin  from dual;
 select valeur into idsite from parametresapplication where nomapplication like 'IPLABEL' and parametre like 'IDSITE';
 select count(*) into valeur from tacheagent where datefin < = datemax and daterealisation > = datemin  ;
 insert into Exploit (DATECONSO,TYPEAPPLICATION,IDMISSION,DONNEE,VALEUR,IDSITE,DONNEEMESURE) values ( datemax, '','',4, valeur,idsite,'');
 FOR  state in 0..3 LOOP
 select count(*) into valeur from tacheagent where etatrealisation= state and datefin < = datemax and daterealisation > = datemin ;
 insert into Exploit (DATECONSO,TYPEAPPLICATION,IDMISSION,DONNEE,VALEUR,IDSITE,DONNEEMESURE) values ( datemax, '','', state, valeur,idsite,''); 
 END LOOP;
 END ConsoTache;
 
  --- CONSOLIDATION DES TACHEAGENT_CONNECT ----------------
 --- type applicattion supéeur à0000
 
 
  PROCEDURE ConsoTache_Connect  IS
 datemax date;
 datemin date;
 --typeapplication number;
 idmission number;
 donnee number;
 valeur number;
 idsite number;
 statei number;
 BEGIN
 select trunc(sysdate,'HH') into datemax  from dual;
 select trunc(sysdate -1/24,'HH') into datemin  from dual;
 select valeur into idsite from parametresapplication where nomapplication like 'IPLABEL' and parametre like 'IDSITE';
 select count(*) into valeur from tacheagent_connect where datefin < = datemax and daterealisation > = datemin  ;
 insert into Exploit (DATECONSO,TYPEAPPLICATION,IDMISSION,DONNEE,VALEUR,IDSITE,DONNEEMESURE) values ( datemax, '','',9, valeur,idsite,'');
 FOR  state in 0..3 LOOP
 statei := 5+ state;
 select count(*) into valeur from tacheagent_connect where etatrealisation= state and datefin < = datemax and daterealisation > = datemin ;
 insert into Exploit (DATECONSO,TYPEAPPLICATION,IDMISSION,DONNEE,VALEUR,IDSITE,DONNEEMESURE) values ( datemax, '','', statei, valeur,idsite,''); 
 END LOOP;
 END ConsoTache_Connect;
 
  PROCEDURE   ConsoTache_ConnectTA(Typeappli   number)  IS
 datemax date;
 datemin date;
 --typeapplication number;
 idmission number;
 donnee number;
 valeur number;
  idsite number;
  statei number;
 BEGIN
 select trunc(sysdate,'HH') into datemax  from dual;
 select trunc(sysdate -1/24,'HH') into datemin  from dual;
  select valeur into idsite from parametresapplication where nomapplication like 'IPLABEL' and parametre like 'IDSITE';
 select count(*) into valeur from tacheagent_connect where datefin < =  datemax and daterealisation > = datemin and idagentsite= Typeappli;
 insert into Exploit (DATECONSO,TYPEAPPLICATION,IDMISSION,DONNEE,VALEUR,IDSITE,DONNEEMESURE) values ( datemax, Typeappli,'',9, valeur,idsite,'');
 FOR  state in 0..3 LOOP
  statei := 5+ state;
 select count(*) into valeur from tacheagent_connect where etatrealisation= state and datefin <= datemax and daterealisation > =  datemin and idagentsite= Typeappli;
 insert into Exploit (DATECONSO,TYPEAPPLICATION,IDMISSION,DONNEE,VALEUR,IDSITE,DONNEEMESURE) values ( datemax, Typeappli,'', statei, valeur,idsite,'');
 
 END LOOP;
 END ConsoTache_ConnectTA;
 
 PROCEDURE ConsoTache_ConnectALLTA  IS
 --- Puis par Type applications
 CURSOR var_cur IS
   Select distinct typeapplication  from mission where typemodem<>-1;
     BEGIN
  FOR var_rec IN var_cur LOOP
       ConsoTache_ConnectTA(var_rec.typeapplication);
     END LOOP;
 END ConsoTache_ConnectALLTA;
	
 
 
   --- CONSOLIDATION DES MISSIONS ----------------
 --- type applicattion  
 
 
 PROCEDURE   ConsoMissionTA(Typeappli   number)  IS
 datemax date;
 datemin date;
 --typeapplication number;
 idmission number;
 donnee number;
 valeur number;
  idsite number;
 BEGIN
 select trunc(sysdate,'HH') into datemax  from dual;
 select trunc(sysdate -1/24,'HH') into datemin  from dual;
  select valeur into idsite from parametresapplication where nomapplication like 'IPLABEL' and parametre like 'IDSITE';
 select count(*) into valeur from mission where typeapplication=Typeappli ;
 insert into Exploit (DATECONSO,TYPEAPPLICATION,IDMISSION,DONNEE,VALEUR,IDSITE,DONNEEMESURE) values ( datemax, Typeappli,'',10, valeur,idsite,''); 
 END ConsoMissionTA;
 
 PROCEDURE ConsoMission  IS
 datemax date;
 datemin date;
 --typeapplication number;
 idmission number;
 donnee number;
 valeur number;
 idsite number;
 BEGIN
 select trunc(sysdate,'HH') into datemax  from dual; 
 select valeur into idsite from parametresapplication where nomapplication like 'IPLABEL' and parametre like 'IDSITE';
 select count(*) into valeur from mission ;
  insert into Exploit (DATECONSO,TYPEAPPLICATION,IDMISSION,DONNEE,VALEUR,IDSITE,DONNEEMESURE) values ( datemax, '','',10, valeur,idsite,'');
 END ConsoMission;
   
 PROCEDURE ConsoMissionALLTA  IS
 --- Puis par Type applications
 CURSOR var_cur IS
   Select distinct (typeapplication)  from mission ;
     BEGIN
  FOR var_rec IN var_cur LOOP
       ConsoMissionTA(var_rec.typeapplication);
     END LOOP;
 END ConsoMissionALLTA;
 
 
 
--- CONSOLIDATION HEURE DES DERNIERES TACHES  ----------------
 --- type applicattion  
 
 
 Procedure DerniereTache(Typeappli  number) is
  datemax date;
 datemin date;
  valeur number;
  idsite number;
  BEGIN
  select trunc(sysdate,'HH') into datemax  from dual;
 
 select valeur into idsite from parametresapplication where nomapplication like 'IPLABEL' and parametre like 'IDSITE';
 select to_char(max(datetentative),'HH24MISS') into valeur from tacheagent where datefin = datemax and idmission in ( select idmission from mission where frequence in (select max(frequence) from mission where typeapplication=Typeappli) and typeapplication = Typeappli);    
  IF valeur is null then
  valeur := 0;
  end if;
  
  insert into Exploit (DATECONSO,TYPEAPPLICATION,IDMISSION,DONNEE,VALEUR,IDSITE,DONNEEMESURE) values ( datemax, Typeappli,'',11, valeur,idsite,''); 
 END DerniereTache;
 
  Procedure DerniereTache_Connect(Typeappli  number) is
  datemax date;
 datemin date;
  valeur number;
  idsite number;
  BEGIN
  select trunc(sysdate,'HH') into datemax  from dual;
 
 select valeur into idsite from parametresapplication where nomapplication like 'IPLABEL' and parametre like 'IDSITE';
 select to_char(max(datetentative),'HH24MISS') into valeur from tacheagent_connect where datefin = datemax and idmission in ( select idmission from mission where frequence in (select max(frequence) from mission where typeapplication=Typeappli) and typeapplication = Typeappli);    
  IF valeur is null then
  valeur := 0;
  end if;
  
  insert into Exploit (DATECONSO,TYPEAPPLICATION,IDMISSION,DONNEE,VALEUR,IDSITE,DONNEEMESURE) values ( datemax, Typeappli,'',11, valeur,idsite,''); 
 END DerniereTache_Connect;
 
 
 	
	   PROCEDURE DerniereTacheALLTA  IS
 --- Puis par Type applications
 CURSOR var_cur IS
   Select distinct typeapplication  from mission where  typemodem=-1;
     BEGIN
  FOR var_rec IN var_cur LOOP
       DerniereTache(var_rec.typeapplication);
     END LOOP;
	 END DerniereTacheALLTA;
	 
	 PROCEDURE DerniereTache_ConnectALLTA  IS
	  CURSOR var_cur2 IS
   Select distinct typeapplication  from mission where typemodem<>-1;
     BEGIN
  FOR var_rec IN var_cur2 LOOP
       DerniereTache_Connect(var_rec.typeapplication);
     END LOOP;
    END DerniereTache_ConnectALLTA;
 
 
 PROCEDURE ConsoALL   IS
 --- Puis par Type applications
 Begin
 
 ConsoTache();
 ConsoTacheALLTA();
  ConsoMission();
 ConsoMissionALLTA();
 DerniereTacheALLTA();
 ConsoTache_ConnectALLTA();
 DerniereTache_ConnectALLTA();
 END ConsoALL;
 
 
   
 END APP_CONSO_EXPLOIT;
/
