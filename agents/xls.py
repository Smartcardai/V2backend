import openpyxl
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain.agents import AgentType
import pandas as pd
import io
import os
from typing import List
from component.response import llm_key



def process_excel_with_pandas_agent(excel_content_list: List[bytes], query: str) -> str:
    """
    Process Excel data using Pandas Agent
    
    Args:
        excel_content_list: List of Excel file contents from Firebase
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

        # Convert all Excel contents to DataFrames
        dataframes = []
        for excel_content in excel_content_list:
            # Read Excel content into DataFrame
            excel_file = io.BytesIO(excel_content)
            
            # Read all sheets from the Excel file
            excel_data = pd.read_excel(excel_file, sheet_name=None)
            
            # Combine all sheets into dataframes list
            print(excel_data.items())
            for sheet_name, df in excel_data.items():
                df['source_sheet'] = sheet_name  # Add sheet name as a column
                dataframes.append(df)
        
        # Combine all DataFrames
        if len(dataframes) > 1:
            combined_df = pd.concat(dataframes, ignore_index=True)
        else:
            combined_df = dataframes[0]
            
        # Create Pandas agent
        agent = create_pandas_dataframe_agent(
            llm=llm,
            df=combined_df,
            agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            allow_dangerous_code=True
        )
        
        # Run the query
        response = agent.run(query)
        print("process end")
        return response
        
    except Exception as e:
        print("process error")
        return f"Error processing Excel data: {str(e)}"

def analyze_firebase_excel(content_list: List[bytes], query: str):
    """
    Analyze Excel data from Firebase
    
    Args:
        content_list: List of Excel contents from Firebase blobs
        query: User's question about the data
    Returns:
        str: Analysis result
    """
    return process_excel_with_pandas_agent(content_list, query)

# Example of integration with Firebase fetch code
def process_firebase_response(blob_contents: List[bytes], query: str):
    """
    Process Firebase response for Excel files
    
    Args:
        blob_contents: List of contents from Firebase blobs
        file_type: Type of file (application/vnd.ms-excel or application/vnd.openxmlformats-officedocument.spreadsheetml.sheet)
        query: Query to analyze the data
    Returns:
        str: Analysis result
    """
    excel_types = [
        'application/vnd.ms-excel',  # .xls
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'  # .xlsx
    ]
    
    
    return analyze_firebase_excel(blob_contents, query)
    return "Unsupported file type"
