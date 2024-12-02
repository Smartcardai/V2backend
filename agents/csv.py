from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain.agents import AgentType
import pandas as pd
import io
import os
from typing import List
from component.response import llm_key


def process_with_pandas_agent(csv_content_list: List[str], query: str) -> str:
    """
    Process CSV data using Pandas Agent
    
    Args:
        csv_content_list: List of CSV strings from Firebase
        query: Question to ask about the data
    Returns:
        str: Agent's response to the query
    """
    try:
        # Initialize LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=llm_key,
            temperature=0.1,
            max_output_tokens=2000
        )

        # Convert all CSV strings to DataFrames
        dataframes = [pd.read_csv(io.StringIO(csv)) for csv in csv_content_list]
        
        # Combine all DataFrames (if multiple)
        if len(dataframes) > 1:
            combined_df = pd.concat(dataframes, ignore_index=True)
        else:
            combined_df = dataframes[0]
            
        # Create Pandas agent
        agent = create_pandas_dataframe_agent(
            llm=llm,
            df=combined_df,
            agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=False,
            allow_dangerous_code=True
        )
        
        # Run the query
        response = agent.run(query)
        return response
        
    except Exception as e:
        raise f"Error processing data: {str(e)}"
