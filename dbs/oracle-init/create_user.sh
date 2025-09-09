#!/bin/bash
set -e

# Load environment variables
source /opt/oracle/scripts/setup/.env

# Debug: print values (mask passwords)
echo "DEBUG: ORACLE_USER=$ORACLE_USER"
echo "DEBUG: ORACLE_PASSWORD=******"
echo "DEBUG: ORACLE_PDB=$ORACLE_PDB"

# Ensure required variables
: "${ORACLE_USER:?ORACLE_USER not set}"
: "${ORACLE_PASSWORD:?ORACLE_PASSWORD not set}"
: "${ORACLE_PDB:=XEPDB1}"  # default PDB if not set

echo "Creating user $ORACLE_USER in $ORACLE_PDB..."

sqlplus sys/"$ORACLE_SYS_PASSWORD"@//localhost:1521/$ORACLE_PDB as sysdba <<EOF
BEGIN
   EXECUTE IMMEDIATE 'CREATE USER $ORACLE_USER IDENTIFIED BY "$ORACLE_PASSWORD"';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE = -01920 THEN
         NULL; -- user exists
      ELSE
         RAISE;
      END IF;
END;
/

BEGIN
   EXECUTE IMMEDIATE 'GRANT CONNECT, RESOURCE TO $ORACLE_USER';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE = -01919 THEN
         NULL; -- already granted
      ELSE
         RAISE;
      END IF;
END;
/

ALTER USER $ORACLE_USER QUOTA UNLIMITED ON USERS;
EXIT;
EOF
