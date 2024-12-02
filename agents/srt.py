from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain.agents import AgentType
import pandas as pd
import io
import os
from typing import List, Dict
from component.response import llm

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