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
# from langchain import hub
import requests

# from sentence_transformers import SentenceTransformer

CHROMADB_URL = os.getenv('CHROMADB_URL', 'chromadb')
CHROMADB_PORT = os.getenv('CHROMADB_PORT', '8000')

# chroma_client = chromadb.HttpClient(host=CHROMADB_URL, port=CHROMADB_PORT)
chroma_client = chromadb.Client()

EMBEDDER_URL = os.getenv("EMBEDDER_URL", "http://172.16.0.48:8000/embed/")

# prompt = hub.pull("rlm/rag-prompt")


def split_text(
    text: str,
    url_info: str,
    db_id: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    # Add other parameters as needed
) -> tuple[List[str], str]:
    """
    Splits the input text into chunks based on the specified parameters.

    Parameters:
    - text (str): The text to be split.
    - chunk_size (int, optional): The size of each chunk. Defaults to 500.
    - chunk_overlap (int, optional): The overlap between consecutive chunks. Defaults to 50.

    Returns:
    - List[str]: A list of text chunks.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        # Pass other parameters here
    )
    chunks = text_splitter.split_text(text)
    return chunks, url_info, db_id


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


def add_to_db(
    text: str,
    url_info: str,
    db_id: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    model_name: str = None,
    **kwargs
):
    collection = chroma_client.get_or_create_collection(name=db_id)
    chunks, _, _ = split_text(
        text=text,
        url_info=url_info,
        db_id=db_id,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    embeddings = generate_embeddings(chunks=chunks, model_name=model_name, **kwargs)

    metadata_list = [{"source": url_info, "chunk": i} for i in range(len(chunks))]
    ids = [str(random.random()) for i in range(len(chunks))]
    collection.add(
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadata_list,
        ids=ids
    )


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
) -> str:
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
    # print(retrieved_results)

    # Prepare context from retrieved documents
    context = "\n".join(
        f"Document {i+1}: {doc}" for i, doc in enumerate(retrieved_results["documents"][0])
    )
    if not use_additional_instruction: additional_instruction = ""
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

# generate_embeddings(
#     chunks=["Hello, i'm llama from facebook"],
#     model_name="Cohere",
#     cohere_api_key="zsok5zfsdaH54iuMI2zWrNrIgQiNMHsRax8A6eOw",
#     model="embed-english-v3.0"
#     )


# add_to_db(
#     text="""В 2011 году в Австралии был сформирован самый длинный в мире грузовой поезд, протяженностью 7353 метра. Этот рекордный состав состоял из 682 вагонов, каждый из которых был гружен до отказа железной рудой.

# Поезд курсировал по маршруту между шахтами Хаус-Крик и портом Дарвин, преодолевая расстояние в 850 километров. Для того чтобы управлять таким гигантом, требовалось два локомотива - один в голове, другой в хвосте.

# За время пути поезд потреблял около 170 тонн дизельного топлива, а его вес достигал 99 734 тонн.

# Этот рекорд был занесен в Книгу рекордов Гиннеса, но уже в 2013 году его побил другой австралийский поезд, состоящий из 683 вагонов.""",
#     url_info="wikipedia",
#     db_id="wiki",
#     chunk_size=100,
#     chunk_overlap=20,
#     model_name="local",
#     # cohere_api_key="zsok5zfsdaH54iuMI2zWrNrIgQiNMHsRax8A6eOw",
#     # model="embed-english-v3.0"
# )

# print(
#     retrieve_document(
#         "embedding generation",
#         model_name="Cohere",
#         db_id="col1",
#         n_results=4,
#         cohere_api_key="zsok5zfsdaH54iuMI2zWrNrIgQiNMHsRax8A6eOw",
#         model="embed-english-v3.0"
#     )
# )

# print(
#     generate_response(
#         question="Какое расстояние преодолевал самый длинный в мире поезд между шахтами Хаус-Крик и портом Дарвин?",
#         model_name="local",
#         db_id="wiki",
#         n_results=4,
#         cohere_api_key="zsok5zfsdaH54iuMI2zWrNrIgQiNMHsRax8A6eOw",
#         model="embed-english-v3.0",
#         llm_name="Cohere",
#         llm_kwargs={
#             "cohere_api_key": "zsok5zfsdaH54iuMI2zWrNrIgQiNMHsRax8A6eOw",
#             "model": "command-r-plus-04-2024"
#         }
#     )
# )

# print(
#     generate_response(
#         question="Какое расстояние преодолевал самый длинный в мире поезд между шахтами Хаус-Крик и портом Дарвин?",
#         model_name="local",
#         db_id="wiki",
#         n_results=10,
#         # cohere_api_key="zsok5zfsdaH54iuMI2zWrNrIgQiNMHsRax8A6eOw",
#         # model="embed-english-v3.0",
#         use_additional_instruction=True,
#         llm_name="OpenAI",
#         llm_kwargs={
#             "base_url": "https://api.deepinfra.com/v1/openai",
#             # "api_key": "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"
#             "api_key": "zszU0KJLKifT3goW16u5N9YwDDXxyCog",
#             "model": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"
#         }
#     )
# )