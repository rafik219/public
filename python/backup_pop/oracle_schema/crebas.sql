/*==============================================================*/
/* Database name:  SITEAGENT                                    */
/* DBMS name:      ORACLE Version 9i                            */
/* Created on:     19/02/2004 10:04:37                          */
/*==============================================================*/


/*==============================================================*/
/* Table: AGENTSITE                                             */
/*==============================================================*/


create table AGENTSITE  (
   IDAGENTSITE          NUMBER(5)                        not null,
   NOMMACHINE           VARCHAR2(255),
   CAPACITEMAX          NUMBER(5),
   CAPACITEUTILISEE     NUMBER(5),
   TYPEAPPLICATION      NUMBER(5)
)
TABLESPACE D_DATA
PCTFREE 5
PCTUSED 80
/


/*==============================================================*/
/* Table: ANOMALIES                                             */
/*==============================================================*/


create table ANOMALIES  (
   IDMISSION            NUMBER(15),
   DATEESSAI            DATE                             not null,
   REQUETE              NUMBER(2)                        not null,
   TYPEANOMALIE         NUMBER(3)                        not null,
   CODEANOMALIE         NUMBER(3)                        not null,
   MESSAGE              VARCHAR2(255),
   DATEMESURE           DATE,
   ETATTRANSFERT        NUMBER(1)                      default 0
)
TABLESPACE D_DATA
PCTFREE 5
PCTUSED 80
/


/*==============================================================*/
/* Table: ESSAITRACEROUTE                                       */
/*==============================================================*/


create table ESSAITRACEROUTE  (
   IDMISSION            NUMBER(15)                       not null,
   DATEESSAI            DATE                             not null,
   CHECKSUM             NUMBER(15)                       not null,
   NBESSAIS             NUMBER(2)                        not null,
   ETATTRANSFERT        NUMBER(1)                      default 0  not null
)
TABLESPACE D_DATA
PCTFREE 5
PCTUSED 80
/


/*==============================================================*/
/* Table: ESSAITRACEROUTEPANEL                                  */
/*==============================================================*/


create table ESSAITRACEROUTEPANEL  (
   IDMISSION            NUMBER(15)                       not null,
   DATEESSAI            DATE                             not null,
   REQUETE              NUMBER(3)                        not null,
   TYPEREQUETE          NUMBER(3)                        not null,
   CHECKSUM             NUMBER(15)                       not null,
   NBESSAIS             NUMBER(2)                        not null,
   ETATTRANSFERT        NUMBER(1)                      default 0  not null
)
/


/*==============================================================*/
/* Table: HEURESMAINTIEN                                        */
/*==============================================================*/


create table HEURESMAINTIEN  (
   HEURE                NUMBER(2)                        not null
)
organization
    index
         pctfree 5
         tablespace D_DATA
/


alter table HEURESMAINTIEN
   add constraint PK_HEURESMAINTIEN primary key (HEURE)
/


/*==============================================================*/
/* Table: INCIDENTMISSION                                       */
/*==============================================================*/


create table INCIDENTMISSION  (
   IDINCIDENTMISSION    INTEGER,
   IDMISSION            NUMBER(15),
   DATEINCIDENT         DATE,
   TYPEINCIDENT         NUMBER(2),
   DESCRIPTIONINCIDENT  VARCHAR2(255),
   ETATTRANSFERT        NUMBER(1)                      default 0
)
TABLESPACE D_DATA
PCTFREE 5
PCTUSED 80
/


/*==============================================================*/
/* Table: INCIDENTSITE                                          */
/*==============================================================*/


create table INCIDENTSITE  (
   IDINCIDENTSITE       INTEGER                          not null,
   DATEINCIDENT         DATE,
   TYPEINCIDENT         NUMBER(2),
   DESCRIPTIONINCIDENT  VARCHAR2(255),
   ETATTRANSFERT        NUMBER(1)                      default 0
)
TABLESPACE D_DATA
PCTFREE 5
PCTUSED 80
/


/*==============================================================*/
/* Table: LIENAGENTMISSION                                      */
/*==============================================================*/


create table LIENAGENTMISSION  (
   IDMISSION            NUMBER(15)                       not null,
   IDAGENTSITE          NUMBER(5)                        not null
)
organization
    index
         pctfree 5
         tablespace D_DATA
/


alter table LIENAGENTMISSION
   add constraint PK_LIENAGENTMISSION primary key (IDMISSION, IDAGENTSITE)
/


/*==============================================================*/
/* Table: MAINTENANCE                                           */
/*==============================================================*/


create table MAINTENANCE  (
   DATEDEBUT            DATE                             not null,
   DATEFIN              DATE                             not null
)
TABLESPACE D_DATA
PCTFREE 5
PCTUSED 80
/


/*==============================================================*/
/* Table: MAINTENANCEMISSION                                    */
/*==============================================================*/


create table MAINTENANCEMISSION  (
   IDMISSION            NUMBER(15),
   DATEMAINTENANCE      DATE                             not null,
   DUREE                NUMBER(7)                        not null,
   TYPEMAINTENANCE      NUMBER(1)                        not null,
   IDMAINTENANCECONTRAT NUMBER(5)
)
TABLESPACE D_DATA
PCTFREE 5
PCTUSED 80
/


/*==============================================================*/
/* Table: MESUREOBJET                                           */
/*==============================================================*/


create table MESUREOBJET  (
   IDMISSION            NUMBER(15)                       not null,
   DATEESSAI            DATE                             not null,
   OBJETMESURE          VARCHAR2(255)                    not null,
   REQUETE              NUMBER(2)                        not null,
   TPSDNS               NUMBER(5)                        not null,
   TPSCONNEXION         NUMBER(5)                        not null,
   TPSOCTET             NUMBER(5)                        not null,
   TPSOBJET             NUMBER(6)                        not null,
   TAILLEOBJET          NUMBER(8)                        not null,
   ETATTRANSFERT        NUMBER(1)                      default 0  not null
)
TABLESPACE D_DATA
PCTFREE 5
PCTUSED 80
/


/*==============================================================*/
/* Table: MESUREPING                                            */
/*==============================================================*/


create table MESUREPING  (
   IDMISSION            NUMBER(15)                       not null,
   DATEESSAI            DATE                             not null,
   ADRESSE              NUMBER(10)                       not null,
   TEMPSMIN             NUMBER(5)                        not null,
   TEMPSMAX             NUMBER(5)                        not null,
   TEMPSMOYEN           NUMBER(5)                        not null,
   NBERREURS            NUMBER(2)                        not null,
   NBESSAIS             NUMBER(2),
   ETATTRANSFERT        NUMBER(1)                      default 0  not null
)
TABLESPACE D_DATA
PCTFREE 5
PCTUSED 80
/


/*==============================================================*/
/* Table: MESURERETOURMESSAGE                                   */
/*==============================================================*/


create table MESURERETOURMESSAGE  (
   IDMISSION            NUMBER(15)                       not null,
   DATEESSAI            DATE,
   NUMERONOEUD          NUMBER(2)                        not null,
   OBJETMESURE          VARCHAR2(255)                    not null,
   TPSDELAI             NUMBER(6),
   ETATTRANSFERT        NUMBER(1)                      default 0
)
TABLESPACE D_DATA
PCTFREE 5
PCTUSED 80
/


/*==============================================================*/
/* Table: MESURES                                               */
/*==============================================================*/


create table MESURES  (
   IDMISSION            NUMBER(15),
   DATEESSAI            DATE,
   DATEMESURE           DATE,
   REQUETE              NUMBER(2)                        not null,
   OBJETMESURE          VARCHAR2(255),
   DONNEEMESURE         NUMBER(10)                       not null,
   VALEURMESURE         NUMBER(10)                       not null,
   ETATTRANSFERT        NUMBER(1)
)
TABLESPACE D_DATA
PCTFREE 5
PCTUSED 80
/


/*==============================================================*/
/* Table: MESURETRACEROUTE                                      */
/*==============================================================*/


create table MESURETRACEROUTE  (
   IDMISSION            NUMBER(15)                       not null,
   DATEESSAI            DATE                             not null,
   ETAPE                NUMBER(2)                        not null,
   ADRESSE              VARCHAR2(200),
   ADRESSEIP            NUMBER(10)                       not null,
   ASNUMBER             NUMBER(1)                      default 0,
   TEMPSMIN             NUMBER(5)                        not null,
   TEMPSMAX             NUMBER(5)                        not null,
   TEMPSMOYEN           NUMBER(5)                        not null,
   NBERREURS            NUMBER(2),
   ETATTRANSFERT        NUMBER(1)                      default 0  not null
)
TABLESPACE D_DATA
PCTFREE 5
PCTUSED 80
/


/*==============================================================*/
/* Table: MESURETRACEROUTEPANEL                                 */
/*==============================================================*/


create table MESURETRACEROUTEPANEL  (
   IDMISSION            NUMBER(15)                       not null,
   DATEESSAI            DATE                             not null,
   REQUETE              NUMBER(3)                        not null,
   TYPEREQUETE          NUMBER(3)                        not null,
   ETAPE                NUMBER(2)                        not null,
   ADRESSEIP            NUMBER(15)                       not null,
   ASNUMBER             NUMBER(1),
   TEMPSMIN             NUMBER(5)                        not null,
   TEMPSMAX             NUMBER(5)                        not null,
   TEMPSMOYEN           NUMBER(5)                        not null,
   NBERREURS            NUMBER(2),
   ETATTRANSFERT        NUMBER(1)                      default 0  not null
)
/


/*==============================================================*/
/* Table: MISSION                                               */
/*==============================================================*/


create table MISSION  (
   IDMISSION            NUMBER(15)                       not null,
   DEBUTMISSION         DATE                             not null,
   FINMISSION           DATE,
   ETATMISSIONSITE      NUMBER(1)                      default 0  not null,
   ETATMISSION          NUMBER(1),
   TYPEAPPLICATION      NUMBER(5),
   COUT                 NUMBER(1),
   DERNIERETACHE        DATE,
   IDCOMMUNICATION      NUMBER(5),
   PARAMETRESAPPLICATION CLOB
)
TABLESPACE D_DATA
PCTFREE 5
PCTUSED 80
 LOB (PARAMETRESAPPLICATION) STORE AS 
      ( TABLESPACE  D_DATA
        ENABLE      STORAGE IN ROW
        CHUNK       8192
        PCTVERSION  10
      )
/


alter table MISSION
   add constraint PK_MISSION primary key (IDMISSION)
      using index
    pctfree 2
    tablespace I_DATA
/


/*==============================================================*/
/* Table: PARAMETRESAPPLICATION                                 */
/*==============================================================*/


create table PARAMETRESAPPLICATION  (
   NOMAPPLICATION       VARCHAR2(255)                    not null,
   PARAMETRE            VARCHAR2(255)                    not null,
   VALEUR               VARCHAR2(255)
)
TABLESPACE D_DATA
PCTFREE 5
PCTUSED 80
/


alter table PARAMETRESAPPLICATION
   add constraint PK_PARAMETRESAPPLICATION primary key (NOMAPPLICATION, PARAMETRE)
      using index
    pctfree 2
    tablespace I_DATA
/


/*==============================================================*/
/* Table: TACHEAGENT                                            */
/*==============================================================*/


create table TACHEAGENT  (
   IDMISSION            NUMBER(15),
   IDAGENTSITE          NUMBER(5),
   DATEREALISATION      DATE,
   DATEFIN              DATE,
   ETATREALISATION      NUMBER(1),
   TENTATIVE            NUMBER(2)                      default 1,
   DATETENTATIVE        DATE
)
TABLESPACE D_DATA
PCTFREE 5
PCTUSED 80
/


/*==============================================================*/
/* Index: IDX_TACHEAGENT_IDMISSION                              */
/*==============================================================*/
create index IDX_TACHEAGENT_IDMISSION on TACHEAGENT (
   IDMISSION ASC,
   IDAGENTSITE ASC
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
   DATEREALISATION ASC,
   IDAGENTSITE ASC
)
pctfree 2
tablespace I_DATA
/


/*==============================================================*/
/* Index: IDX_TACHEAGENT_DATEFIN                                */
/*==============================================================*/
create index IDX_TACHEAGENT_DATEFIN on TACHEAGENT (
   DATEFIN ASC,
   ETATREALISATION ASC
)
pctfree 2
tablespace I_DATA
/


/*==============================================================*/
/* Table: TACHEAGENT_CONNECT                                    */
/*==============================================================*/


create table TACHEAGENT_CONNECT  (
   IDMISSION            NUMBER(15),
   IDAGENTSITE          NUMBER(5),
   DATEREALISATION      DATE,
   DATEFIN              DATE,
   ETATREALISATION      NUMBER(1),
   MODEM_TYPE           NUMBER(2),
   TENTATIVE            NUMBER(1)                      default 1,
   DATETENTATIVE        DATE
)
TABLESPACE D_DATA
PCTFREE 5
PCTUSED 80
/


/*==============================================================*/
/* Index: IDX_TACHEAGENT_C_IDMISSION                            */
/*==============================================================*/
create index IDX_TACHEAGENT_C_IDMISSION on TACHEAGENT_CONNECT (
   IDMISSION ASC,
   IDAGENTSITE ASC
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
   DATEREALISATION ASC,
   IDAGENTSITE ASC
)
pctfree 2
tablespace I_DATA
/


/*==============================================================*/
/* Index: IDX_TACHEAGENT_C_DATEFIN                              */
/*==============================================================*/
create index IDX_TACHEAGENT_C_DATEFIN on TACHEAGENT_CONNECT (
   DATEFIN ASC,
   ETATREALISATION ASC
)
pctfree 2
tablespace I_DATA
/


/*==============================================================*/
/* Table: TRACEESSAI                                            */
/*==============================================================*/


create table TRACEESSAI  (
   IDMISSION            NUMBER(15)                       not null,
   DATEESSAI            DATE                             not null,
   ETATTRANSFERT        NUMBER(1)                      default 0,
   TRACE                CLOB                             not null
)
TABLESPACE D_DATA
PCTFREE 5
PCTUSED 80
 LOB (TRACE) STORE AS 
      ( TABLESPACE  D_DATA
        ENABLE      STORAGE IN ROW
        CHUNK       8192
        PCTVERSION  10
      )
/


/*==============================================================*/
/* Table: VALEURMIB                                             */
/*==============================================================*/


create table VALEURMIB  (
   IDVALEURMIB          NUMBER(2)                        not null,
   DATEESSAI            DATE,
   IDMISSION            NUMBER(15),
   REQUETE              NUMBER(2),
   VALEUR               NUMBER(10)
)
TABLESPACE D_DATA
PCTFREE 5
PCTUSED 80
/


alter table ANOMALIES
   add constraint FK_ANOMALIES_MIS04 foreign key (IDMISSION)
      references MISSION (IDMISSION)
        enable novalidate
/


alter table ESSAITRACEROUTE
   add constraint FK_ESSAITRACEROUTE_MIS03 foreign key (IDMISSION)
      references MISSION (IDMISSION)
        enable novalidate
/


alter table ESSAITRACEROUTEPANEL
   add constraint FK_ESSAITRACEROUTE_MIS15 foreign key (IDMISSION)
      references MISSION (IDMISSION)
        enable novalidate
/


alter table INCIDENTMISSION
   add constraint FK_INCIDENTMISSION_MIS02 foreign key (IDMISSION)
      references MISSION (IDMISSION)
        enable novalidate
/


alter table LIENAGENTMISSION
   add constraint FK_LIENAGENTMISSIO_MIS01 foreign key (IDMISSION)
      references MISSION (IDMISSION)
        enable novalidate
/


alter table MAINTENANCEMISSION
   add constraint FK_MAINTENANCEMISS_MIS09 foreign key (IDMISSION)
      references MISSION (IDMISSION)
        enable novalidate
/


alter table MESUREOBJET
   add constraint FK_MESUREOBJET_MIS12 foreign key (IDMISSION)
      references MISSION (IDMISSION)
        enable novalidate
/


alter table MESUREPING
   add constraint FK_MESUREPING_MIS05 foreign key (IDMISSION)
      references MISSION (IDMISSION)
        enable novalidate
/


alter table MESURERETOURMESSAGE
   add constraint FK_MESURERETOURMES_MIS06 foreign key (IDMISSION)
      references MISSION (IDMISSION)
        enable novalidate
/


alter table MESURES
   add constraint FK_MESURES_MIS10 foreign key (IDMISSION)
      references MISSION (IDMISSION)
        enable novalidate
/


alter table MESURETRACEROUTE
   add constraint FK_MESURETRACEROUT_MIS08 foreign key (IDMISSION)
      references MISSION (IDMISSION)
        enable novalidate
/


alter table MESURETRACEROUTEPANEL
   add constraint FK_MESURETRACEROUT_MIS14 foreign key (IDMISSION)
      references MISSION (IDMISSION)
        enable novalidate
/


alter table TACHEAGENT
   add constraint FK_TACHEAGENT_LAM01 foreign key (IDMISSION, IDAGENTSITE)
      references LIENAGENTMISSION (IDMISSION, IDAGENTSITE)
        enable novalidate
/


alter table TACHEAGENT_CONNECT
   add constraint FK_TACHEAGENT_CONN_LAM02 foreign key (IDMISSION, IDAGENTSITE)
      references LIENAGENTMISSION (IDMISSION, IDAGENTSITE)
        enable novalidate
/


alter table TRACEESSAI
   add constraint FK_TRACEESSAI_MIS13 foreign key (IDMISSION)
      references MISSION (IDMISSION)
        enable novalidate
/


alter table VALEURMIB
   add constraint FK_VALEURMIB_MIS11 foreign key (IDMISSION)
      references MISSION (IDMISSION)
        enable novalidate
/


