from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import PromptTemplate
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent





from langchain.agents.agent_types import AgentType
from langchain_experimental.agents.agent_toolkits import create_csv_agent

from dotenv import load_dotenv
import os

from langchain.agents import (
    create_json_agent,
    AgentExecutor
)
from langchain.agents.agent_toolkits import JsonToolkit
from langchain.tools.json.tool import JsonSpec
from langchain.schema import SystemMessage
from langchain.tools import BaseTool
import json
from typing import Dict, List, Any, Union
from langchain_community.tools.tavily_search import TavilySearchResults



import warnings
warnings.filterwarnings("ignore")

load_dotenv()


llm_key= os.getenv('LLM_KEY')

embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001",google_api_key=llm_key)

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash-latest",
    temperature=0.3,
    top_p=0.9,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key=llm_key
)




prompt_template='''
You are an AI assistant. 

Instructions: {prompt}
Reference Data: {content}
Conversation History: {chat}
User's Question: {query}

Your response should be concise and accurate to the query.
'''

prompt= PromptTemplate.from_template(prompt_template)
parser= StrOutputParser()

chain= prompt | llm | parser






def doc_agent_response(prompt,content,chat,query ):
    
    res= chain.invoke(
        {
        'prompt': prompt,   
        'content': content,
        'chat': chat,
        'query': query
        }
    )
    return res






# test ------------------------------

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
import os
import json

def analyze_json(json_data, query):
    """
    Analyze JSON data using ChatGoogleGenerativeAI with direct reasoning.
    """
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=llm_key,
            temperature=0
        )

        # Create a prompt template that encourages direct reasoning
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a JSON analysis expert. Given a JSON structure and a question, 
            analyze the data directly and provide a clear answer. No need to explain the steps.
            The JSON data is: {json_data}"""),
            ("human", "{query}")
        ])

        # Create chain
        chain = LLMChain(llm=llm, prompt=prompt)

        # Run the chain
        response = chain.invoke({
            "json_data": json_data,
            "query": query
        })

        return response["text"]

    except Exception as e:
        return f"Error during analysis: {str(e)}"




# testin pandas agent

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain.agents import AgentType
import pandas as pd
import io
import os
from typing import List

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




# test xls files

import openpyxl

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



# xml agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain.agents import AgentType
import pandas as pd
import xml.etree.ElementTree as ET
import io
import os
from typing import List, Dict, Union
from collections import defaultdict

class XMLProcessor:
    def __init__(self):
        """Initialize the XML Processor"""
        self.llm = llm

    def xml_to_dataframe(self, xml_content: str) -> pd.DataFrame:
        """
        Convert XML content to pandas DataFrame
        
        Args:
            xml_content: XML string content
        Returns:
            DataFrame representing the XML structure
        """
        try:
            # Parse XML content
            root = ET.fromstring(xml_content)
            
            # Convert XML to list of dictionaries
            data = []
            
            def process_element(element, parent_path=""):
                """Recursively process XML elements"""
                item = {}
                
                # Add attributes
                for key, value in element.attrib.items():
                    item[f"{parent_path}{key}"] = value
                
                # Add text content if exists
                if element.text and element.text.strip():
                    item[f"{parent_path}{element.tag}_text"] = element.text.strip()
                
                # Process child elements
                for child in element:
                    child_path = f"{parent_path}{element.tag}_"
                    child_data = process_element(child, child_path)
                    item.update(child_data)
                
                return item

            # Process all root children
            for child in root:
                data.append(process_element(child))
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            return df
            
        except Exception as e:
            raise Exception(f"Error converting XML to DataFrame: {str(e)}")

    def process_xml_data(self, xml_content_list: List[str], query: str) -> str:
        """
        Process multiple XML contents and answer query
        
        Args:
            xml_content_list: List of XML strings
            query: Question about the XML data
        Returns:
            Answer to the query
        """
        try:
            # Convert all XML contents to DataFrames
            dataframes = []
            for xml_content in xml_content_list:
                df = self.xml_to_dataframe(xml_content)
                dataframes.append(df)
            
            # Combine all DataFrames
            if len(dataframes) > 1:
                combined_df = pd.concat(dataframes, ignore_index=True)
            else:
                combined_df = dataframes[0]
            
            # Create pandas agent
            agent = create_pandas_dataframe_agent(
                llm=self.llm,
                df=combined_df,
                agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=True,
                allow_dangerous_code=True
            )
            
            # Run query
            response = agent.run(query)
            return response
            
        except Exception as e:
            return f"Error processing XML data: {str(e)}"

def process_firebase_xml(blob_contents: List[str], query: str) -> str:
    """
    Process XML files from Firebase
    
    Args:
        blob_contents: List of XML contents from Firebase
        query: Query about the XML data
    Returns:
        Analysis result
    """
    try:
        processor = XMLProcessor()
        return processor.process_xml_data(blob_contents, query)
    except Exception as e:
        return f"Error processing Firebase XML: {str(e)}"
    


# srt agent
import re
from datetime import datetime

class SRTProcessor:
    def __init__(self):
        """Initialize the SRT Processor"""
        self.llm = llm

    def parse_time(self, time_str: str) -> float:
        """
        Convert SRT timestamp to seconds
        
        Args:
            time_str: SRT timestamp (e.g., '00:00:20,000')
        Returns:
            Timestamp in seconds
        """
        try:
            # Replace comma with decimal point for milliseconds
            time_str = time_str.replace(',', '.')
            time_obj = datetime.strptime(time_str, '%H:%M:%S.%f')
            return time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second + time_obj.microsecond / 1000000
        except Exception as e:
            raise Exception(f"Error parsing time: {str(e)}")

    def parse_srt(self, srt_content: str) -> List[Dict]:
        """
        Parse SRT content into structured data
        
        Args:
            srt_content: Raw SRT file content
        Returns:
            List of dictionaries containing subtitle information
        """
        try:
            # Split into subtitle blocks
            subtitle_blocks = re.split(r'\n\n+', srt_content.strip())
            subtitles = []
            
            for block in subtitle_blocks:
                lines = block.strip().split('\n')
                if len(lines) >= 3:  # Valid subtitle block should have at least 3 lines
                    # Parse subtitle number
                    subtitle_number = int(lines[0])
                    
                    # Parse timestamp line
                    timestamp_line = lines[1]
                    start_time, end_time = timestamp_line.split(' --> ')
                    
                    # Parse text (might be multiple lines)
                    text = ' '.join(lines[2:])
                    
                    # Convert times to seconds
                    start_seconds = self.parse_time(start_time)
                    end_seconds = self.parse_time(end_time)
                    
                    # Calculate duration
                    duration = end_seconds - start_seconds
                    
                    subtitles.append({
                        'subtitle_number': subtitle_number,
                        'start_time': start_time,
                        'end_time': end_time,
                        'start_seconds': start_seconds,
                        'end_seconds': end_seconds,
                        'duration': duration,
                        'text': text
                    })
            
            return subtitles
        except Exception as e:
            raise Exception(f"Error parsing SRT: {str(e)}")

    def srt_to_dataframe(self, srt_content: str) -> pd.DataFrame:
        """
        Convert SRT content to pandas DataFrame
        
        Args:
            srt_content: Raw SRT file content
        Returns:
            DataFrame containing subtitle data
        """
        try:
            subtitles = self.parse_srt(srt_content)
            return pd.DataFrame(subtitles)
        except Exception as e:
            raise Exception(f"Error converting to DataFrame: {str(e)}")

    def process_srt_data(self, srt_content_list: List[str], query: str) -> str:
        """
        Process multiple SRT contents and answer query
        
        Args:
            srt_content_list: List of SRT file contents
            query: Question about the subtitle data
        Returns:
            Answer to the query
        """
        try:
            # Convert all SRT contents to DataFrames
            dataframes = []
            for idx, srt_content in enumerate(srt_content_list):
                df = self.srt_to_dataframe(srt_content)
                df['source_file'] = f'subtitle_{idx+1}'
                dataframes.append(df)
            
            # Combine all DataFrames
            if len(dataframes) > 1:
                combined_df = pd.concat(dataframes, ignore_index=True)
            else:
                combined_df = dataframes[0]
            
            # Create pandas agent
            agent = create_pandas_dataframe_agent(
                llm=self.llm,
                df=combined_df,
                agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=True,
                allow_dangerous_code= True
            )
            
            # Run query
            response = agent.run(query)
            return response
            
        except Exception as e:
            return f"Error processing SRT data: {str(e)}"

def process_firebase_srt(blob_contents: List[str], query: str) -> str:
    """
    Process SRT files from Firebase
    
    Args:
        blob_contents: List of SRT contents from Firebase
        query: Query about the subtitle data
    Returns:
        Analysis result
    """
    try:
        processor = SRTProcessor()
        return processor.process_srt_data(blob_contents, query)
    except Exception as e:
        return f"Error processing Firebase SRT: {str(e)}"