import streamlit as st
import redirect as rd

import os
import tempfile
import time

from llama_index import SimpleDirectoryReader, StorageContext, LLMPredictor
from llama_index import TreeIndex
from llama_index import ServiceContext
from langchain.prompts import StringPromptTemplate
from typing import List, Union
from langchain.schema import AgentAction, AgentFinish
from langchain.agents import AgentExecutor, LLMSingleActionAgent, AgentOutputParser
from langchain import LLMChain, OpenAI
from llama_index.indices.tree.tree_root_retriever import TreeRootRetriever
import re
from langchain.chat_models import ChatOpenAI
from llama_index.tools import QueryEngineTool, ToolMetadata
from llama_index.query_engine import SubQuestionQueryEngine
from langchain.agents import Tool
from llama_index.query_engine import RetrieverQueryEngine
# import nest_asyncio

# nest_asyncio.apply()
os.environ['OPENAI_API_KEY'] = os.getenv('API_KEY')
query_engine_tools = []

import asyncio
def get_or_create_eventloop():
    try:
        return asyncio.get_event_loop()
    except RuntimeError as ex:
        if "There is no current event loop in thread" in str(ex):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return asyncio.get_event_loop()

def remove_formatting(output):
    output = re.sub('\[[0-9;m]+', '', output)  
    output = re.sub('\', '', output) 
    return output.strip()

@st.cache_resource
def preprocessing(uploaded_files):
    names = []
    descriptions = []
    if uploaded_files:
        temp_dir = tempfile.TemporaryDirectory()
        file_paths = []
        
        for uploaded_file in uploaded_files:
            file_path = os.path.join(temp_dir.name, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.read())
            file_paths.append(file_path)
        
        for file_path in file_paths:
            document = SimpleDirectoryReader(input_files=[file_path]).load_data()
            index = TreeIndex.from_documents(document)
            engine = index.as_query_engine(similarity_top_k = 3)
            retriever = TreeRootRetriever(index)
            temp_engine = RetrieverQueryEngine(retriever=retriever)
            summary = temp_engine.query("Write a short concise summary of this document")
            heading = temp_engine.query("Write a short concise heading of this document")
            description = str(summary)
            name = str(heading)
            query_engine_tools.append(QueryEngineTool(
                query_engine = engine,
                metadata = ToolMetadata(name = name, description = description)
            ))
            names.append(name)
            descriptions.append(description)
        st.write(names)
        st.write(descriptions)

        s_engine = SubQuestionQueryEngine.from_defaults(query_engine_tools = query_engine_tools)

        tools = [Tool(
            name = "Llama-Index",
            func = s_engine.query,
            description = f"Useful for when you want to answer questions on the topics - {names}. The input to this tool should be a complete English sentence.",
            return_direct = True
            )
        ]

        template1 = """You are an Assistant. You have access to the following tools:

                    {tools}

                    Use the following format:

                    Question: the input question you must answer
                    Thought: you should always think about what to do
                    Action: the action to take, should be one of [{tool_names}]
                    Action Input: the input to the action
                    Observation: the result of the action
                    ... (this Thought/Action/Action Input/Observation can repeat N times)
                    Thought: I now know the final answer
                    Final Answer: the final answer to the original input question

                    Begin! Remember to be ethical and articulate when giving your final answer. Use lots of "Arg"s

                    Question: {input}
                    {agent_scratchpad}"""

        prompt = CustomPromptTemplate(
            template = template1,
            tools = tools,
            input_variables=["input", "intermediate_steps"]
        )

        output_parser = CustomOutputParser()

        llm = OpenAI(temperature = 0)
        llm_chain = LLMChain(llm = llm, prompt = prompt)

        tool_names = [tool.name for tool in tools]
        agent = LLMSingleActionAgent(
            llm_chain = llm_chain, 
            output_parser = output_parser,
            stop = ["\nObservation:"], 
            allowed_tools = tool_names
        )

        agent_chain = AgentExecutor.from_agent_and_tools(tools = tools, agent = agent, verbose = True)

        return agent_chain
    
@st.cache_resource
def run(query):
    if query:
        with rd.stdout() as out:
            ox = agent_chain.run(query)
        output = out.getvalue()
        output = remove_formatting(output)
        st.write(ox.response)
        return True

class CustomPromptTemplate(StringPromptTemplate):
    template: str
    tools: List[Tool]
    
    def format(self, **kwargs) -> str:
        intermediate_steps = kwargs.pop("intermediate_steps")
        thoughts = ""
        for action, observation in intermediate_steps:
            thoughts += action.log
            thoughts += f"\nObservation: {observation}\nThought: "
        kwargs["agent_scratchpad"] = thoughts
        kwargs["tools"] = "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools])
        kwargs["tool_names"] = ", ".join([tool.name for tool in self.tools])
        return self.template.format(**kwargs)
    
class CustomOutputParser(AgentOutputParser):
    
    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        if "Final Answer:" in llm_output:
            return AgentFinish(
                return_values={"output": llm_output.split("Final Answer:")[-1].strip()},
                log=llm_output,
            )
        regex = r"Action\s*\d*\s*:(.*?)\nAction\s*\d*\s*Input\s*\d*\s*:[\s]*(.*)"
        match = re.search(regex, llm_output, re.DOTALL)
        if not match:
            raise ValueError(f"Could not parse LLM output: `{llm_output}`")
        action = match.group(1).strip()
        action_input = match.group(2)
        return AgentAction(tool=action, tool_input=action_input.strip(" ").strip('"'), log=llm_output)

st.set_page_config(layout = "wide")

st.title("Tools and Subqueries using LangChain and Llama-Index")
st.write("Upload your PDF files")

llm_predictor = LLMPredictor(llm = ChatOpenAI(temperature = 0, model_name = 'gpt-3.5-turbo', max_tokens = -1))

storage_context = StorageContext.from_defaults()
service_context = ServiceContext.from_defaults(llm_predictor = llm_predictor)

uploaded_files = st.file_uploader("Upload files", accept_multiple_files = True)

agent_chain = preprocessing(uploaded_files)
ack = False

if agent_chain:
    query = st.text_input('Enter your Query.', key = 'query_input')
    ack = run(query)
    if ack:
        ack = False
        query = st.text_input('Enter your Query.', key = 'new_query_input')
        ack = run(query)
        