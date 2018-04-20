rem !
rem  @(-) File : %M%	Release : %I%	Date : %G%
rem ==============================================================================
rem Oracle version : 9i
rem Project........: IP-LABEL CO
rem Filename.......: users_cre.sql
rem Date...........: 16/10/2003
rem Version........: 1.0
rem Description....: Users creation
rem

define VAR_USER=&&1

connect / as sysdba

spool .users_cre&&VAR_USER.log

DROP USER &&VAR_USER CASCADE;

CREATE USER &&VAR_USER
  IDENTIFIED BY lyd7ugp
  DEFAULT TABLESPACE USERS
  TEMPORARY TABLESPACE TEMP
  PROFILE DEFAULT
  ACCOUNT UNLOCK
/

GRANT CONNECT TO &&VAR_USER;
GRANT IPLABEL TO &&VAR_USER;
ALTER USER &&VAR_USER DEFAULT ROLE ALL;

ALTER USER &&VAR_USER
    QUOTA UNLIMITED ON USERS
    QUOTA UNLIMITED ON D_DATA
    QUOTA UNLIMITED ON I_DATA
/


CREATE OR REPLACE DIRECTORY dmpdir AS '/home/oracle/dmpdir';
GRANT read, write ON DIRECTORY dmpdir to &&VAR_USER;

spool off

exit

rem ==============================================================================
rem   End of file
rem ==============================================================================
