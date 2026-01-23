"""
SQL Generator using LLM
Converts natural language to SQL queries for various databases
"""

from typing import Dict, Any, Optional
from langchain.prompts import ChatPromptTemplate
from langchain.schema import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
import logging

logger = logging.getLogger(__name__)


class SQLGenerator:
    """Generate SQL from natural language using LLM"""
    
    def __init__(self, llm: ChatOpenAI):
        """Initialize with LLM instance"""
        self.llm = llm
        
        # Database-specific SQL dialects
        self.dialect_instructions = {
            "postgresql": "Use PostgreSQL syntax with LIMIT for pagination",
            "mysql": "Use MySQL syntax with LIMIT for pagination",
            "mariadb": "Use MariaDB (MySQL-compatible) syntax with LIMIT for pagination",
            "mssql": "Use SQL Server syntax with TOP or OFFSET-FETCH for pagination",
            "sqlite": "Use SQLite syntax with LIMIT for pagination",
            "mongodb": "Generate MongoDB aggregation pipeline (JSON format)",
            "snowflake": "Use Snowflake SQL syntax with LIMIT for pagination, supports QUALIFY and advanced analytics",
            "redshift": "Use Amazon Redshift (PostgreSQL-compatible) syntax with LIMIT for pagination",
            "bigquery": "Use Google BigQuery Standard SQL syntax with LIMIT for pagination",
            "oracle": "Use Oracle SQL syntax with ROWNUM or FETCH FIRST for pagination",
            "db2": "Use IBM DB2 syntax with FETCH FIRST for pagination",
            "cassandra": "Generate Cassandra CQL (not SQL) - use SELECT with LIMIT and ALLOW FILTERING sparingly",
            "dynamodb": "Generate DynamoDB query JSON format with TableName, KeyConditionExpression, or FilterExpression"
        }
    
    async def generate(
        self,
        user_query: str,
        schema: str,
        database_type: str,
        intent: Optional[str] = None
    ) -> str:
        """
        Generate SQL query from natural language
        
        Args:
            user_query: User's natural language question
            schema: Database schema context
            database_type: Type of database
            intent: Query intent classification
            
        Returns:
            SQL query string
        """
        logger.info(f"Generating SQL for database type: {database_type}")
        
        dialect_instruction = self.dialect_instructions.get(
            database_type,
            "Use standard SQL syntax"
        )
        
        system_prompt = f"""You are an expert SQL generator. Your task is to convert natural language queries 
into accurate SQL queries based on the provided database schema.

Database Type: {database_type}
Dialect Instructions: {dialect_instruction}

Guidelines:
1. Only use tables and columns that exist in the provided schema
2. Generate efficient, optimized queries
3. Handle aggregations, joins, and filtering correctly
4. Include appropriate WHERE clauses for filtering
5. Use proper date/time functions for temporal queries
6. Add ORDER BY for meaningful ordering
7. Include LIMIT to prevent overwhelming results (default: 1000 rows)
8. Use appropriate GROUP BY for aggregations
9. Handle NULL values appropriately
10. Return ONLY the SQL query, no explanations

Query Intent: {intent if intent else 'general query'}

Database Schema:
{schema}

Generate a SQL query for the following request. Return ONLY the SQL query without any markdown formatting or explanations:"""

        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_query)
        ])
        
        response = await self.llm.ainvoke(prompt.format_messages())
        sql_query = response.content.strip()
        
        # Clean up the response
        sql_query = self._clean_sql(sql_query)
        
        logger.info(f"Generated SQL: {sql_query}")
        return sql_query
    
    def _clean_sql(self, sql: str) -> str:
        """Clean up the generated SQL query"""
        # Remove markdown code blocks
        sql = sql.replace("```sql", "").replace("```", "")
        
        # Remove leading/trailing whitespace
        sql = sql.strip()
        
        # Remove any explanatory text before or after the query
        lines = sql.split("\n")
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip comment lines or explanations
            if line and not line.startswith("#") and not line.startswith("--"):
                cleaned_lines.append(line)
        
        sql = " ".join(cleaned_lines)
        
        return sql
    
    async def validate_sql(
        self,
        sql_query: str,
        database_type: str
    ) -> Dict[str, Any]:
        """
        Validate SQL query for syntax and safety
        
        Args:
            sql_query: SQL query to validate
            database_type: Type of database
            
        Returns:
            Validation result with is_valid flag and messages
        """
        validation_result = {
            "is_valid": True,
            "warnings": [],
            "errors": []
        }
        
        # Check for dangerous operations
        dangerous_keywords = ["DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE"]
        upper_sql = sql_query.upper()
        
        for keyword in dangerous_keywords:
            if keyword in upper_sql:
                validation_result["is_valid"] = False
                validation_result["errors"].append(
                    f"Dangerous operation detected: {keyword}"
                )
        
        # Check for SQL injection patterns
        injection_patterns = ["';", "--", "/*", "*/", "xp_", "sp_"]
        for pattern in injection_patterns:
            if pattern in sql_query:
                validation_result["warnings"].append(
                    f"Potential SQL injection pattern detected: {pattern}"
                )
        
        # Validate database-specific syntax (basic checks)
        if database_type == "mssql" and "LIMIT" in upper_sql:
            validation_result["warnings"].append(
                "LIMIT is not supported in SQL Server, use TOP or OFFSET-FETCH"
            )
        
        logger.info(f"SQL validation result: {validation_result}")
        return validation_result
    
    async def optimize_query(
        self,
        sql_query: str,
        schema: str,
        database_type: str
    ) -> str:
        """
        Optimize SQL query for performance
        
        Args:
            sql_query: Original SQL query
            schema: Database schema
            database_type: Type of database
            
        Returns:
            Optimized SQL query
        """
        logger.info("Optimizing SQL query")
        
        system_prompt = f"""You are an expert SQL query optimizer for {database_type}.
Given the following SQL query and schema, optimize it for better performance.

Consider:
1. Adding appropriate indexes (as comments)
2. Rewriting subqueries as JOINs where beneficial
3. Using EXPLAIN-friendly patterns
4. Avoiding SELECT *
5. Using appropriate WHERE clause ordering
6. Minimizing function calls in WHERE clauses

Original Query:
{sql_query}

Schema:
{schema}

Return the optimized SQL query with comments explaining optimizations:"""

        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_prompt),
            HumanMessage(content="Optimize this query")
        ])
        
        response = await self.llm.ainvoke(prompt.format_messages())
        optimized_query = self._clean_sql(response.content)
        
        logger.info(f"Optimized SQL: {optimized_query}")
        return optimized_query
