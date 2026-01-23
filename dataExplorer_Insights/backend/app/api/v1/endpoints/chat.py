"""
Chat API endpoints for natural language queries
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import logging

from app.agents.database_insights_agent import DatabaseInsightsAgent
from app.services.cache_manager import CacheManager
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize agent and cache
agent = DatabaseInsightsAgent()
cache = CacheManager()


class ChatRequest(BaseModel):
    """Chat request model"""
    query: str = Field(..., description="Natural language query", min_length=1)
    database_type: str = Field(..., description="Database type (postgresql, mysql, mssql, sqlite, mongodb)")
    connection_params: Dict[str, Any] = Field(..., description="Database connection parameters")
    use_cache: bool = Field(default=True, description="Whether to use cached results")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the top 10 customers by total revenue?",
                "database_type": "postgresql",
                "connection_params": {
                    "host": "localhost",
                    "port": 5432,
                    "user": "postgres",
                    "password": "password",
                    "database": "sales_db"
                }
            }
        }


class ChatResponse(BaseModel):
    """Chat response model"""
    query: str
    intent: Optional[str]
    sql_query: Optional[str]
    results: list
    insights: Dict[str, Any]
    visualizations: list
    metadata: Dict[str, Any]
    cached: bool = False


@router.post("/query", response_model=ChatResponse)
async def process_natural_language_query(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Process natural language query and return insights
    
    This endpoint:
    1. Understands user intent
    2. Generates SQL query
    3. Executes query on specified database
    4. Analyzes results
    5. Generates insights and visualizations
    """
    logger.info(f"Processing query from user {current_user.id}: {request.query}")
    
    try:
        # Check cache first
        cache_key = cache.generate_key(
            request.query,
            request.database_type,
            request.connection_params
        )
        
        if request.use_cache:
            cached_result = await cache.get(cache_key)
            if cached_result:
                logger.info("Returning cached result")
                cached_result["cached"] = True
                return cached_result
        
        # Run the agentic workflow
        result = await agent.run(
            user_query=request.query,
            database_type=request.database_type,
            connection_params=request.connection_params
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        response = ChatResponse(
            query=result["query"],
            intent=result.get("intent"),
            sql_query=result.get("sql_query"),
            results=result.get("results", []),
            insights=result.get("insights", {}),
            visualizations=result.get("visualizations", []),
            metadata=result.get("metadata", {}),
            cached=False
        )
        
        # Cache the result
        if request.use_cache:
            background_tasks.add_task(
                cache.set,
                cache_key,
                response.dict()
            )
        
        # Log query history
        background_tasks.add_task(
            log_query_history,
            current_user.id,
            request.query,
            result
        )
        
        logger.info("Query processed successfully")
        return response
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process query: {str(e)}"
        )


@router.post("/streaming")
async def stream_query_results(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Stream query results in real-time (for long-running queries)
    """
    # TODO: Implement streaming using Server-Sent Events (SSE)
    pass


async def log_query_history(
    user_id: int,
    query: str,
    result: Dict[str, Any]
):
    """Log query to history (background task)"""
    # TODO: Implement query history logging to database
    logger.info(f"Logged query history for user {user_id}")
