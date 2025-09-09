# file: db_clients.py
from __future__ import annotations
import abc
from typing import Iterable, Any, Sequence, Optional
import pyodbc

class BaseSQLServerClient(abc.ABC):
    """Common interface for SQL Server connections."""
    def __init__(self) -> None:
        self.conn = None
        self.cursor = None

    @abc.abstractmethod
    def connect_sql_auth(self, server: str, database: str, user: str, password: str, **kwargs) -> None: ...

    @abc.abstractmethod
    def connect_windows_auth(self, server: str, database: str, **kwargs) -> None: ...

    @abc.abstractmethod
    def execute(self, sql: str, params: Optional[Sequence[Any]] = None) -> None: ...

    @abc.abstractmethod
    def executemany(self, sql: str, rows: Iterable[Sequence[Any]]) -> None: ...

    @abc.abstractmethod
    def fetchall(self) -> list[tuple]: ...

    @abc.abstractmethod
    def commit(self) -> None: ...

    @abc.abstractmethod
    def rollback(self) -> None: ...

    @abc.abstractmethod
    def close(self) -> None: ...


# ---------- pyodbc implementation ----------
class PyODBCClient(BaseSQLServerClient):
    """
    pyodbc client.
    Requires Microsoft ODBC Driver for SQL Server (e.g., 'ODBC Driver 17 for SQL Server').
    Placeholder style: '?'
    """
    def __init__(self, driver: str = "ODBC Driver 18 for SQL Server", autocommit: bool = False) -> None:
        super().__init__()
        try:
            import pyodbc  # type: ignore
        except ImportError as e:
            raise RuntimeError("pyodbc not installed. pip install pyodbc") from e
        self._pyodbc = pyodbc
        self.driver = driver
        self.autocommit = autocommit

    def connect_sql_auth(self, server: str, database: str, user: str, password: str, **kwargs) -> None:
        conn_str = (
            f"DRIVER={{{self.driver}}};"
            f"SERVER={server};DATABASE={database};UID={user};PWD={password}"
        )
        self.conn = self._pyodbc.connect(conn_str, autocommit=self.autocommit, timeout=kwargs.get("timeout", 10))
        self.cursor = self.conn.cursor()

    def connect_windows_auth(self, server: str, database: str, **kwargs) -> None:
        # Windows only
        conn_str = (
            f"DRIVER={{{self.driver}}};"
            f"SERVER={server};DATABASE={database};Trusted_Connection=yes"
        )
        self.conn = self._pyodbc.connect(conn_str, autocommit=self.autocommit, timeout=kwargs.get("timeout", 10))
        self.cursor = self.conn.cursor()

    def execute(self, sql: str, params: Optional[Sequence[Any]] = None) -> None:
        self.cursor.execute(sql, params or [])

    def executemany(self, sql: str, rows: Iterable[Sequence[Any]]) -> None:
        # Enable fast batch inserts
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
            if self.cursor: self.cursor.close()
        finally:
            if self.conn: self.conn.close()


# ---------- pymssql implementation ----------
class PyMSSQLClient(BaseSQLServerClient):
    """
    pymssql client (TDS protocol).
    Placeholder style: '%s'
    """
    def __init__(self, autocommit: bool = False) -> None:
        super().__init__()
        try:
            import pymssql  # type: ignore
        except ImportError as e:
            raise RuntimeError("pymssql not installed. pip install pymssql") from e
        self._pymssql = pymssql
        self.autocommit = autocommit

    def connect_sql_auth(self, server: str, database: str, user: str, password: str, **kwargs) -> None:
        # server may be 'host' or 'host,port'
        self.conn = self._pymssql.connect(
            server=server,
            user=user,
            password=password,
            database=database,
            timeout=kwargs.get("timeout", 10),
            login_timeout=kwargs.get("login_timeout", 10),
            as_dict=False
        )
        self.conn.autocommit(self.autocommit)
        self.cursor = self.conn.cursor()

    def connect_windows_auth(self, server: str, database: str, **kwargs) -> None:
        # Windows Integrated Security via pymssql is non-trivial; generally use SQL auth
        # or configure Kerberos/FreeTDS. We surface a clear error to avoid confusion.
        raise NotImplementedError("Windows Auth with pymssql is not directly supported; prefer pyodbc or Kerberos + FreeTDS.")

    def execute(self, sql: str, params: Optional[Sequence[Any]] = None) -> None:
        self.cursor.execute(sql, tuple(params or []))  # %s placeholders

    def executemany(self, sql: str, rows: Iterable[Sequence[Any]]) -> None:
        self.cursor.executemany(sql, list(rows))  # no fast_executemany

    def fetchall(self) -> list[tuple]:
        return list(self.cursor.fetchall())

    def commit(self) -> None:
        self.conn.commit()

    def rollback(self) -> None:
        self.conn.rollback()

    def close(self) -> None:
        try:
            if self.cursor: self.cursor.close()
        finally:
            if self.conn: self.conn.close()

if __name__ == "__main__":
    # pyodbc

    # conn = pyodbc.connect(
    #     "DRIVER={ODBC Driver 18 for SQL Server};"
    #     r"SERVER=192.168.1.210\SQL_SRV_A;"  # NOTE: raw string or double backslash \\
    #     "DATABASE=Adventureworks2017;"
    #     "UID=sa;PWD=P@ssw0rd;"
    #     "Encrypt=yes;TrustServerCertificate=yes;"
    # )



    # conn = pyodbc.connect(
    #     "DRIVER={ODBC Driver 18 for SQL Server};"
    #     "SERVER=192.168.1.210,1433;"  # host,comma,port
    #     "DATABASE=Adventureworks2017;"
    #     "UID=sa;PWD=P@ssw0rd;"
    #     "Encrypt=yes;TrustServerCertificate=yes;"
    # )
    #
    #


    # print(pyodbc.drivers())
    # client = PyODBCClient(driver="ODBC Driver 18 for SQL Server", autocommit=False)
    # client.connect_sql_auth(server="192.168.1.210,1433", database="Adventureworks2017", user="sa", password="P@ssw0rd", Encrypt="yes", TrustServerCertificate="yes")
    # # client.connect_sql_auth(server="192.168.1.210", database="Adventureworks2017", user="sa", password="P@ssw0rd", Encrypt="no")
    # # client.execute("SELECT TOP 3 SymbolName FROM Finance.Symbols")
    # # print(client.fetchall())
    # client.close()

    # pymssql
    client = PyMSSQLClient(autocommit=False)
    client.connect_sql_auth(server="192.168.1.210", database="Adventureworks2017", user="sa", password="P@ssw0rd")
    # client.execute("SELECT TOP 3 SymbolName FROM Finance.Symbols")
    client.execute("SELECT Title, FirstName, MiddleName, LastName  FROM Person.Person")
    print(client.fetchall())
    client.close()

    #
    #
    # # Windows Authentication (pyodbc only)
    # client = PyODBCClient(driver="ODBC Driver 17 for SQL Server", autocommit=False)
    # client.connect_windows_auth(server=r".\\SQLEXPRESS", database="FinancialData")
    # client.execute("SELECT COUNT(*) FROM Finance.HistoricalPrices")
    # print(client.fetchall())
    # client.close()






    # # Parameterization & stored procedures
    # # pyodbc parameterization ('?')
    # client.execute("SELECT * FROM Finance.Symbols WHERE SymbolName = ?", ["BTCUSD"])
    #
    # # pyodbc stored proc
    # client.execute("EXEC Finance.MyProc ?, ?", [42, "abc"])
    # # or: client.execute("{CALL Finance.MyProc(?, ?)}", [42, "abc"])
    #
    # # pymssql parameterization ('%s')
    # client.execute("SELECT * FROM Finance.Symbols WHERE SymbolName = %s", ["BTCUSD"])
    #
    # # pymssql stored proc
    # client.cursor.callproc("Finance.MyProc", (42, "abc"))
    # rows = client.fetchall()
    #
    #
    #
    #
    #
    #
    # # Bulk Insert
    # rows = [
    #     ("BTCUSD", "Bitcoin / USD"),
    #     ("ETHUSD", "Ethereum / USD"),
    # ]
    #
    # # pyodbc (faster):
    # client = PyODBCClient()
    # client.connect_sql_auth("localhost", "FinancialData", "sa", "P@ssw0rd")
    # client.executemany("INSERT INTO Finance.Symbols(SymbolName, Description) VALUES (?, ?)", rows)
    # client.commit()
    # client.close()
    #
    # # pymssql:
    # client = PyMSSQLClient()
    # client.connect_sql_auth("localhost", "FinancialData", "sa", "P@ssw0rd")
    # client.executemany("INSERT INTO Finance.Symbols(SymbolName, Description) VALUES (%s, %s)", rows)
    # client.commit()
    # client.close()
    #















