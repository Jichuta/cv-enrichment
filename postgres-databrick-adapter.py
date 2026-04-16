"""
Databricks database adapter implementation
"""

import os
from typing import List, Dict, Any, Optional
from databricks import sql
from app.models.adapters.base_adapter import BaseDatabaseAdapter
import psycopg2
import psycopg2.extras
from databricks.sdk import WorkspaceClient
import uuid


class PostgresDatabaseAdapter(BaseDatabaseAdapter):
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        autocommit: bool = False,
    ):
        w = WorkspaceClient(
            host=os.getenv("DATABRICKS_HOST"), token=os.getenv("DATABRICKS_TOKEN")
        )

        credential = None

        environment = os.getenv("ENVIRONMENT", "development")
        if environment == "production":
            # Generate OAuth token for database connection (1-hour expiration)
            credential = w.postgres.generate_database_credential(
                endpoint="projects/recruitment/branches/production/endpoints/primary"
                )
        
        elif environment == "development":
            instance_name = os.getenv(
            "DATABRICKS_POSTGRES_INSTANCE_NAME", "recruitment-ai-web-data"
            )

            credential = w.database.generate_database_credential(
            request_id=str(uuid.uuid4()), instance_names=[instance_name]
            )
        

        self._dsn = {
            "host": host or os.getenv("DATABRICKS_POSTGRES_HOST"),
            "port": port or os.getenv("DATABRICKS_POSTGRES_PORT", 5432),
            "dbname": database or os.getenv("DATABRICKS_POSTGRES_DB"),
            "user": user or os.getenv("DATABRICKS_POSTGRES_USER"),
            "password": credential.token,
            "sslmode": "require",
        }
        self._conn = None
        self._autocommit = autocommit

    def connect(self):
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(**self._dsn)
            self._conn.autocommit = self._autocommit

    def close(self):
        if self._conn and not self._conn.closed:
            self._conn.close()
            self._conn = None

    # -------------------------
    # Query execution
    # -------------------------
    def _convert_query_for_postgres(self, query: str) -> str:
        """
        Convert query from Databricks format to PostgreSQL format:
        - Convert :param_name to %(param_name)s (psycopg2 format)
        - Convert CURRENT_TIMESTAMP() to CURRENT_TIMESTAMP
        """
        import re

        query = re.sub(r":(\w+)", r"%(\1)s", query)
        query = query.replace("CURRENT_TIMESTAMP()", "CURRENT_TIMESTAMP")
        return query

    def execute_query(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Any]:
        self._ensure_connection()

        assert self._conn is not None
        query = self._convert_query_for_postgres(query)
        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def execute_update(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> int:
        self._ensure_connection()
        assert self._conn is not None
        query = self._convert_query_for_postgres(query)
        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(query, params)
            return cursor.rowcount

    def execute_insert(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> Optional[int]:
        """
        Expects RETURNING id in the query if an ID is needed
        """
        self._ensure_connection()
        assert self._conn is not None
        query = self._convert_query_for_postgres(query)
        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(query, params)
            try:
                if cursor.description:
                    row = cursor.fetchone()
                    if row:
                        if isinstance(row, dict):
                            inserted_id = list(row.values())[0]
                        else:
                            inserted_id = row[0]
                        return inserted_id
            except (TypeError, IndexError):
                return None

    # -------------------------
    # Transactions
    # -------------------------
    def begin_transaction(self):
        self._ensure_connection()
        assert self._conn is not None
        self._conn.autocommit = False

    def commit(self):
        if self._conn:
            self._conn.commit()

    def rollback(self):
        if self._conn:
            self._conn.rollback()

    # -------------------------
    # Internal helpers
    # -------------------------
    def _ensure_connection(self):
        if self._conn is None or self._conn.closed:
            self.connect()