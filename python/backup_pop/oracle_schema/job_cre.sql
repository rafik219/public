DECLARE
  var_job_id NUMBER;
BEGIN
  SYS.DBMS_JOB.SUBMIT
  ( job       => var_job_id 
   ,what      => 'begin taches.Suppressiontache(); end;'
   ,next_date => sysdate
   ,interval  => 'sysdate + 1/24'
  );
END;
/
