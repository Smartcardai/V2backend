from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain.agents import AgentType
import pandas as pd
import io
import os
from typing import List
from component.response import llm_key

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
import os


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
