/*==============================================================*/
/* Database name:  SITEAGENT                                    */
/* DBMS name:      ORACLE Version 9i                            */
/* Created on:     27/10/2005 07:31:30                          */
/* Modifie le:     18/09/2007 15:29:30                          */
/* Rajout table EXPLOIT                                         */
/*==============================================================*/


/*==============================================================*/
/* Table: AGENTSITE                                             */
/*==============================================================*/


create table AGENTSITE  (
   TYPEAPPLICATION      NUMBER(5)                        not null,
   NOMMACHINE           VARCHAR2(255)                    not null,
   CAPACITEMAX          NUMBER(5),
   CAPACITEUTILISEE     NUMBER(5),
   IDAGENTSITE          NUMBER(5)                        not null,
   constraint PK_AGENTSITE primary key (TYPEAPPLICATION, NOMMACHINE)
         using index
       pctfree 2
       tablespace I_DATA
)
TABLESPACE D_DATA
PCTFREE 5
PCTUSED 80
/


/*==============================================================*/
/* Table: ANOMALIES                                             */
/*==============================================================*/


create table ANOMALIES  (
   IDMISSION            NUMBER(15)                       not null,
   DATEESSAI            DATE                             not null,
   REQUETE              NUMBER(2)                        not null,
   TYPEANOMALIE         NUMBER(3)                        not null,
   CODEANOMALIE         NUMBER(4)                        not null,
   MESSAGE              VARCHAR2(255),
   DATEMESURE           DATE,
   ETATTRANSFERT        NUMBER(1)                      default 0  not null
)
TABLESPACE D_DATA
PCTFREE 5
PCTUSED 80
/


/*==============================================================*/
/* Table: DATETIMEZONE                                          */
/*==============================================================*/


create table DATETIMEZONE  (
   IDTIMEZONE           NUMBER(5)                        not null,
   DATEDEBUTDST         DATE                             not null,
   DATEFINDST           DATE                             not null
)
PCTFREE 10
PCTUSED 75
TABLESPACE D_DATA
/


comment on table DATETIMEZONE is 'DATE TIMEZONE'
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
TABLESPACE D_DATA
PCTFREE 5
PCTUSED 80
/


/*==============================================================*/
/* Table: EXPLOIT                                               */
/*==============================================================*/

CREATE TABLE EXPLOIT
(
  DATECONSO        DATE                         NOT NULL,
  TYPEAPPLICATION  NUMBER(6),
  IDSITE           NUMBER(5)                    NOT NULL,
  DONNEEMESURE     NUMBER(3),
  IDMISSION        NUMBER(15),
  DONNEE           NUMBER(3)                    NOT NULL,
  VALEUR           NUMBER(13)                   NOT NULL,
  ETATTRANSFERT    NUMBER(1)                    DEFAULT 0                     NOT NULL
)
TABLESPACE D_DATA
PCTFREE    5
PCTUSED    80
/



/*==============================================================*/
/* Table: HEURESMAINTIEN                                        */
/*==============================================================*/


create table HEURESMAINTIEN  (
   HEURE                NUMBER(2)                        not null,
   constraint PK_HEURESMAINTIEN primary key (HEURE)
)
organization
    index
         pctfree 5
         tablespace D_DATA
/


/*==============================================================*/
/* Table: INCIDENTMISSION                                       */
/*==============================================================*/


create table INCIDENTMISSION  (
   IDINCIDENTMISSION    INTEGER,
   IDMISSION            NUMBER(15),
   DATEINCIDENT         DATE,
   TYPEINCIDENT         NUMBER(3),
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
   IDINCIDENTSITE       INTEGER,
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
   IDMISSION            NUMBER(15) not null,
   DATEMAINTENANCE      DATE                             not null,
   DUREE                NUMBER(7)                        not null,
   TYPEMAINTENANCE      NUMBER(1)                        not null,
   IDMAINTENANCECONTRAT NUMBER(13) not null
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
   TPSDNS               NUMBER(5),
   TPSCONNEXION         NUMBER(5),
   TPSOCTET             NUMBER(6),
   TPSOBJET             NUMBER(6),
   TAILLEOBJET          NUMBER(8),
   ETATTRANSFERT        NUMBER(1)                      default 0  not null,
   CODEHTTP             NUMBER(4),
   DELTATIME            NUMBER(6)
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
   REQUETE              NUMBER(3),
   TEMPSMIN             NUMBER(5),
   TEMPSMAX             NUMBER(5),
   TEMPSMOYEN           NUMBER(5),
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
   NUMERONOEUD          NUMBER(3)                        not null,
   OBJETMESURE          VARCHAR2(255)                    not null,
   TPSDELAI             NUMBER(15),
   ETATTRANSFERT        NUMBER(1)                      default 0  not null
)
TABLESPACE D_DATA
PCTFREE 5
PCTUSED 80
/


/*==============================================================*/
/* Table: MESURES                                               */
/*==============================================================*/


create table MESURES  (
   IDMISSION            NUMBER(15)                       not null,
   DATEESSAI            DATE                             not null,
   DATEMESURE           DATE,
   REQUETE              NUMBER(2)                        not null,
   OBJETMESURE          VARCHAR2(255),
   DONNEEMESURE         NUMBER(3)                        not null,
   VALEURMESURE         NUMBER(13)                       not null,
   ETATTRANSFERT        NUMBER(1)                      default 0  not null
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
   ADRESSEIP            NUMBER(15)                       not null,
   ASNUMBER             NUMBER(1)                      default 0,
   TEMPSMIN             NUMBER(5),
   TEMPSMAX             NUMBER(5),
   TEMPSMOYEN           NUMBER(5),
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
   TEMPSMIN             NUMBER(5),
   TEMPSMAX             NUMBER(5),
   TEMPSMOYEN           NUMBER(5),
   NBERREURS            NUMBER(2),
   ETATTRANSFERT        NUMBER(1)                      default 0  not null
)
TABLESPACE D_DATA
PCTFREE 5
PCTUSED 80
/


/*==============================================================*/
/* Table: MISSION                                               */
/*==============================================================*/


create table MISSION  (
   IDMISSION            NUMBER(15)                       not null,
   DEBUTMISSION         DATE                             not null,
   FINMISSION           DATE,
   ETATMISSIONSITE      NUMBER(1)                      default 1  not null,
   ETATMISSION          NUMBER(1),
   TYPEAPPLICATION      NUMBER(5),
   COUT                 NUMBER(1),
   DERNIERETACHE        DATE,
   IDCOMMUNICATION      NUMBER(5),
   FREQUENCE            NUMBER(6)                      default 0  not null,
   TYPEMODEM            NUMBER(10),
   PARAMETRESAPPLICATION CLOB,
   constraint PK_MISSION primary key (IDMISSION)
         using index
       pctfree 2
       tablespace I_DATA
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


/*==============================================================*/
/* Table: PARAMETRESAPPLICATION                                 */
/*==============================================================*/


create table PARAMETRESAPPLICATION  (
   NOMAPPLICATION       VARCHAR2(255)                    not null,
   PARAMETRE            VARCHAR2(255)                    not null,
   VALEUR               VARCHAR2(255),
   constraint PK_PARAMETRESAPPLICATION primary key (NOMAPPLICATION, PARAMETRE)
         using index
       pctfree 2
       tablespace I_DATA
)
TABLESPACE D_DATA
PCTFREE 5
PCTUSED 80
/


/*==============================================================*/
/* Table: TACHEAGENT                                            */
/*==============================================================*/


create table TACHEAGENT  (
   IDMISSION            NUMBER(15)                       not null,
   DATEREALISATION      DATE                             not null,
   IDAGENTSITE          NUMBER(5)                        not null,
   DATEFIN              DATE,
   ETATREALISATION      NUMBER(1),
   TENTATIVE            NUMBER(2)                      default 1,
   DATETENTATIVE        DATE,
   constraint PK_TACHEAGENT primary key (IDMISSION, DATEREALISATION)
         using index
       pctfree 2
       tablespace I_DATA
)
TABLESPACE D_DATA
PCTFREE 5
PCTUSED 80
/


/*==============================================================*/
/* Table: TACHEAGENT_CONNECT                                    */
/*==============================================================*/


create table TACHEAGENT_CONNECT  (
   IDMISSION            NUMBER(15)                       not null,
   DATEREALISATION      DATE                             not null,
   IDAGENTSITE          NUMBER(5)                        not null,
   DATEFIN              DATE,
   ETATREALISATION      NUMBER(1),
   MODEM_TYPE           NUMBER(10),
   TENTATIVE            NUMBER(2)                      default 1,
   DATETENTATIVE        DATE,
   constraint PK_TACHEAGENT_CONNECT primary key (IDMISSION, DATEREALISATION)
         using index
       pctfree 2
       tablespace I_DATA
)
TABLESPACE D_DATA
PCTFREE 5
PCTUSED 80
/


/*==============================================================*/
/* Table: TIMEZONE                                              */
/*==============================================================*/


create table TIMEZONE  (
   IDTIMEZONE           NUMBER(5)                        not null,
   DECALAGE             NUMBER(5,2)                      not null,
   DECALAGEDST          NUMBER(5,2)                      not null,
   ADST                 NUMBER(1)                        not null,
   NOMTIMEZONE          VARCHAR2(255)                    not null,
   constraint PK_TIMEZONE primary key (IDTIMEZONE)
         using index
          pctfree 2
          tablespace I_DATA
)
PCTFREE 10
PCTUSED 75
TABLESPACE D_DATA
/


comment on table TIMEZONE is 'TIMEZONE'
/


/*==============================================================*/
/* Table: TRACEESSAI                                            */
/*==============================================================*/


create table TRACEESSAI  (
   IDMISSION            NUMBER(15)                       not null,
   DATEESSAI            DATE                             not null,
   ETATTRANSFERT        NUMBER(1)                      default 0  not null,
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


