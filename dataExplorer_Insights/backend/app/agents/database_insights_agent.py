"""
Agentic AI Agent using LangGraph for database insights
Multi-step reasoning for complex analytical queries
"""

from typing import Dict, List, Any, Optional, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
import json
import logging

from app.core.config import settings
from app.services.sql_generator import SQLGenerator
from app.services.database_manager import DatabaseManager
from app.services.insights_analyzer import InsightsAnalyzer

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State for the agentic workflow"""
    user_query: str
    database_type: str
    connection_params: Dict[str, Any]
    schema_context: Optional[str]
    intent: Optional[str]
    sql_query: Optional[str]
    query_results: Optional[List[Dict]]
    insights: Optional[Dict[str, Any]]
    visualizations: Optional[List[Dict]]
    error: Optional[str]
    iterations: int
    final_response: Optional[Dict[str, Any]]


class DatabaseInsightsAgent:
    """
    Agentic AI agent for database insights using LangGraph
    Implements multi-step reasoning and tool use
    """
    
    def __init__(self):
        """Initialize the agent with LLM and tools"""
        # Initialize LLM
        if settings.OPENAI_API_KEY:
            self.llm = ChatOpenAI(
                model=settings.OPENAI_MODEL,
                temperature=settings.OPENAI_TEMPERATURE,
                api_key=settings.OPENAI_API_KEY
            )
        elif settings.ANTHROPIC_API_KEY:
            self.llm = ChatAnthropic(
                model=settings.ANTHROPIC_MODEL,
                api_key=settings.ANTHROPIC_API_KEY
            )
        else:
            raise ValueError("No LLM API key configured")
        
        # Initialize tools
        self.sql_generator = SQLGenerator(self.llm)
        self.db_manager = DatabaseManager()
        self.insights_analyzer = InsightsAnalyzer(self.llm)
        
        # Build the agent graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("understand_intent", self._understand_intent)
        workflow.add_node("get_schema", self._get_schema)
        workflow.add_node("generate_sql", self._generate_sql)
        workflow.add_node("execute_query", self._execute_query)
        workflow.add_node("analyze_results", self._analyze_results)
        workflow.add_node("generate_insights", self._generate_insights)
        workflow.add_node("create_visualizations", self._create_visualizations)
        workflow.add_node("handle_error", self._handle_error)
        
        # Set entry point
        workflow.set_entry_point("understand_intent")
        
        # Add edges
        workflow.add_edge("understand_intent", "get_schema")
        workflow.add_edge("get_schema", "generate_sql")
        workflow.add_conditional_edges(
            "generate_sql",
            self._should_execute_or_error,
            {
                "execute": "execute_query",
                "error": "handle_error"
            }
        )
        workflow.add_conditional_edges(
            "execute_query",
            self._should_analyze_or_error,
            {
                "analyze": "analyze_results",
                "error": "handle_error",
                "retry": "generate_sql"
            }
        )
        workflow.add_edge("analyze_results", "generate_insights")
        workflow.add_edge("generate_insights", "create_visualizations")
        workflow.add_edge("create_visualizations", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    async def _understand_intent(self, state: AgentState) -> AgentState:
        """Step 1: Understand user intent"""
        logger.info(f"Understanding intent for query: {state['user_query']}")
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an expert at understanding database query intentions.
            Classify the user's query into one of these categories:
            - metrics: Request for specific metrics (count, sum, average, etc.)
            - insights: Request for data analysis and patterns
            - comparison: Comparing different data segments
            - trend: Looking for trends over time
            - distribution: Understanding data distribution
            - anomaly: Finding unusual patterns
            - custom: Custom query
            
            Also identify key entities and filters mentioned.
            Respond with a JSON object containing: intent, entities, filters, time_range."""),
            HumanMessage(content=state["user_query"])
        ])
        
        response = await self.llm.ainvoke(prompt.format_messages())
        
        try:
            intent_data = json.loads(response.content)
            state["intent"] = intent_data.get("intent", "custom")
            logger.info(f"Identified intent: {state['intent']}")
        except json.JSONDecodeError:
            state["intent"] = "custom"
            logger.warning("Could not parse intent, using default")
        
        state["iterations"] = state.get("iterations", 0) + 1
        return state
    
    async def _get_schema(self, state: AgentState) -> AgentState:
        """Step 2: Get database schema context"""
        logger.info("Fetching database schema")
        
        try:
            schema = await self.db_manager.get_schema(
                state["database_type"],
                state["connection_params"]
            )
            state["schema_context"] = schema
            logger.info("Schema fetched successfully")
        except Exception as e:
            logger.error(f"Error fetching schema: {str(e)}")
            state["error"] = f"Schema fetch error: {str(e)}"
        
        return state
    
    async def _generate_sql(self, state: AgentState) -> AgentState:
        """Step 3: Generate SQL query from natural language"""
        logger.info("Generating SQL query")
        
        try:
            sql_query = await self.sql_generator.generate(
                user_query=state["user_query"],
                schema=state["schema_context"],
                database_type=state["database_type"],
                intent=state["intent"]
            )
            state["sql_query"] = sql_query
            logger.info(f"Generated SQL: {sql_query}")
        except Exception as e:
            logger.error(f"Error generating SQL: {str(e)}")
            state["error"] = f"SQL generation error: {str(e)}"
        
        return state
    
    async def _execute_query(self, state: AgentState) -> AgentState:
        """Step 4: Execute the SQL query"""
        logger.info("Executing SQL query")
        
        try:
            results = await self.db_manager.execute_query(
                sql_query=state["sql_query"],
                database_type=state["database_type"],
                connection_params=state["connection_params"]
            )
            state["query_results"] = results
            logger.info(f"Query executed successfully, {len(results)} rows returned")
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            state["error"] = f"Query execution error: {str(e)}"
        
        return state
    
    async def _analyze_results(self, state: AgentState) -> AgentState:
        """Step 5: Analyze query results"""
        logger.info("Analyzing query results")
        
        try:
            analysis = await self.insights_analyzer.analyze_data(
                data=state["query_results"],
                query=state["user_query"],
                intent=state["intent"]
            )
            state["insights"] = analysis
            logger.info("Results analyzed successfully")
        except Exception as e:
            logger.error(f"Error analyzing results: {str(e)}")
            state["error"] = f"Analysis error: {str(e)}"
        
        return state
    
    async def _generate_insights(self, state: AgentState) -> AgentState:
        """Step 6: Generate natural language insights"""
        logger.info("Generating insights")
        
        try:
            insights = await self.insights_analyzer.generate_insights(
                data=state["query_results"],
                analysis=state["insights"],
                user_query=state["user_query"]
            )
            state["insights"]["narrative"] = insights
            logger.info("Insights generated successfully")
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            state["error"] = f"Insight generation error: {str(e)}"
        
        return state
    
    async def _create_visualizations(self, state: AgentState) -> AgentState:
        """Step 7: Create visualization recommendations"""
        logger.info("Creating visualization recommendations")
        
        try:
            viz_configs = await self.insights_analyzer.recommend_visualizations(
                data=state["query_results"],
                insights=state["insights"]
            )
            state["visualizations"] = viz_configs
            
            # Build final response
            state["final_response"] = {
                "query": state["user_query"],
                "intent": state["intent"],
                "sql_query": state["sql_query"],
                "results": state["query_results"],
                "insights": state["insights"],
                "visualizations": state["visualizations"],
                "metadata": {
                    "rows_returned": len(state["query_results"]),
                    "iterations": state["iterations"],
                    "database_type": state["database_type"]
                }
            }
            logger.info("Visualization recommendations created")
        except Exception as e:
            logger.error(f"Error creating visualizations: {str(e)}")
            state["error"] = f"Visualization error: {str(e)}"
        
        return state
    
    async def _handle_error(self, state: AgentState) -> AgentState:
        """Handle errors in the workflow"""
        logger.error(f"Handling error: {state.get('error')}")
        
        state["final_response"] = {
            "error": state["error"],
            "query": state["user_query"],
            "iterations": state["iterations"]
        }
        
        return state
    
    def _should_execute_or_error(self, state: AgentState) -> str:
        """Conditional edge: check if SQL was generated successfully"""
        if state.get("error"):
            return "error"
        return "execute"
    
    def _should_analyze_or_error(self, state: AgentState) -> str:
        """Conditional edge: check if query executed successfully"""
        if state.get("error"):
            if state["iterations"] < settings.AGENT_MAX_ITERATIONS:
                return "retry"
            return "error"
        return "analyze"
    
    async def run(
        self,
        user_query: str,
        database_type: str,
        connection_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run the agentic workflow
        
        Args:
            user_query: Natural language query from user
            database_type: Type of database (postgres, mysql, mssql, sqlite, mongodb)
            connection_params: Database connection parameters
            
        Returns:
            Complete response with insights and visualizations
        """
        logger.info(f"Starting agent run for query: {user_query}")
        
        initial_state: AgentState = {
            "user_query": user_query,
            "database_type": database_type,
            "connection_params": connection_params,
            "schema_context": None,
            "intent": None,
            "sql_query": None,
            "query_results": None,
            "insights": None,
            "visualizations": None,
            "error": None,
            "iterations": 0,
            "final_response": None
        }
        
        # Run the graph
        final_state = await self.graph.ainvoke(initial_state)
        
        logger.info("Agent run completed")
        return final_state["final_response"]
