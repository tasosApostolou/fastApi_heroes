from sqlmodel import Session, SQLModel, create_engine
from functools import lru_cache
from typing import Annotated
from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine


# -------------------------------------------------------------------
# Base Database
# -------------------------------------------------------------------

class BaseDatabase:
    """BaseDatabase defines the database operations. It can be extended to support different database types (SQLite, Postgres, MySQL) by implementing the create_db_and_tables() and get_session() methods."""
    def __init__(
        self,
        url: str,
        echo: bool = False,
        connect_args: dict | None = None,
    ):
        self.engine = create_engine(
            url,
            echo=echo,
            connect_args=connect_args or {},
        )

    def create_db_and_tables(self):
        SQLModel.metadata.create_all(self.engine)

    def get_session(self):
        with Session(self.engine) as session:
            yield session

# -------------------------------------------------------------------
# SQLite Database setup inheriting from BaseDatabase
# -------------------------------------------------------------------

class SQLiteDatabase(BaseDatabase):
    """SQLiteDatabase extends BaseDatabase to provide a concrete implementation for SQLite. It initializes the database connection with the appropriate URL and connection arguments for SQLite."""
    def __init__(
        self,
        path: str = "./database.db",
        echo: bool = False,
    ):
        super().__init__(
            url=f"sqlite:///{path}",
            echo=echo,
            connect_args={"check_same_thread": False},
        )

# -------------------------------------------------------------------
# PostgreSQL Database
# -------------------------------------------------------------------

class PostgresDatabase(BaseDatabase):
    """
    PostgreSQL database implementation.
    """

    def __init__(
        self,
        user: str = "postgres",
        password: str = "postgres",
        host: str = "localhost",
        port: int = 5432,
        database: str = "heroes_db",
        echo: bool = False,
    ):
        super().__init__(
            url=(
                f"postgresql+psycopg://"
                f"{user}:{password}@{host}:{port}/{database}"
            ),
            echo=echo,
        )

# -------------------------------------------------------------------
# MySQL Database
# -------------------------------------------------------------------

class MySQLDatabase(BaseDatabase):
    """
    MySQL database implementation.
    """

    def __init__(
        self,
        user: str = "root",
        password: str = "root",
        host: str = "localhost",
        port: int = 3306,
        database: str = "heroes_db",
        echo: bool = False,
    ):
        super().__init__(
            url=(
                f"mysql+pymysql://"
                f"{user}:{password}@{host}:{port}/{database}"
            ),
            echo=echo,
        )


# -------------------------------------------------------------------
# Singleton db instance cache & Dependency SQLite by default
# -------------------------------------------------------------------

@lru_cache
def get_database(db_type:str = "sqlite") -> BaseDatabase:
    """
    Returrn a singleton Database instance with default type of sqlite.
    this could be extended to return different database types based on config
    """
    match db_type:

        case "sqlite":
            sqlite_db = SQLiteDatabase( path="./database.db", echo=False)
            return sqlite_db
        case "postgres":
            return PostgresDatabase()  # default config by class implementation

        case "mysql":
            return MySQLDatabase()  # default config by class implementation

        case _:
            raise ValueError(
                f"Unsupported database type: {db_type}"
            )

def get_sqlite() -> BaseDatabase:
    return get_database("sqlite")

sqlite_dep = Annotated[BaseDatabase,Depends(get_sqlite)]

def get_session(db: sqlite_dep):
    yield from db.get_session()

