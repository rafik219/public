# rem Create user and schema

# import data for each user
for var_user in $(cat list_users_drop.txt)
do
  sqlplus / as sysdba @users_drop.sql ${var_user}
  # create schema object
done

exit 0
