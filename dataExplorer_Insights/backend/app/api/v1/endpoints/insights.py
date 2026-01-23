"""
Insights endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List
import logging

from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/templates")
async def get_insight_templates(current_user: User = Depends(get_current_user)):
    """Get predefined insight templates"""
    return {
        "templates": [
            {
                "id": "revenue_analysis",
                "name": "Revenue Analysis",
                "description": "Analyze revenue trends and patterns",
                "queries": [
                    "What is the total revenue by month?",
                    "Which products generate the most revenue?",
                    "Show revenue growth rate over time"
                ]
            },
            {
                "id": "customer_analysis",
                "name": "Customer Analysis",
                "description": "Understand customer behavior and segments",
                "queries": [
                    "Who are the top 10 customers by revenue?",
                    "What is the customer retention rate?",
                    "Show customer acquisition trends"
                ]
            },
            {
                "id": "performance_metrics",
                "name": "Performance Metrics",
                "description": "Key performance indicators and metrics",
                "queries": [
                    "What are the key performance metrics?",
                    "Show conversion rates over time",
                    "Compare performance across regions"
                ]
            }
        ]
    }


@router.get("/sample-queries")
async def get_sample_queries():
    """Get sample natural language queries"""
    return {
        "queries": [
            "Show me total sales by month for the last year",
            "What are the top 10 products by revenue?",
            "Which customers have spent more than $10,000?",
            "Show me the average order value by customer segment",
            "What is the conversion rate trend over time?",
            "Find anomalies in daily transactions",
            "Compare sales between regions",
            "What products are frequently bought together?",
            "Show me customer churn rate by cohort",
            "What is the inventory turnover for each product?"
        ]
    }
