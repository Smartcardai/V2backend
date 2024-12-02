from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain.agents import AgentType
import pandas as pd
import xml.etree.ElementTree as ET
import io
import os
from typing import List, Dict, Union
from collections import defaultdict
from component.response import llm

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
