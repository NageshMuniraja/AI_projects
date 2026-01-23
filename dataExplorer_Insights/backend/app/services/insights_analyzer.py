"""
Insights Analyzer - Generate insights and recommendations from data
Uses LLM to create natural language insights and visualization recommendations
"""

from typing import Dict, List, Any, Optional
from langchain.prompts import ChatPromptTemplate
from langchain.schema import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
import pandas as pd
import numpy as np
import logging
import json

logger = logging.getLogger(__name__)


class InsightsAnalyzer:
    """Analyze data and generate insights using LLM"""
    
    def __init__(self, llm: ChatOpenAI):
        """Initialize with LLM instance"""
        self.llm = llm
    
    async def analyze_data(
        self,
        data: List[Dict[str, Any]],
        query: str,
        intent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze query results statistically
        
        Args:
            data: Query results as list of dictionaries
            query: Original user query
            intent: Query intent classification
            
        Returns:
            Statistical analysis results
        """
        logger.info("Performing statistical analysis on data")
        
        if not data:
            return {
                "row_count": 0,
                "message": "No data returned from query"
            }
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(data)
        
        analysis = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "statistics": {}
        }
        
        # Analyze numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            analysis["statistics"]["numeric"] = {}
            
            for col in numeric_cols:
                col_stats = {
                    "mean": float(df[col].mean()),
                    "median": float(df[col].median()),
                    "std": float(df[col].std()),
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                    "sum": float(df[col].sum()),
                    "null_count": int(df[col].isnull().sum())
                }
                analysis["statistics"]["numeric"][col] = col_stats
        
        # Analyze categorical columns
        categorical_cols = df.select_dtypes(include=["object"]).columns
        if len(categorical_cols) > 0:
            analysis["statistics"]["categorical"] = {}
            
            for col in categorical_cols:
                value_counts = df[col].value_counts()
                col_stats = {
                    "unique_count": int(df[col].nunique()),
                    "most_common": value_counts.head(5).to_dict(),
                    "null_count": int(df[col].isnull().sum())
                }
                analysis["statistics"]["categorical"][col] = col_stats
        
        # Detect patterns
        analysis["patterns"] = await self._detect_patterns(df, intent)
        
        logger.info("Statistical analysis completed")
        return analysis
    
    async def _detect_patterns(
        self,
        df: pd.DataFrame,
        intent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Detect patterns in the data"""
        patterns = {
            "trends": [],
            "anomalies": [],
            "correlations": []
        }
        
        # Detect trends in time series data
        date_cols = df.select_dtypes(include=["datetime64"]).columns
        if len(date_cols) > 0:
            for date_col in date_cols:
                # Sort by date and check for trends
                df_sorted = df.sort_values(date_col)
                numeric_cols = df_sorted.select_dtypes(include=[np.number]).columns
                
                for num_col in numeric_cols:
                    # Simple trend detection using correlation with index
                    correlation = df_sorted[num_col].corr(
                        pd.Series(range(len(df_sorted)))
                    )
                    
                    if abs(correlation) > 0.7:
                        trend_direction = "increasing" if correlation > 0 else "decreasing"
                        patterns["trends"].append({
                            "column": num_col,
                            "direction": trend_direction,
                            "strength": abs(correlation)
                        })
        
        # Detect outliers using IQR method
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            
            outliers = df[
                (df[col] < (Q1 - 1.5 * IQR)) | 
                (df[col] > (Q3 + 1.5 * IQR))
            ]
            
            if len(outliers) > 0:
                patterns["anomalies"].append({
                    "column": col,
                    "count": len(outliers),
                    "percentage": (len(outliers) / len(df)) * 100
                })
        
        # Detect correlations between numeric columns
        if len(numeric_cols) > 1:
            corr_matrix = df[numeric_cols].corr()
            
            for i in range(len(numeric_cols)):
                for j in range(i + 1, len(numeric_cols)):
                    corr_value = corr_matrix.iloc[i, j]
                    
                    if abs(corr_value) > 0.7:
                        patterns["correlations"].append({
                            "column1": numeric_cols[i],
                            "column2": numeric_cols[j],
                            "correlation": float(corr_value),
                            "strength": "strong" if abs(corr_value) > 0.9 else "moderate"
                        })
        
        return patterns
    
    async def generate_insights(
        self,
        data: List[Dict[str, Any]],
        analysis: Dict[str, Any],
        user_query: str
    ) -> str:
        """
        Generate natural language insights from analysis
        
        Args:
            data: Original query results
            analysis: Statistical analysis results
            user_query: Original user query
            
        Returns:
            Natural language insights
        """
        logger.info("Generating natural language insights")
        
        # Prepare analysis summary for LLM
        analysis_summary = json.dumps(analysis, indent=2)
        
        # Prepare sample data
        sample_data = json.dumps(data[:5], indent=2) if data else "[]"
        
        system_prompt = """You are an expert data analyst. Your task is to generate clear, 
actionable insights from data analysis results. 

Provide:
1. Key findings (3-5 bullet points)
2. Notable patterns or trends
3. Anomalies or outliers
4. Actionable recommendations
5. Context-aware interpretation based on the user's question

Be concise, specific, and focus on what matters most to answer the user's question.
Use business-friendly language, avoiding technical jargon when possible."""

        user_prompt = f"""User Query: {user_query}

Statistical Analysis:
{analysis_summary}

Sample Data (first 5 rows):
{sample_data}

Generate insightful analysis and recommendations:"""

        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        
        response = await self.llm.ainvoke(prompt.format_messages())
        insights = response.content
        
        logger.info("Insights generated successfully")
        return insights
    
    async def recommend_visualizations(
        self,
        data: List[Dict[str, Any]],
        insights: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Recommend appropriate visualizations for the data
        
        Args:
            data: Query results
            insights: Analysis insights
            
        Returns:
            List of visualization configurations
        """
        logger.info("Recommending visualizations")
        
        if not data:
            return []
        
        df = pd.DataFrame(data)
        recommendations = []
        
        # Get column types
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=["object"]).columns.tolist()
        date_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()
        
        # Recommend based on data characteristics
        
        # 1. Time series visualization
        if date_cols and numeric_cols:
            recommendations.append({
                "type": "line",
                "title": "Trend Over Time",
                "x_axis": date_cols[0],
                "y_axis": numeric_cols[0],
                "description": "Shows how values change over time",
                "priority": 1
            })
        
        # 2. Distribution visualization
        if numeric_cols:
            recommendations.append({
                "type": "histogram",
                "title": f"Distribution of {numeric_cols[0]}",
                "column": numeric_cols[0],
                "description": "Shows the frequency distribution of values",
                "priority": 2
            })
        
        # 3. Categorical comparison
        if categorical_cols and numeric_cols:
            # Check cardinality
            unique_count = df[categorical_cols[0]].nunique()
            
            if unique_count <= 10:
                recommendations.append({
                    "type": "bar",
                    "title": f"{numeric_cols[0]} by {categorical_cols[0]}",
                    "x_axis": categorical_cols[0],
                    "y_axis": numeric_cols[0],
                    "description": "Compares values across categories",
                    "priority": 1
                })
            
            if unique_count <= 7:
                recommendations.append({
                    "type": "pie",
                    "title": f"Distribution by {categorical_cols[0]}",
                    "category": categorical_cols[0],
                    "value": numeric_cols[0],
                    "description": "Shows proportion of each category",
                    "priority": 3
                })
        
        # 4. Correlation heatmap
        if len(numeric_cols) >= 2:
            recommendations.append({
                "type": "heatmap",
                "title": "Correlation Matrix",
                "columns": numeric_cols[:5],  # Limit to 5 columns
                "description": "Shows relationships between numeric variables",
                "priority": 3
            })
        
        # 5. Scatter plot for correlations
        if len(numeric_cols) >= 2:
            recommendations.append({
                "type": "scatter",
                "title": f"{numeric_cols[0]} vs {numeric_cols[1]}",
                "x_axis": numeric_cols[0],
                "y_axis": numeric_cols[1],
                "description": "Shows relationship between two variables",
                "priority": 2
            })
        
        # 6. Box plot for outlier detection
        if numeric_cols and insights.get("patterns", {}).get("anomalies"):
            recommendations.append({
                "type": "box",
                "title": "Outlier Detection",
                "columns": [
                    anomaly["column"] 
                    for anomaly in insights["patterns"]["anomalies"][:3]
                ],
                "description": "Identifies outliers and data distribution",
                "priority": 2
            })
        
        # Sort by priority
        recommendations.sort(key=lambda x: x["priority"])
        
        logger.info(f"Generated {len(recommendations)} visualization recommendations")
        return recommendations
    
    async def generate_metrics_summary(
        self,
        data: List[Dict[str, Any]],
        query: str
    ) -> Dict[str, Any]:
        """
        Generate high-level metrics summary
        
        Args:
            data: Query results
            query: Original query
            
        Returns:
            Metrics summary
        """
        logger.info("Generating metrics summary")
        
        if not data:
            return {
                "total_records": 0,
                "status": "no_data"
            }
        
        df = pd.DataFrame(data)
        
        summary = {
            "total_records": len(df),
            "key_metrics": {}
        }
        
        # Extract key metrics from numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            summary["key_metrics"][col] = {
                "total": float(df[col].sum()),
                "average": float(df[col].mean()),
                "maximum": float(df[col].max()),
                "minimum": float(df[col].min())
            }
        
        logger.info("Metrics summary generated")
        return summary
