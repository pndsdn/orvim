from typing import List, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_cohere import CohereEmbeddings, ChatCohere
from langchain_gigachat import GigaChatEmbeddings
from langchain_community.llms import GigaChat
from langchain_openai import OpenAIEmbeddings,  ChatOpenAI
from langchain_mistralai import MistralAIEmbeddings
from langchain_core.messages import SystemMessage, HumanMessage
import os, chromadb, random, re
from chromadb.api.types import Embedding
from typing import cast
from langchain import hub
import requests
from settings import settings


CHROMADB_URL = settings.CHROMADB_URL
CHROMADB_PORT = settings.CHROMADB_PORT

chroma_client = chromadb.HttpClient(host=CHROMADB_URL, port=CHROMADB_PORT)
#chroma_client = chromadb.Client()

EMBEDDER_URL = settings.EMBEDDER_URL

prompt = hub.pull("rlm/rag-prompt")


def generate_embeddings(
    chunks: List[str],
    model_name: str,
    **kwargs
) -> List[List[float]]:
    """
    Generates embeddings for the list of text chunks using the specified embedding model.

    Parameters:
    - chunks (List[str]): The list of text chunks to be embedded.
    - model_name (str): The name of the embedding model to use, e.g., "OpenAIEmbeddings" or "huggingface.HuggingFaceEmbeddings".
    - **kwargs: Additional keyword arguments specific to the embedding model.

    Returns:
    - List[List[float]]: A list of embeddings for the text chunks.

    Raises:
    - AttributeError: If the specified model_name or class is not found.
    - ImportError: If the specified module path is not found.
    """
    embedding_model = None
    if model_name == "Cohere": embedding_model = CohereEmbeddings(**kwargs)
    elif model_name == "GigaChat": embedding_model = GigaChatEmbeddings(**kwargs)
    elif model_name == "OpenAI": embedding_model = OpenAIEmbeddings(**kwargs)
    elif model_name == "Mistral": embedding_model = MistralAIEmbeddings(**kwargs)
    elif model_name == "local":
        try:
            response = requests.post(EMBEDDER_URL, json=chunks)
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occured: {http_err}")
        except Exception as err:
            print(f"An error occured {err}")
        else:
            result = response.json()
            embeddings_list = [cast(Embedding, emb) for emb in result]
            return embeddings_list
    else: raise KeyError(f"Model {model_name} not permitted")
    # Generate embeddings for the chunks
    embeddings_list = [cast(Embedding, emb) for emb in embedding_model.embed_documents(chunks)]
    return embeddings_list


def retrieve_document(
    question: str,
    model_name: str,
    db_id: str,
    n_results: int,
    **kwargs
):
    embeddings = generate_embeddings(chunks=[question], model_name=model_name, **kwargs)
    collection = chroma_client.get_or_create_collection(name=db_id)

    result = collection.query(
        query_embeddings=embeddings,
        n_results=n_results
    )

    return result


def generate_response(
    question: str,
    model_name: str,
    db_id: str,
    n_results: int,
    use_additional_instruction: bool = True,
    additional_instruction: str = "после вашего ответа укажите самые релевантные номера документов, которые вы использовали для ответа, в квадратных скобках через запятую, как в примере:[1,4, 27] ",
    prompt_template: str = None,
    llm_name: str = "OpenAI",
    llm_kwargs: dict = None,
    **kwargs
):
    """
    Generates a response by retrieving relevant documents from Chroma DB and processing them with a language model.

    Parameters:
    - question (str): The user's question or query.
    - model_name (str): The name of the embedding model used for Chroma retrieval.
    - db_id (str): The database ID in Chroma DB to search for documents.
    - n_results (int): Number of top documents to retrieve.
    - llm_name (str, optional): The name of the language model to use. Defaults to "OpenAI".
    - llm_kwargs (dict, optional): Additional arguments for the LLM. Defaults to None.
    - **kwargs: Additional arguments for embedding model.

    Returns:
    - str: The generated response from the LLM.
    """
    # Retrieve relevant documents from Chroma DB
    retrieved_results = retrieve_document(
        question=question,
        model_name=model_name,
        db_id=db_id,
        n_results=n_results,
        **kwargs
    )

    # Prepare context from retrieved documents
    context = "\n".join(
        f"Document {i+1}: {doc}" for i, doc in enumerate(retrieved_results["documents"][0])
    )
    if not use_additional_instruction:
        additional_instruction = ""
    # Create prompt template
    if prompt_template is None:
        prompt_template = f"""Вы ИИ-помощник. Используйте следующие найденные документы, чтобы ответить на вопрос:
        {context}
        """
    else:
        if "{context}" not in prompt_template or "{additional_instruction}" not in prompt_template:
            raise ValueError("Promt_template must contain '{context}' and '{additional_instruction}' fields")

    # Initialize the LLM
    if llm_name == "Cohere": llm = ChatCohere(**llm_kwargs)
    elif llm_name == "GigaChat": llm = GigaChat(**llm_kwargs)
    elif llm_name == "OpenAI": llm = ChatOpenAI(**llm_kwargs)
    else:
        raise ValueError(f"Unsupported LLM: {llm_name}")

    full_prompt = [
        SystemMessage(
            content=prompt_template
        ),
        HumanMessage(content=question + f"Строго после ответа на вопрос пользователя выполните следующую инструкцию: {additional_instruction}.")
    ]

    response = llm.invoke(full_prompt)

    if use_additional_instruction:
        index = response.content.find("[")
        answer = response.content[:index] if index != - 1 else response.content
        try:
            matches = re.findall(r'\[(.*?)\]', response.content, re.DOTALL)[-1]
        except:
            return response.content, f"System: {full_prompt[0].content} User: {full_prompt[1].content}", []

        if "," in matches: matches = [int(i) for i in matches.split(",")]
        else: matches = [int(matches)]

        resulted_source = [retrieved_results["metadatas"][0][i]["source"] for i in range(len(matches))]

        return answer, f"System: {full_prompt[0].content} User: {full_prompt[1].content}", list(set(resulted_source))

    return response.content, f"System: {full_prompt[0].content} User: {full_prompt[1].content}", []
