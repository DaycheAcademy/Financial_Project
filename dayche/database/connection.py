
# abstraction
# abstract class

# abstract base class -> abc
import abc
from typing import Optional, Sequence, Any, Iterable

# microsoft -> ODBC Driver
import pyodbc
import pymssql

from dayche.conf.logmanager import LogManager
import logging

from dayche.exceptions.cryptoexceptions import DriverNotInstalled
from dayche.exceptions.cryptoexceptions import DataBaseConnectionError
from dayche.exceptions.cryptoexceptions import QueryExecutionError
from dayche.exceptions.cryptoexceptions import TransactionError

class BaseSQLServerClient(abc.ABC):

    def __init__(self) -> None:

        try:
            lm = LogManager(prefix='db', console=True)
            self._log_path, self._run_id = lm.logger_setup()
            self.files_removed = lm.logger_cleanup(keep_days=2)
        except Exception as e:
            logging.basicConfig(level=logging.INFO)
            self._log_path, self._run_id = None, None

        self.logger = logging.getLogger(self.__class__.__name__)
        self.cursor = None
        self.conn = None
        self.logger.debug("Initialized BaseSQLServerClient | run_id={} | log_path={}".format(self._run_id, self._log_path))

    @abc.abstractmethod
    def connect_sql_auth(self, server: str, database: str, user: str, password: str, **kwargs) -> None:
        pass

    @abc.abstractmethod
    def connect_windows_auth(self, server: str, database: str, user: str, password: str, **kwargs) -> None:
        pass

    @abc.abstractmethod
    def execute(self, sql: str, params: Optional[Sequence[Any]] = None) -> None:
        pass

    @abc.abstractmethod
    def executemany(self, sql: str, rows: Iterable[Sequence[Any]] = None) -> None:
        pass

    @abc.abstractmethod
    def fetchall(self) -> list[tuple]:
        pass

    @abc.abstractmethod
    def commit(self) -> None:
        pass

    @abc.abstractmethod
    def rollback(self) -> None:
        pass

    @abc.abstractmethod
    def close(self) -> None:
        pass



class PyODBCClient(BaseSQLServerClient):
    """

    """
    def __init__(self, driver: str = 'ODBC Driver 18 for SQL Server', autocommit: bool = False) -> None:
        super().__init__()
        try:
            import pyodbc
        except ImportError as e:
            raise RuntimeError("pyodbc is not installed. pip install pyodbc") from e
        self._pyodbc = pyodbc
        self.driver = driver
        self.autocommit = autocommit

    def connect_sql_auth(self, server: str, database: str, user: str, password: str, **kwargs) -> None:
        conn_str = (
            f'DRIVER={self.driver};SERVER={server};,DATABASE={database};,UID={user};,PWD={password}'
        )
        self.conn = self._pyodbc.connect(conn_str, autocommit=self.autocommit, timeout=kwargs.get('timeout', 10))
        self.cursor = self.conn.cursor()

    def connect_windows_auth(self, server: str, database: str, user: str, password: str, **kwargs) -> None:
        '''
        windows only authentication method
        '''
        conn_str = (
            f'DRIVER={self.driver};,SERVER={server};,DATABASE={database};'
        )
        self.conn = self._pyodbc.connect(conn_str, autocommit=self.autocommit, timeout=kwargs.get('timeout', 10))
        self.cursor = self.conn.cursor()


    def execute(self, sql: str, params: Optional[Sequence[Any]] = None) -> None:
        self.cursor.execute(sql, params)

    def executemany(self, sql: str, rows: Iterable[Sequence[Any]] = None) -> None:
        self.cursor.fast_executemany = True
        self.cursor.executemany(sql, list(rows))

    def fetchall(self) -> list[tuple]:
        return list(self.cursor.fetchall())

    def commit(self) -> None:
        self.conn.commit()

    def rollback(self) -> None:
        self.conn.rollback()

    def close(self) -> None:
        try:
            if self.cursor:
                self.cursor.close()
        finally:
            if self.conn:
                self.conn.close()


class PyMSSQLClient(BaseSQLServerClient):
    """

    """
    def __init__(self, autocommit: bool = False) -> None:
        super().__init__()
        try:
            import pymssql
        except ImportError as e:
            raise DriverNotInstalled("pymssql is not installed. pip install pymssql", cause=str(e))
        self._pymssql = pymssql
        self.autocommit = autocommit
        self.logger.info("PyMSSQLClient Instance Created | autocommit={}".format(autocommit))

    def connect_sql_auth(self, server: str, database: str, user: str, password: str, **kwargs) -> None:
        # server -> ip or name (host)  |  host,port

        self.logger.debug("Connecting (using pymsssql) to server={} | database={} | user={} | password={}"
                          .format(server, database, user, password))
        try:
            self.conn = self._pymssql.connect(
                server=server,
                database=database,
                user=user,
                password=password,
                timeout=kwargs.get('timeout', 10),
                login_timeout=kwargs.get('login_timeout', 10),
                as_dict=False
            )
            self.conn.autocommit(self.autocommit)
            self.cursor = self.conn.cursor()
            self.logger.info("Connecting (using pymsssql) to server={} | database={} | user={} | password={}"
                          .format(server, database, user, password))
        except Exception as e:
            self.logger.error("Connection (using pymsssql) to server failed: {}".format(str(e)))
            raise DataBaseConnectionError("pymssql connection failed", cause=str(e))

    def connect_windows_auth(self, server: str, database: str, user: str, password: str, **kwargs) -> None:
        self.logger.warning("Windows Auth Requested, but pymssql does not support it")
        raise QueryExecutionError("pymssql connection failed")

    def execute(self, sql: str, params: Optional[Sequence[Any]] = None):
        self.logger.debug("Executing (using pymssql) SQL Query: {} | params: {}".format(sql, params))
        try:
            self.cursor.execute(sql, params) if params is not None else self.cursor.execute(sql)
            self.logger.info("Query (using pymssql) Executed Successfully: {} | params: {}".format(sql, params))
        except Exception as e:
            self.logger.error("Execution (using pymssql) of query failed")
            raise QueryExecutionError("pymssql query execution failed", cause=str(e))

    def executemany(self, sql: str, rows: Iterable[Sequence[Any]] = None) -> None:
        try:
            query_length = len(rows) if rows and hasattr(rows, '__len__') else 0
        except Exception as e:
            query_length = 0
            self.logger.warning("Executing (using pymssql) {} Queries: {}".format(query_length, str(e)))
        try:
            self.cursor.executemany(sql, list(rows))
        except Exception as e:
            self.logger.error("Executemany (using pymssql) failed")
            raise QueryExecutionError("pymssql query executemany failed", cause=str(e))

    def fetchall(self) -> list[tuple]:
        self.logger.debug("Fetching (using pymssql) All Outputs")
        try:
            rows = list(self.cursor.fetchall())
            self.logger.info("Fetched (using pymssql) All Outputs Successfully")
            return rows
        except Exception as e:
            self.logger.error("Fetchall (using pymssql) failed")
            raise QueryExecutionError("pymssql fetchall query execution failed", cause=str(e))

    def commit(self) -> None:
        self.logger.debug("Committing (using pymssql) All Changes")
        try:
            self.conn.commit()
            self.logger.info("All (using pymssql) Changes Committed Successfully")
        except Exception as e:
            self.logger.error("Commit (using pymssql) failed")
            raise TransactionError("pymssql commit failed", cause=str(e))

    def rollback(self) -> None:
        self.logger.debug("Rolling Back (using pymssql) All Changes")
        try:
            self.conn.rollback()
            self.logger.info("All (using pymssql) Changes Rolled Back Successfully")
        except Exception as e:
            self.logger.error("Rolling Back (using pymssql) failed")
            raise TransactionError("pymssql commit failed", cause=str(e))
        self.conn.rollback()

    def close(self) -> None:
        self.logger.debug("Closing (using pymssql) Connection")
        try:
            if self.cursor:
                self.cursor.close()
        finally:
            try:
                if self.conn:
                    self.conn.close()
                self.logger.info("Connection (using pymssql) Closed")
            except Exception as e:
                self.logger.warning("Error (using pymssql) While Closing the Connection: {}".format(str(e)))



if __name__ == "__main__":

    # pyodbc
    # client = PyODBCClient(driver='{ODBC Driver 18 for SQL Server}', autocommit=False)
    # client.connect_sql_auth(server='192.168.1.210',
    #                         database='AdventureWorks2017',
    #                         user='sa',
    #                         password='P@ssw0rd')
    # client.execute('USE AdventureWorks2017')
    # client.execute('SELECT * FROM Person.Person')
    # print(client.fetchall())
    # client.close()


    # pymssql
    client = PyMSSQLClient(autocommit=False)
    client.connect_sql_auth(server='192.168.1.210', database='AdventureWorks2017', user='sa', password='P@ssw0rd')
    client.execute('USE AdventureWorks2017')
    client.execute('SELECT FirstName, LastName FROM Person.Person')
    for item in client.fetchall():
        print(item)
    client.close()




