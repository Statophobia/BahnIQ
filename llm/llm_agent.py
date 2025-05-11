from langchain_groq.chat_models import ChatGroq
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.sql_database import SQLDatabase

import os
from dotenv import load_dotenv

from pathlib import Path

load_dotenv()

db_path = Path('data')/'db_data.db'
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

def get_sql_agent():
    db = SQLDatabase.from_uri("duckdb:///" + str(db_path.resolve()))

    llm = ChatGroq(
        model_name="gemma2-9b-it",
        #model_name='llama3-8b-8192',
        api_key=GROQ_API_KEY,
        temperature=0.0
    )

    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    agent = create_sql_agent(
        llm=llm,
        toolkit=toolkit,
        verbose=False,
        handle_parsing_errors=True,
        max_iterations=10,
        time_limit=60
    )
    return agent
