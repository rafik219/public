/*==============================================================*/
/* Database name:  SITEAGENT                                    */
/* DBMS name:      ORACLE Version 9i                            */
/* Created on:     17/02/2006 13:24:16                          */
/*==============================================================*/


/*==============================================================*/
/* Index: IDX_MAINTENANCEMISSION                                */
/*==============================================================*/
create index IDX_MAINTENANCEMISSION on MAINTENANCEMISSION (
   IDMISSION ASC,
   DATEMAINTENANCE ASC
)
pctfree 2
tablespace I_DATA
/


/*==============================================================*/
/* Index: IDX_MISSION_TYPEAPP                                   */
/*==============================================================*/
create index IDX_MISSION_TYPEAPP on MISSION (
   TYPEAPPLICATION ASC
)
pctfree 2
tablespace I_DATA
/


/*==============================================================*/
/* Index: IDX_TACHEAGENT_IDAGENTSITE                            */
/*==============================================================*/
create index IDX_TACHEAGENT_IDAGENTSITE on TACHEAGENT (
   IDAGENTSITE ASC,
   ETATREALISATION ASC
)
pctfree 2
tablespace I_DATA
/


/*==============================================================*/
/* Index: IDX_TACHEAGENT_DATEREA                                */
/*==============================================================*/
create index IDX_TACHEAGENT_DATEREA on TACHEAGENT (
   DATEREALISATION ASC
)
pctfree 2
tablespace I_DATA
/


/*==============================================================*/
/* Index: IDX_TACHEAGENT_C_IDAGENTSITE                          */
/*==============================================================*/
create index IDX_TACHEAGENT_C_IDAGENTSITE on TACHEAGENT_CONNECT (
   IDAGENTSITE ASC,
   ETATREALISATION ASC
)
pctfree 2
tablespace I_DATA
/


/*==============================================================*/
/* Index: IDX_TACHEAGENT_C_DATEREA                              */
/*==============================================================*/
create index IDX_TACHEAGENT_C_DATEREA on TACHEAGENT_CONNECT (
   DATEREALISATION ASC
)
pctfree 2
tablespace I_DATA
/


