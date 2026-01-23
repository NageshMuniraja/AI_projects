"""
Database Manager - Multi-database connection and query execution
Supports PostgreSQL, MySQL, SQL Server, SQLite, MongoDB, Snowflake, 
Redshift, BigQuery, Oracle, Cassandra, DynamoDB, DB2, MariaDB
"""

from typing import Dict, List, Any, Optional
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.pool import NullPool
from pymongo import MongoClient
import pandas as pd
import logging
from contextlib import contextmanager
import json

from app.core.config import settings

logger = logging.getLogger(__name__)

# Import cloud database libraries (with error handling)
try:
    from snowflake import connector as snowflake_connector
    SNOWFLAKE_AVAILABLE = True
except ImportError:
    SNOWFLAKE_AVAILABLE = False
    logger.warning("Snowflake connector not available")

try:
    import redshift_connector
    REDSHIFT_AVAILABLE = True
except ImportError:
    REDSHIFT_AVAILABLE = False
    logger.warning("Redshift connector not available")

try:
    from google.cloud import bigquery
    from google.oauth2 import service_account
    BIGQUERY_AVAILABLE = True
except ImportError:
    BIGQUERY_AVAILABLE = False
    logger.warning("BigQuery client not available")

try:
    import oracledb
    ORACLE_AVAILABLE = True
except ImportError:
    ORACLE_AVAILABLE = False
    logger.warning("Oracle client not available")

try:
    from cassandra.cluster import Cluster
    from cassandra.auth import PlainTextAuthProvider
    CASSANDRA_AVAILABLE = True
except ImportError:
    CASSANDRA_AVAILABLE = False
    logger.warning("Cassandra driver not available")

try:
    import boto3
    DYNAMODB_AVAILABLE = True
except ImportError:
    DYNAMODB_AVAILABLE = False
    logger.warning("Boto3 (DynamoDB) not available")


class DatabaseManager:
    """Manage connections and queries across multiple database types"""
    
    def __init__(self):
        """Initialize database manager"""
        self.engines = {}
        self.mongo_clients = {}
    
    def _get_connection_string(
        self,
        database_type: str,
        connection_params: Dict[str, Any]
    ) -> str:
        """Build connection string for SQL databases"""
        host = connection_params.get("host")
        port = connection_params.get("port")
        user = connection_params.get("user")
        password = connection_params.get("password")
        database = connection_params.get("database")
        
        if database_type == "postgresql":
            return f"postgresql://{user}:{password}@{host}:{port}/{database}"
        elif database_type == "mysql":
            return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
        elif database_type == "mariadb":
            return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
        elif database_type == "mssql":
            return f"mssql+pymssql://{user}:{password}@{host}:{port}/{database}"
        elif database_type == "sqlite":
            return f"sqlite:///{database}"
        elif database_type == "oracle":
            # Oracle connection string: oracle+oracledb://user:pass@host:port/?service_name=service
            service_name = connection_params.get("service_name", database)
            return f"oracle+oracledb://{user}:{password}@{host}:{port}/?service_name={service_name}"
        elif database_type == "db2":
            # DB2 connection string
            return f"db2+ibm_db://{user}:{password}@{host}:{port}/{database}"
        elif database_type == "snowflake":
            account = connection_params.get("account")
            warehouse = connection_params.get("warehouse", "")
            schema = connection_params.get("schema", "PUBLIC")
            return f"snowflake://{user}:{password}@{account}/{database}/{schema}?warehouse={warehouse}"
        elif database_type == "redshift":
            return f"redshift+redshift_connector://{user}:{password}@{host}:{port}/{database}"
        else:
            raise ValueError(f"Unsupported database type: {database_type}")
    
    @contextmanager
    def get_connection(
        self,
        database_type: str,
        connection_params: Dict[str, Any]
    ):
        """Get database connection context manager"""
        if database_type == "mongodb":
            # MongoDB connection
            uri = connection_params.get("uri") or settings.MONGODB_URI
            client = MongoClient(uri)
            try:
                yield client
            finally:
                client.close()
        
        elif database_type == "bigquery":
            # BigQuery connection
            if not BIGQUERY_AVAILABLE:
                raise ImportError("BigQuery client not installed. Install: pip install google-cloud-bigquery")
            
            project_id = connection_params.get("project_id")
            credentials_json = connection_params.get("credentials_json")
            
            if credentials_json:
                credentials = service_account.Credentials.from_service_account_info(
                    json.loads(credentials_json)
                )
                client = bigquery.Client(project=project_id, credentials=credentials)
            else:
                client = bigquery.Client(project=project_id)
            
            try:
                yield client
            finally:
                client.close()
        
        elif database_type == "cassandra":
            # Cassandra connection
            if not CASSANDRA_AVAILABLE:
                raise ImportError("Cassandra driver not installed. Install: pip install cassandra-driver")
            
            contact_points = connection_params.get("contact_points", [connection_params.get("host")])
            port = connection_params.get("port", 9042)
            keyspace = connection_params.get("keyspace")
            username = connection_params.get("user")
            password = connection_params.get("password")
            
            if username and password:
                auth_provider = PlainTextAuthProvider(username=username, password=password)
                cluster = Cluster(contact_points=contact_points, port=port, auth_provider=auth_provider)
            else:
                cluster = Cluster(contact_points=contact_points, port=port)
            
            session = cluster.connect(keyspace)
            try:
                yield session
            finally:
                cluster.shutdown()
        
        elif database_type == "dynamodb":
            # DynamoDB connection
            if not DYNAMODB_AVAILABLE:
                raise ImportError("Boto3 not installed. Install: pip install boto3")
            
            region = connection_params.get("region", "us-east-1")
            aws_access_key = connection_params.get("aws_access_key_id")
            aws_secret_key = connection_params.get("aws_secret_access_key")
            
            if aws_access_key and aws_secret_key:
                dynamodb = boto3.resource(
                    'dynamodb',
                    region_name=region,
                    aws_access_key_id=aws_access_key,
                    aws_secret_access_key=aws_secret_key
                )
            else:
                dynamodb = boto3.resource('dynamodb', region_name=region)
            
            try:
                yield dynamodb
            finally:
                pass  # DynamoDB resource doesn't need explicit cleanup
        
        else:
            # SQL database connection (PostgreSQL, MySQL, SQL Server, SQLite, Oracle, DB2, Snowflake, Redshift)
            conn_string = self._get_connection_string(database_type, connection_params)
            
            # Create engine with connection pooling disabled for short-lived connections
            engine = create_engine(
                conn_string,
                poolclass=NullPool,
                echo=settings.DEBUG
            )
            
            try:
                with engine.connect() as conn:
                    yield conn
            finally:
                engine.dispose()
    
    async def get_schema(
        self,
        database_type: str,
        connection_params: Dict[str, Any]
    ) -> str:
        """
        Get database schema as a formatted string
        
        Args:
            database_type: Type of database
            connection_params: Connection parameters
            
        Returns:
            Formatted schema description
        """
        logger.info(f"Fetching schema for {database_type}")
        
        if database_type == "mongodb":
            return await self._get_mongodb_schema(connection_params)
        elif database_type == "bigquery":
            return await self._get_bigquery_schema(connection_params)
        elif database_type == "cassandra":
            return await self._get_cassandra_schema(connection_params)
        elif database_type == "dynamodb":
            return await self._get_dynamodb_schema(connection_params)
        else:
            return await self._get_sql_schema(database_type, connection_params)
    
    async def _get_sql_schema(
        self,
        database_type: str,
        connection_params: Dict[str, Any]
    ) -> str:
        """Get SQL database schema"""
        with self.get_connection(database_type, connection_params) as conn:
            inspector = inspect(conn.engine)
            
            schema_parts = []
            
            # Get all tables
            tables = inspector.get_table_names()
            
            for table in tables:
                schema_parts.append(f"\nTable: {table}")
                
                # Get columns
                columns = inspector.get_columns(table)
                schema_parts.append("Columns:")
                
                for col in columns:
                    col_type = str(col['type'])
                    nullable = "NULL" if col['nullable'] else "NOT NULL"
                    schema_parts.append(
                        f"  - {col['name']}: {col_type} {nullable}"
                    )
                
                # Get primary keys
                pk = inspector.get_pk_constraint(table)
                if pk and pk.get('constrained_columns'):
                    schema_parts.append(
                        f"Primary Key: {', '.join(pk['constrained_columns'])}"
                    )
                
                # Get foreign keys
                fks = inspector.get_foreign_keys(table)
                if fks:
                    schema_parts.append("Foreign Keys:")
                    for fk in fks:
                        schema_parts.append(
                            f"  - {', '.join(fk['constrained_columns'])} -> "
                            f"{fk['referred_table']}.{', '.join(fk['referred_columns'])}"
                        )
                
                # Get indexes
                indexes = inspector.get_indexes(table)
                if indexes:
                    schema_parts.append("Indexes:")
                    for idx in indexes:
                        unique = "UNIQUE" if idx['unique'] else ""
                        schema_parts.append(
                            f"  - {idx['name']}: {', '.join(idx['column_names'])} {unique}"
                        )
            
            return "\n".join(schema_parts)
    
    async def _get_mongodb_schema(
        self,
        connection_params: Dict[str, Any]
    ) -> str:
        """Get MongoDB schema by sampling documents"""
        with self.get_connection("mongodb", connection_params) as client:
            db_name = connection_params.get("database") or settings.MONGODB_DB
            db = client[db_name]
            
            schema_parts = []
            
            # Get all collections
            collections = db.list_collection_names()
            
            for collection_name in collections:
                schema_parts.append(f"\nCollection: {collection_name}")
                
                # Sample documents to infer schema
                collection = db[collection_name]
                sample = list(collection.find().limit(10))
                
                if sample:
                    # Get all unique field names
                    fields = set()
                    for doc in sample:
                        fields.update(doc.keys())
                    
                    schema_parts.append("Fields:")
                    for field in sorted(fields):
                        # Try to infer type from samples
                        types = set()
                        for doc in sample:
                            if field in doc:
                                types.add(type(doc[field]).__name__)
                        
                        schema_parts.append(
                            f"  - {field}: {', '.join(types)}"
                        )
            
            return "\n".join(schema_parts)
    
    async def _get_bigquery_schema(
        self,
        connection_params: Dict[str, Any]
    ) -> str:
        """Get BigQuery schema"""
        with self.get_connection("bigquery", connection_params) as client:
            dataset_id = connection_params.get("dataset")
            project_id = connection_params.get("project_id")
            
            schema_parts = [f"BigQuery Project: {project_id}"]
            schema_parts.append(f"Dataset: {dataset_id}\n")
            
            # List tables in dataset
            tables = client.list_tables(f"{project_id}.{dataset_id}")
            
            for table in tables:
                table_ref = client.get_table(f"{project_id}.{dataset_id}.{table.table_id}")
                schema_parts.append(f"\nTable: {table.table_id}")
                schema_parts.append(f"Rows: {table_ref.num_rows}")
                schema_parts.append("Columns:")
                
                for field in table_ref.schema:
                    schema_parts.append(f"  - {field.name}: {field.field_type} ({field.mode})")
            
            return "\n".join(schema_parts)
    
    async def _get_cassandra_schema(
        self,
        connection_params: Dict[str, Any]
    ) -> str:
        """Get Cassandra schema"""
        with self.get_connection("cassandra", connection_params) as session:
            keyspace = connection_params.get("keyspace")
            
            schema_parts = [f"Cassandra Keyspace: {keyspace}\n"]
            
            # Get all tables in keyspace
            rows = session.execute(
                "SELECT table_name FROM system_schema.tables WHERE keyspace_name = %s",
                [keyspace]
            )
            
            for row in rows:
                table_name = row.table_name
                schema_parts.append(f"\nTable: {table_name}")
                
                # Get columns for table
                columns = session.execute(
                    "SELECT column_name, type, kind FROM system_schema.columns WHERE keyspace_name = %s AND table_name = %s",
                    [keyspace, table_name]
                )
                
                schema_parts.append("Columns:")
                for col in columns:
                    schema_parts.append(f"  - {col.column_name}: {col.type} ({col.kind})")
            
            return "\n".join(schema_parts)
    
    async def _get_dynamodb_schema(
        self,
        connection_params: Dict[str, Any]
    ) -> str:
        """Get DynamoDB schema"""
        with self.get_connection("dynamodb", connection_params) as dynamodb:
            schema_parts = ["DynamoDB Tables:\n"]
            
            # List all tables
            client = dynamodb.meta.client
            tables = client.list_tables()
            
            for table_name in tables.get('TableNames', []):
                table = dynamodb.Table(table_name)
                table.load()
                
                schema_parts.append(f"\nTable: {table_name}")
                schema_parts.append(f"Item Count: {table.item_count}")
                schema_parts.append(f"Primary Key:")
                
                # Get key schema
                for key in table.key_schema:
                    key_type = "Partition Key" if key['KeyType'] == 'HASH' else "Sort Key"
                    schema_parts.append(f"  - {key['AttributeName']} ({key_type})")
                
                # Get attribute definitions
                schema_parts.append("Attributes:")
                for attr in table.attribute_definitions:
                    schema_parts.append(f"  - {attr['AttributeName']}: {attr['AttributeType']}")
            
            return "\n".join(schema_parts)
    
    async def execute_query(
        self,
        sql_query: str,
        database_type: str,
        connection_params: Dict[str, Any],
        timeout: int = None
    ) -> List[Dict[str, Any]]:
        """
        Execute SQL query and return results
        
        Args:
            sql_query: SQL query to execute
            database_type: Type of database
            connection_params: Connection parameters
            timeout: Query timeout in seconds
            
        Returns:
            List of result rows as dictionaries
        """
        logger.info(f"Executing query on {database_type}")
        
        if database_type == "mongodb":
            return await self._execute_mongodb_query(sql_query, connection_params)
        elif database_type == "bigquery":
            return await self._execute_bigquery_query(sql_query, connection_params, timeout)
        elif database_type == "cassandra":
            return await self._execute_cassandra_query(sql_query, connection_params)
        elif database_type == "dynamodb":
            return await self._execute_dynamodb_query(sql_query, connection_params)
        else:
            return await self._execute_sql_query(
                sql_query,
                database_type,
                connection_params,
                timeout
            )
    
    async def _execute_sql_query(
        self,
        sql_query: str,
        database_type: str,
        connection_params: Dict[str, Any],
        timeout: int = None
    ) -> List[Dict[str, Any]]:
        """Execute SQL query"""
        timeout = timeout or settings.MAX_QUERY_TIMEOUT
        
        with self.get_connection(database_type, connection_params) as conn:
            # Set query timeout
            if database_type == "postgresql":
                conn.execute(text(f"SET statement_timeout = {timeout * 1000}"))
            elif database_type == "mysql":
                conn.execute(text(f"SET SESSION max_execution_time = {timeout * 1000}"))
            
            # Execute query
            result = conn.execute(text(sql_query))
            
            # Convert to list of dicts
            columns = result.keys()
            rows = []
            
            for row in result.fetchmany(settings.MAX_RESULT_ROWS):
                rows.append(dict(zip(columns, row)))
            
            logger.info(f"Query executed successfully, {len(rows)} rows returned")
            return rows
    
    async def _execute_mongodb_query(
        self,
        query: str,
        connection_params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Execute MongoDB aggregation pipeline"""
        import json
        
        with self.get_connection("mongodb", connection_params) as client:
            db_name = connection_params.get("database") or settings.MONGODB_DB
            db = client[db_name]
            
            # Parse the query as JSON (should be aggregation pipeline)
            try:
                pipeline = json.loads(query)
                collection_name = pipeline[0].get("collection", "")
                
                if not collection_name:
                    raise ValueError("Collection name not specified in query")
                
                collection = db[collection_name]
                results = list(collection.aggregate(pipeline[1:]))
                
                # Convert ObjectId to string
                for result in results:
                    if "_id" in result:
                        result["_id"] = str(result["_id"])
                
                logger.info(f"MongoDB query executed, {len(results)} documents returned")
                return results
            except json.JSONDecodeError as e:
                logger.error(f"Invalid MongoDB query format: {str(e)}")
                raise ValueError("MongoDB query must be valid JSON aggregation pipeline")
    
    async def _execute_bigquery_query(
        self,
        sql_query: str,
        connection_params: Dict[str, Any],
        timeout: int = None
    ) -> List[Dict[str, Any]]:
        """Execute BigQuery query"""
        timeout = timeout or settings.MAX_QUERY_TIMEOUT
        
        with self.get_connection("bigquery", connection_params) as client:
            # Execute query with timeout
            query_job = client.query(sql_query, timeout=timeout)
            
            # Wait for results
            results = query_job.result(max_results=settings.MAX_RESULT_ROWS)
            
            # Convert to list of dicts
            rows = []
            for row in results:
                rows.append(dict(row.items()))
            
            logger.info(f"BigQuery query executed, {len(rows)} rows returned")
            return rows
    
    async def _execute_cassandra_query(
        self,
        cql_query: str,
        connection_params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Execute Cassandra CQL query"""
        with self.get_connection("cassandra", connection_params) as session:
            # Execute query
            result_set = session.execute(cql_query)
            
            # Convert to list of dicts
            rows = []
            for row in result_set:
                rows.append(dict(row._asdict()))
                if len(rows) >= settings.MAX_RESULT_ROWS:
                    break
            
            logger.info(f"Cassandra query executed, {len(rows)} rows returned")
            return rows
    
    async def _execute_dynamodb_query(
        self,
        query_json: str,
        connection_params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Execute DynamoDB query"""
        import json
        
        with self.get_connection("dynamodb", connection_params) as dynamodb:
            # Parse query JSON
            try:
                query_params = json.loads(query_json)
                table_name = query_params.pop("TableName")
                operation = query_params.pop("Operation", "scan")
                
                table = dynamodb.Table(table_name)
                
                # Execute operation
                if operation.lower() == "query":
                    response = table.query(**query_params)
                else:  # scan
                    response = table.scan(**query_params)
                
                items = response.get('Items', [])
                
                # Limit results
                items = items[:settings.MAX_RESULT_ROWS]
                
                logger.info(f"DynamoDB {operation} executed, {len(items)} items returned")
                return items
            
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON format for DynamoDB query")
    
    async def test_connection(
        self,
        database_type: str,
        connection_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Test database connection
        
        Returns:
            Connection test result with status and message
        """
        try:
            with self.get_connection(database_type, connection_params) as conn:
                if database_type == "mongodb":
                    # Test MongoDB connection
                    conn.server_info()
                else:
                    # Test SQL connection
                    conn.execute(text("SELECT 1"))
                
                return {
                    "status": "success",
                    "message": f"Successfully connected to {database_type} database"
                }
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to connect: {str(e)}"
            }
    
    async def get_sample_data(
        self,
        database_type: str,
        connection_params: Dict[str, Any],
        table_name: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get sample data from a table/collection"""
        logger.info(f"Fetching sample data from {table_name}")
        
        if database_type == "mongodb":
            with self.get_connection("mongodb", connection_params) as client:
                db_name = connection_params.get("database") or settings.MONGODB_DB
                db = client[db_name]
                collection = db[table_name]
                
                results = list(collection.find().limit(limit))
                
                for result in results:
                    if "_id" in result:
                        result["_id"] = str(result["_id"])
                
                return results
        else:
            query = f"SELECT * FROM {table_name} LIMIT {limit}"
            return await self._execute_sql_query(
                query,
                database_type,
                connection_params
            )
