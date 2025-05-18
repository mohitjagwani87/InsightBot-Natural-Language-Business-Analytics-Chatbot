import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
import json
import requests
from typing import List, Dict, Any

# Load environment variables
load_dotenv()

# Constants for HuggingFace
API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
HEADERS = {"Authorization": "Bearer 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"}

def query_huggingface(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Make a request to HuggingFace's inference API."""
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    return response.json()

# Database connection
def get_db_connection():
    connection_string = os.getenv("DATABASE_URL")
    if not connection_string:
        st.error("Database connection string not found in environment variables!")
        return None
    return create_engine(connection_string)

def generate_sql_query(question: str) -> str:
    """Generate SQL query from natural language question using predefined templates."""
    # Common SQL query templates
    templates = {
        "top": "SELECT {columns} FROM {table} ORDER BY {order_column} DESC LIMIT {limit}",
        "total": "SELECT {group_column}, SUM({value_column}) as total FROM {table} GROUP BY {group_column}",
        "average": "SELECT {group_column}, AVG({value_column}) as average FROM {table} GROUP BY {group_column}",
        "count": "SELECT {group_column}, COUNT(*) as count FROM {table} GROUP BY {group_column}"
    }
    
    # Analyze the question to determine which template to use
    question_lower = question.lower()
    
    try:
        if "top" in question_lower or "best" in question_lower:
            if "products" in question_lower or "product" in question_lower:
                return """
                SELECT p.name as product_name, 
                       SUM(s.quantity) as total_quantity,
                       SUM(s.total_amount) as total_sales
                FROM sales s
                JOIN products p ON s.product_id = p.product_id
                GROUP BY p.product_id, p.name
                ORDER BY total_sales DESC
                LIMIT 5
                """
        elif "sales by region" in question_lower:
            return """
            SELECT c.region, 
                   SUM(s.total_amount) as total_sales,
                   COUNT(DISTINCT s.customer_id) as customer_count
            FROM sales s
            JOIN customers c ON s.customer_id = c.customer_id
            GROUP BY c.region
            ORDER BY total_sales DESC
            """
        elif "all products" in question_lower:
            return """
            SELECT p.name, 
                   p.category,
                   p.price,
                   p.stock
            FROM products p
            ORDER BY p.category, p.name
            """
        elif "customer" in question_lower and "spending" in question_lower:
            return """
            SELECT c.name as customer_name,
                   c.region,
                   SUM(s.total_amount) as total_spent
            FROM sales s
            JOIN customers c ON s.customer_id = c.customer_id
            GROUP BY c.customer_id, c.name, c.region
            ORDER BY total_spent DESC
            LIMIT 10
            """
        else:
            # Default to a simple product sales query
            return """
            SELECT p.name as product_name,
                   p.category,
                   COUNT(*) as number_of_sales,
                   SUM(s.quantity) as total_quantity,
                   SUM(s.total_amount) as total_revenue
            FROM sales s
            JOIN products p ON s.product_id = p.product_id
            GROUP BY p.product_id, p.name, p.category
            ORDER BY total_revenue DESC
            """
    except Exception as e:
        st.error(f"Error generating SQL query: {str(e)}")
        return None

def analyze_data(df: pd.DataFrame, question: str) -> Dict[str, Any]:
    """Generate analysis and visualization suggestions based on the data structure."""
    try:
        # Get basic statistics
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
        categorical_cols = df.select_dtypes(include=['object']).columns
        
        analysis = []
        insights = []
        visualizations = []
        
        # Basic data summary
        total_rows = len(df)
        analysis.append(f"Analysis of {total_rows} records:")
        
        # Analyze numeric columns
        for col in numeric_cols:
            total = df[col].sum()
            avg = df[col].mean()
            analysis.append(f"- Total {col}: {total:,.2f}")
            analysis.append(f"- Average {col}: {avg:,.2f}")
            
            # Add insights
            if "amount" in col.lower() or "sales" in col.lower():
                insights.append(f"Total {col} is {total:,.2f}")
                insights.append(f"Average {col} per record is {avg:,.2f}")
        
        # Generate visualization suggestions
        if len(categorical_cols) > 0 and len(numeric_cols) > 0:
            # Bar chart for categorical vs numeric
            visualizations.append({
                "type": "bar",
                "x": categorical_cols[0],
                "y": numeric_cols[0],
                "title": f"{numeric_cols[0]} by {categorical_cols[0]}"
            })
            
            # Pie chart for distribution
            visualizations.append({
                "type": "pie",
                "x": categorical_cols[0],
                "y": numeric_cols[0],
                "title": f"Distribution of {numeric_cols[0]} by {categorical_cols[0]}"
            })
        
        return {
            "analysis": "\n".join(analysis),
            "insights": insights,
            "visualizations": visualizations
        }
    except Exception as e:
        st.error(f"Error analyzing data: {str(e)}")
        return None

def create_visualization(df, viz_config):
    """Create a Plotly visualization based on the configuration."""
    try:
        chart_type = viz_config["type"].lower()
        if chart_type == "bar":
            fig = px.bar(df, x=viz_config["x"], y=viz_config["y"], title=viz_config["title"])
        elif chart_type == "line":
            fig = px.line(df, x=viz_config["x"], y=viz_config["y"], title=viz_config["title"])
        elif chart_type == "scatter":
            fig = px.scatter(df, x=viz_config["x"], y=viz_config["y"], title=viz_config["title"])
        elif chart_type == "pie":
            fig = px.pie(df, names=viz_config["x"], values=viz_config["y"], title=viz_config["title"])
        else:
            return None
        return fig
    except Exception as e:
        st.error(f"Error creating visualization: {str(e)}")
        return None

# Streamlit UI
st.set_page_config(page_title="SQL Chat Assistant", layout="wide")
st.title("Business Intelligence Chat Assistant")

# Check for API key
if not os.getenv("OPENAI_API_KEY"):
    st.error("Please set your OpenAI API key in the .env file!")
    st.stop()

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Main input
question = st.text_area("Ask your business question:", height=100)

if st.button("Analyze"):
    if not question:
        st.warning("Please enter a question!")
    else:
        with st.spinner("Analyzing your question..."):
            # Generate SQL query
            sql_query = generate_sql_query(question)
            if sql_query:
                st.code(sql_query, language="sql")
                
                try:
                    # Execute query
                    engine = get_db_connection()
                    if engine:
                        df = pd.read_sql_query(sql_query, engine)
                        
                        # Display raw data in an expander
                        with st.expander("View Raw Data"):
                            st.dataframe(df)
                        
                        # Analyze the data
                        analysis_result = analyze_data(df, question)
                        if analysis_result:
                            # Display natural language analysis
                            st.write("### Analysis")
                            st.write(analysis_result["analysis"])
                            
                            # Display insights
                            st.write("### Key Insights")
                            for insight in analysis_result["insights"]:
                                st.write(f"• {insight}")
                            
                            # Create and display visualizations
                            st.write("### Visualizations")
                            cols = st.columns(2)
                            for idx, viz_config in enumerate(analysis_result["visualizations"]):
                                fig = create_visualization(df, viz_config)
                                if fig:
                                    cols[idx % 2].plotly_chart(fig, use_container_width=True)
                            
                            # Add to chat history
                            st.session_state.chat_history.append({
                                "question": question,
                                "sql": sql_query,
                                "analysis": analysis_result
                            })
                            
                except Exception as e:
                    st.error(f"Error executing query: {str(e)}")

# Display chat history
if st.session_state.chat_history:
    st.write("### Previous Analyses")
    for idx, item in enumerate(reversed(st.session_state.chat_history)):
        with st.expander(f"Question: {item['question'][:100]}..."):
            st.code(item["sql"], language="sql")
            st.write(item["analysis"]["analysis"]) 
