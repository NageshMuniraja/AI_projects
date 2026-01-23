"""
Database API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, List
import logging

from app.services.database_manager import DatabaseManager
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)

db_manager = DatabaseManager()


class ConnectionTestRequest(BaseModel):
    """Database connection test request"""
    database_type: str = Field(..., description="Database type")
    connection_params: Dict[str, Any] = Field(..., description="Connection parameters")


class SchemaRequest(BaseModel):
    """Schema fetch request"""
    database_type: str
    connection_params: Dict[str, Any]


class TableSampleRequest(BaseModel):
    """Table sample data request"""
    database_type: str
    connection_params: Dict[str, Any]
    table_name: str
    limit: int = Field(default=10, ge=1, le=100)


@router.post("/test-connection")
async def test_connection(
    request: ConnectionTestRequest,
    current_user: User = Depends(get_current_user)
):
    """Test database connection"""
    logger.info(f"Testing connection to {request.database_type}")
    
    result = await db_manager.test_connection(
        request.database_type,
        request.connection_params
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.post("/schema")
async def get_schema(
    request: SchemaRequest,
    current_user: User = Depends(get_current_user)
):
    """Get database schema"""
    logger.info(f"Fetching schema for {request.database_type}")
    
    try:
        schema = await db_manager.get_schema(
            request.database_type,
            request.connection_params
        )
        
        return {
            "database_type": request.database_type,
            "schema": schema
        }
    except Exception as e:
        logger.error(f"Error fetching schema: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sample-data")
async def get_sample_data(
    request: TableSampleRequest,
    current_user: User = Depends(get_current_user)
):
    """Get sample data from a table"""
    logger.info(f"Fetching sample data from {request.table_name}")
    
    try:
        data = await db_manager.get_sample_data(
            request.database_type,
            request.connection_params,
            request.table_name,
            request.limit
        )
        
        return {
            "table_name": request.table_name,
            "row_count": len(data),
            "data": data
        }
    except Exception as e:
        logger.error(f"Error fetching sample data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/supported-databases")
async def get_supported_databases():
    """Get list of supported database types"""
    return {
        "databases": [
            {
                "type": "postgresql",
                "name": "PostgreSQL",
                "icon": "🐘",
                "category": "RDBMS"
            },
            {
                "type": "mysql",
                "name": "MySQL",
                "icon": "🐬",
                "category": "RDBMS"
            },
            {
                "type": "mariadb",
                "name": "MariaDB",
                "icon": "🦭",
                "category": "RDBMS"
            },
            {
                "type": "mssql",
                "name": "SQL Server",
                "icon": "🗄️",
                "category": "RDBMS"
            },
            {
                "type": "sqlite",
                "name": "SQLite",
                "icon": "💾",
                "category": "RDBMS"
            },
            {
                "type": "oracle",
                "name": "Oracle Database",
                "icon": "🏛️",
                "category": "RDBMS"
            },
            {
                "type": "db2",
                "name": "IBM DB2",
                "icon": "🔷",
                "category": "RDBMS"
            },
            {
                "type": "snowflake",
                "name": "Snowflake",
                "icon": "❄️",
                "category": "Cloud Warehouse"
            },
            {
                "type": "redshift",
                "name": "Amazon Redshift",
                "icon": "🔴",
                "category": "Cloud Warehouse"
            },
            {
                "type": "bigquery",
                "name": "Google BigQuery",
                "icon": "🔷",
                "category": "Cloud Warehouse"
            },
            {
                "type": "mongodb",
                "name": "MongoDB",
                "icon": "🍃",
                "category": "NoSQL"
            },
            {
                "type": "cassandra",
                "name": "Apache Cassandra",
                "icon": "💿",
                "category": "NoSQL"
            },
            {
                "type": "dynamodb",
                "name": "Amazon DynamoDB",
                "icon": "⚡",
                "category": "NoSQL"
            }
        ]
    }
