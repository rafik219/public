rem !
rem  @(-) File : %M%	Release : %I%	Date : %G%
rem ==============================================================================
rem Oracle version : 8i
rem Project........: NETDEALING & CO
rem Filename.......: users_sup.sql
rem Date...........: 11/09/2001
rem Version........: 1.0
rem Description....: Users suppression
rem
rem ==============================================================================
rem Use : sqlplus system/manager @users_sup.sql
rem
rem -------------------------------------------------------------------------------
rem             ACTION                           | VERSION |  DATE   |   AUTHOR |
rem -------------------------------------------------------------------------------
rem Creation                                     |  1.0    |11/09/01 |    D.S   |
rem ==============================================================================

define VAR_USER=&&1


spool users_&&VAR_USER.log

DROP USER &&VAR_USER CASCADE;

spool off

exit

rem ==============================================================================
rem   End of file
rem ==============================================================================

