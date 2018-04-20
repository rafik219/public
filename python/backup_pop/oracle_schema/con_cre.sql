/*==============================================================*/
/* Database name:  SITEAGENT                                    */
/* DBMS name:      ORACLE Version 9i                            */
/* Created on:     27/10/2005 07:32:44                          */
/*==============================================================*/


alter table ANOMALIES
   add constraint FK_ANOMALIES_MIS04 foreign key (IDMISSION)
      references MISSION (IDMISSION)
        disable novalidate
/


alter table DATETIMEZONE
   add constraint FK_DATETIMEZONE_TZ01 foreign key (IDTIMEZONE)
      references TIMEZONE (IDTIMEZONE)
/


alter table ESSAITRACEROUTE
   add constraint FK_ESSAITRACEROUTE_MIS03 foreign key (IDMISSION)
      references MISSION (IDMISSION)
        disable novalidate
/


alter table ESSAITRACEROUTEPANEL
   add constraint FK_ESSAITRACEROUTE_MIS15 foreign key (IDMISSION)
      references MISSION (IDMISSION)
        disable novalidate
/


alter table INCIDENTMISSION
   add constraint FK_INCIDENTMISSION_MIS02 foreign key (IDMISSION)
      references MISSION (IDMISSION)
        disable novalidate
/


alter table MAINTENANCEMISSION
   add constraint FK_MAINTENANCEMISS_MIS09 foreign key (IDMISSION)
      references MISSION (IDMISSION)
      on delete cascade
/


alter table MESUREOBJET
   add constraint FK_MESUREOBJET_MIS12 foreign key (IDMISSION)
      references MISSION (IDMISSION)
        disable novalidate
/


alter table MESUREPING
   add constraint FK_MESUREPING_MIS05 foreign key (IDMISSION)
      references MISSION (IDMISSION)
        disable novalidate
/


alter table MESURERETOURMESSAGE
   add constraint FK_MESURERETOURMES_MIS06 foreign key (IDMISSION)
      references MISSION (IDMISSION)
        disable novalidate
/


alter table MESURES
   add constraint FK_MESURES_MIS10 foreign key (IDMISSION)
      references MISSION (IDMISSION)
        disable novalidate
/


alter table MESURETRACEROUTE
   add constraint FK_MESURETRACEROUT_MIS08 foreign key (IDMISSION)
      references MISSION (IDMISSION)
        disable novalidate
/


alter table MESURETRACEROUTEPANEL
   add constraint FK_MESURETRACEROUT_MIS14 foreign key (IDMISSION)
      references MISSION (IDMISSION)
        disable novalidate
/


alter table TRACEESSAI
   add constraint FK_TRACEESSAI_MIS13 foreign key (IDMISSION)
      references MISSION (IDMISSION)
        disable novalidate
/


alter table VALEURMIB
   add constraint FK_VALEURMIB_MIS11 foreign key (IDMISSION)
      references MISSION (IDMISSION)
/


