"""
Data Warehouse Database Connection Manager
Provides unified interface for SQLite, DuckDB, and PostgreSQL.
"""

import os
from contextlib import contextmanager
from typing import Generator, Any, Optional
import pandas as pd
from sqlalchemy import create_engine, Engine, text
import config
from utils.logger import get_logger

logger = get_logger("warehouse_db")

class WarehouseManager:
    """Manages database connection lifecycle and provides query execution utilities."""
    
    _engine: Optional[Engine] = None

    @classmethod
    def get_connection_url(cls) -> str:
        """Returns the SQLAlchemy connection URL according to configuration."""
        dialect = config.DB_DIALECT.lower()
        if dialect == "postgresql":
            return f"postgresql://{config.PG_USER}:{config.PG_PASSWORD}@{config.PG_HOST}:{config.PG_PORT}/{config.PG_DATABASE}"
        elif dialect == "duckdb":
            return f"duckdb:///{config.DUCKDB_PATH}"
        else:
            # Default to SQLite for 100% self-contained local execution
            return f"sqlite:///{config.SQLITE_DB_PATH}"

    @classmethod
    def get_engine(cls) -> Engine:
        """Returns singleton SQLAlchemy Engine."""
        if cls._engine is None:
            url = cls.get_connection_url()
            logger.info(f"Initializing Warehouse connection with dialect '{config.DB_DIALECT}'...")
            cls._engine = create_engine(url, echo=False)
        return cls._engine

    @classmethod
    @contextmanager
    def get_connection(cls) -> Generator[Any, None, None]:
        """Context manager for obtaining a database connection."""
        engine = cls.get_engine()
        connection = engine.connect()
        try:
            yield connection
        finally:
            connection.close()

    @classmethod
    def execute_query(cls, sql_query: str, params: Optional[dict] = None) -> None:
        """Executes a raw SQL DDL or DML statement."""
        engine = cls.get_engine()
        with engine.begin() as conn:
            conn.execute(text(sql_query), params or {})

    @classmethod
    def read_query(cls, sql_query: str, params: Optional[dict] = None) -> pd.DataFrame:
        """Executes a SELECT query and returns a pandas DataFrame."""
        engine = cls.get_engine()
        with engine.connect() as conn:
            return pd.read_sql(text(sql_query), conn, params=params)

    @classmethod
    def write_dataframe(
        cls,
        df: pd.DataFrame,
        table_name: str,
        if_exists: str = "replace",
        index: bool = False
    ) -> None:
        """Writes a pandas DataFrame into a data warehouse table."""
        engine = cls.get_engine()
        logger.info(f"Writing {len(df):,} records into table '{table_name}' (mode: {if_exists})...")
        df.to_sql(table_name, engine, if_exists=if_exists, index=index, chunksize=10000)
        logger.info(f"Successfully loaded '{table_name}'.")
