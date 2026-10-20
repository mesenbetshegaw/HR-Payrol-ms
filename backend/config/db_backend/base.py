"""
Custom Django database backend for psycopg v3 (Python 3.14 compatible).

Django 5.1 supports psycopg v3 via ENGINE = "django.db.backends.postgresql"
IF psycopg (v3) is installed AND psycopg2 is NOT installed (it prefers psycopg2).
This wrapper forces psycopg v3 usage.
"""
import psycopg
import psycopg.adapt
from django.db.backends.postgresql.base import DatabaseWrapper as Psycopg2DatabaseWrapper
from django.db.backends.postgresql import base as pg_base


# Monkey-patch Django to use psycopg v3's Database module
# Django checks for `Database.connect` — psycopg v3 exposes this via psycopg.connect
class _PsycopgModule:
    """Adapter that makes psycopg v3 look like psycopg2 to Django's backend."""
    
    # Expose what Django's backend checks for
    connect = staticmethod(psycopg.connect)
    Error = psycopg.Error
    DatabaseError = psycopg.DatabaseError
    IntegrityError = psycopg.IntegrityError
    OperationalError = psycopg.OperationalError
    ProgrammingError = psycopg.ProgrammingError
    InterfaceError = psycopg.InterfaceError
    DataError = psycopg.DataError
    NotSupportedError = psycopg.NotSupportedError
    InternalError = psycopg.InternalError
    
    # Constants Django's backend references
    STRING = psycopg.postgres.types["text"]
    NUMBER = psycopg.postgres.types["numeric"] 
    DATETIME = psycopg.postgres.types["timestamp"]
    ROWID = psycopg.postgres.types["oid"]
    
    apilevel = "2.0"
    threadsafety = 1
    paramstyle = "pyformat"


# Override Django's Database reference at module level
pg_base.Database = _PsycopgModule()


class DatabaseWrapper(Psycopg2DatabaseWrapper):
    """
    PostgreSQL database backend using psycopg v3 binary.
    Compatible with Python 3.14.
    """

    def get_new_connection(self, conn_params):
        """Open a new connection using psycopg v3."""
        # psycopg v3 connect() has same interface as psycopg2 for basic params
        conn = psycopg.connect(
            dbname=conn_params.get("dbname") or conn_params.get("database"),
            user=conn_params.get("user"),
            password=conn_params.get("password"),
            host=conn_params.get("host", "127.0.0.1"),
            port=conn_params.get("port", 5432),
        )
        return conn

    def _set_autocommit(self, autocommit):
        with self.wrap_database_errors:
            self.connection.autocommit = autocommit

    def get_database_version(self):
        """Return PostgreSQL server version as tuple."""
        if self.connection:
            v = self.connection.server_version
            # server_version is an integer like 180006
            major = v // 10000
            minor = (v % 10000) // 100
            return (major, minor)
        return (18, 0)
