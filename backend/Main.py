from dotenv import load_dotenv
from llama_index import VectorStoreIndex, SimpleDirectoryReader, ServiceContext
from llama_index.vector_stores import PineconeVectorStore
from llama_index.storage.storage_context import StorageContext
from langchain.chat_models import ChatOpenAI
from llama_index.llm_predictor import LLMPredictor
from langchain.agents import ZeroShotAgent, Tool, AgentExecutor
from langchain import OpenAI, SerpAPIWrapper, LLMChain
import pinecone
from huggingface_hub.inference_api import InferenceApi
import os
import openai

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

pinecone.init(environment = "asia-southeast1-gcp-free")

tools = []

### Replace output.show() with frontends

def waifu(prompt):
    inference = InferenceApi(repo_id = "hakurei/waifu-diffusion")
    output = (inference(prompt))
    output.show()
    return "The image was generated and displayed."

def midjourney(prompt):
    inference = InferenceApi(repo_id = "prompthero/openjourney") #Use the activation token mdjrny-v4 style in prompt
    output = (inference(prompt))
    output.show()
    return "The image was generated and displayed."

def disney(prompt):
    inference = InferenceApi(repo_id = "nitrosocke/mo-di-diffusion") #Use the activation token modern disney style in prompt
    output = (inference(prompt))
    output.show()
    return "The image was generated and displayed."

def real(prompt):
    inference = InferenceApi(repo_id = "dreamlike-art/dreamlike-photoreal-2.0") #Use the activation token photo in prompt
    output = (inference(prompt))
    output.show()
    return "The image was generated and displayed."

def timeless(prompt):
    inference = InferenceApi(repo_id = "wavymulder/timeless-diffusion") #Use the activation token timeless style in prompt
    output = (inference(prompt))
    output.show()
    return "The image was generated and displayed."

### To be called at the beginning of the chat process, to be called ONLY ONCE, creates a new Pinecone Index, deletes the old, preprocesses the documents.
def preprocessing_prelimnary(name = "", description = ""):
    path_to_temp = r'temp'
    documents = SimpleDirectoryReader(path_to_temp).load_data()
    pinecone_index = pinecone.Index('best')
    pinecone_index.delete(deleteAll = True)
    vector_store = PineconeVectorStore(pinecone_index = pinecone_index)
    storage_context = StorageContext.from_defaults(vector_store = vector_store)
    llm_predictor_chatgpt = LLMPredictor(llm = ChatOpenAI(temperature = 0, model_name = "gpt-3.5-turbo"))
    service_context = ServiceContext.from_defaults(chunk_size = 128, llm_predictor = llm_predictor_chatgpt)
    index = VectorStoreIndex.from_documents(documents, service_context = service_context, storage_context = storage_context)
    engine = index.as_query_engine(similarity_top_k = 3)
    tool_description = engine.query('Give a very brief and concise description of this document. A maximum of 2 or 3 sentences.')
    print(tool_description)
    search = SerpAPIWrapper()
    tools = [Tool(
            name = "Documents",
            func = engine.query,
            description = f"{tool_description}. The input to this tool should be a complete English sentence. Use this tool if don't have context.",
            return_direct = True
            ),
            Tool(
            name = "Search",
            func = search.run,
            description="useful for when you need to answer questions about current events",
            ),
            Tool(
            name = "Anime Image Generation",
            func = waifu,
            description = "useful for generating anime images. The input to this tool should be descriptions/features separated by a comma. Do give identifying features like ethnicity, age, hair color et cetera for better results.",
            ),
            # Tool(
            # name = "Anime Image Generation",
            # func = waifu,
            # description = "useful for generating anime images. The input to this tool should be descriptions/features separated by a comma. Do give identifying features like ethnicity, age, hair color et cetera for better results.",
            # ),
            # Tool(
            # name = "Anime Image Generation",
            # func = waifu,
            # description = "useful for generating anime images. The input to this tool should be descriptions/features separated by a comma. Do give identifying features like ethnicity, age, hair color et cetera for better results.",
            # ),
            # Tool(
            # name = "Anime Image Generation",
            # func = waifu,
            # description = "useful for generating anime images. The input to this tool should be descriptions/features separated by a comma. Do give identifying features like ethnicity, age, hair color et cetera for better results.",
            # )
    ]
    if not name:
        if not description:
            prefix = """You are an AI Assistant. Answer the following questions as best you can. You have access to the following tools:"""
            suffix = """You are rewarded for using the Documnets tool, use it as much as you can. Remember to be moral and ethical. Reply in the language you were asked the question in. Begin."

            Question: {input}
            {agent_scratchpad}"""
        else:
            prefix = f"""You are an AI Assistant. A brief description about you - {description}. Answer the following questions as best you can. You have access to the following tools:"""
            suffix = """You are rewarded for using the Documnets tool, use it as much as you can. Remember to be moral and ethical. Reply in the language you were asked the question in. Begin."

            Question: {input}
            {agent_scratchpad}"""
    else:
        if not description:
            prefix = f"""Your name is {name}. Stay in character. Answer the following questions as best you can. You have access to the following tools:"""
            suffix = """You are rewarded for using the Documnets tool, use it as much as you can. Remember to be moral and ethical. Reply in the language you were asked the question in. Begin."

            Question: {input}
            {agent_scratchpad}"""
        else:
            prefix = f"""Your name is {name} and a brief description about you is {description}. Stay in character. Answer the following questions as best you can. You have access to the following tools:"""
            suffix = """You are rewarded for using the Documnets tool, use it as much as you can. Remember to be moral and ethical. Reply in the language you were asked the question in. Begin."

            Question: {input}
            {agent_scratchpad}"""

    prompt = ZeroShotAgent.create_prompt(
        tools, prefix = prefix, suffix = suffix, input_variables = ["input", "agent_scratchpad"]
    )

    print(prompt.template)

    llm_chain = LLMChain(llm = OpenAI(temperature = 0), prompt = prompt)

    tool_names = [tool.name for tool in tools]

    agent = ZeroShotAgent(llm_chain = llm_chain, allowed_tools = tool_names)

    global agent_executor
    agent_executor = AgentExecutor.from_agent_and_tools(
        agent = agent, tools = tools, verbose = True
    )

### To run a querys
def run(question):
    response = agent_executor.run(question)
    print(response)

preprocessing_prelimnary('AI Bot', 'AI Assistant for answering questions.')
run('Generate an anime image of Tamish based on his attributes')