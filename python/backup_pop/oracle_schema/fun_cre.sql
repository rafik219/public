CREATE OR REPLACE FUNCTION Return_Decalage_Maintenance(datemaintenance DATE, idt NUMBER) RETURN DATE IS
debut DATE;
fin DATE;
debut_sys DATE;
fin_sys DATE;
decal NUMBER;
decal_sys NUMBER;
adst NUMBER;
--test_date DATE :=TO_DATE('11/02/2003 22:00:00','DD/MM/YYYY HH24:MI:SS');
--remplacer sysdate par test_date pour tester
BEGIN
SELECT adst  INTO adst FROM TIMEZONE  WHERE idtimezone=idt;
SELECT datedebutdst, datefindst INTO debut, fin FROM DATETIMEZONE WHERE idtimezone=idt AND
TO_CHAR(datemaintenance,'YYYY')=TO_CHAR(datedebutdst,'YYYY');

IF datemaintenance<debut OR datemaintenance>=fin THEN
   			SELECT decalage INTO decal FROM TIMEZONE WHERE idtimezone=idt;
ELSE
   			SELECT decalagedst INTO decal FROM TIMEZONE WHERE idtimezone=idt;
END IF;

BEGIN
SELECT datedebutdst, datefindst INTO debut_sys, fin_sys FROM DATETIMEZONE WHERE idtimezone=idt AND
TO_CHAR(SYSDATE,'YYYY')=TO_CHAR(datedebutdst,'YYYY');
IF SYSDATE<debut_sys OR SYSDATE>=fin_sys THEN
   			SELECT decalage INTO decal_sys FROM TIMEZONE WHERE idtimezone=idt;
ELSE
   			SELECT decalagedst INTO decal_sys FROM TIMEZONE WHERE idtimezone=idt;
END IF;
EXCEPTION WHEN OTHERS THEN
  decal_sys := -1;
END;
--DBMS_OUTPUT.PUT_LINE(datemaintenance||' decal '||decal||' decal sys '||decal_sys||' adst '||adst);
IF decal=decal_sys THEN RETURN TO_DATE(datemaintenance,'DD/MM/YYYY HH24:MI:SS');
ELSIF decal<decal_sys   THEN RETURN TO_DATE(datemaintenance-(adst/24),'DD/MM/YYYY HH24:MI:SS');
ELSE RETURN TO_DATE(datemaintenance+(adst/24),'DD/MM/YYYY HH24:MI:SS');
END IF;
END;
/
SHOW ERRORS

