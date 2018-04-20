rem !
rem @(-) FILE : %M%	RELEASE : %I%	DATE : %G%
rem ==============================================================================
rem Oracle version : 9i
rem Project........: AGENT & co
rem Filename.......: obj_cre.sql
rem DATE...........: 16/10/2003
rem Version........: 1.0
rem Description....: creation OF  objects with options
rem
rem ==============================================================================
rem USE : sqlplus siteagent/siteagent @obj_cre.sql
rem
rem ------------------------------------------------------------------------------
rem             ACTION                           | VERSION |  DATE   |   AUTHOR |
rem ------------------------------------------------------------------------------
rem Creation                                     |  1.0    |16/10/03 |    D.S   |
rem ==============================================================================

set define off

spool .obj_cre.log

prompt TABLE CREATION
@@tab_cre.sql
prompt END OF TABLE CREATION
prompt
prompt

prompt CONSTRAINT CREATION
@@con_cre.sql
prompt END OF CONSTRAINT CREATION
prompt
prompt

prompt CONSTRAINT CHECK CREATION
@@chk_cre.sql
prompt END OF CONSTRAINT CHECK CREATION
prompt
prompt

prompt INDEX CREATION
@@idx_cre.sql
prompt END OF INDEX CREATION
prompt
prompt

prompt SEQUENCE CREATION
@@seq_cre.sql
prompt END OF SEQUENCE CREATION
prompt
prompt

prompt VIEW CREATION
@@view_cre.sql
prompt END OF VIEW CREATION
prompt
prompt

prompt VIEW CREATION
@@fun_cre.sql
prompt END OF VIEW CREATION
prompt
prompt

prompt PROCEDURE-FUNCTION CREATION
REM @@pro_cre.sql
prompt END OF PROCEDURE-FUNCTION CREATION
prompt
prompt

prompt PACKAGE CREATION
@@pkg_cre.sql
REM @@pkg_cre-aol.sql
prompt END OF PACKAGE CREATION
prompt
prompt

prompt TRIGGER CREATION
@@trg_cre.sql
prompt END OF TRIGGER CREATION
prompt
prompt

prompt JOB CREATION
@@job_cre.sql
prompt END OF JOB CREATION
prompt
prompt

prompt DATA INIT
@@data_init.sql
prompt END OF DATA INIT
prompt
prompt


spool off

EXIT

rem ==============================================================================
rem   End of file
rem ==============================================================================
