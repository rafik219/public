rem !
rem @(-) FILE : %M%	RELEASE : %I%	DATE : %G%
rem ==============================================================================
rem Oracle version : 8i
rem Project........: AGENT & co
rem Filename.......: view_cre.sql
rem DATE...........: 16/10/2003
rem Version........: 1.1
rem Description....: creation OF views
rem
rem ==============================================================================
rem USE : sqlplus AGENT/siteagent @view_cre.sql
rem
rem ------------------------------------------------------------------------------
rem             ACTION                           | VERSION |  DATE   |   AUTHOR |
rem ------------------------------------------------------------------------------
rem Creation                                     |  1.0    |16/10/03 |    D.S   |
rem ==============================================================================

REM
REM Custumize views
REM ---------------
REM

create or replace view lienagentmission
as select idmission,typeapplication idagentsite
from mission
where etatmission=0;

rem ==============================================================================
rem END OF FILE
rem ==============================================================================
