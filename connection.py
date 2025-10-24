
# abstraction
# abstract class

# abstract base class -> abc
import abc
from typing import Optional, Sequence, Any, Iterable

# microsoft -> ODBC Driver
import pyodbc
import pymssql


class BaseSQLServerClient(abc.ABC):

    def __init__(self) -> None:
        self.cursor = None
        self.conn = None

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
            raise RuntimeError("pymssql is not installed. pip install pymssql") from e
        self._pymssql = pymssql
        self.autocommit = autocommit

    def connect_sql_auth(self, server: str, database: str, user: str, password: str, **kwargs) -> None:
        # server -> ip or name (host)  |  host,port

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

    def connect_windows_auth(self, server: str, database: str, user: str, password: str, **kwargs) -> None:
        raise NotImplementedError("Windows Authwith pymssql is not directly supported")

    def execute(self, sql: str, params: Optional[Sequence[Any]] = None):
        self.cursor.execute(sql, params)

    def executemany(self, sql: str, rows: Iterable[Sequence[Any]] = None) -> None:
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




