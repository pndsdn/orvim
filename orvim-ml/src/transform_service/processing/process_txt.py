from common.workflow import TransformTextParser, RagChunker, RagEmbedder, RagLLMQa
from common.schema import Document
from io import BytesIO
from common.s3_connector import s3
from chunker import split_text
from download import download

def process_txt(document: Document, data: TransformTextParser, chunker: RagChunker, embedder: RagEmbedder, llm: RagLLMQa) ->  str:
    error = ""
    if document.type == "":
        text = document.data
    else:
        response = requests.get(url, headers=headers)

    for file_s3 in data.s3_path:
        ext = file_s3[file_s3.rfind(".")+1:]
        if ext!=file_s3:
            try:
                link = s3.generate_link(file_s3)
                result.append(Document(type=ext, data=link, source=f"s3|{file_s3}"))
            except Exception as e:
                error += str(e)
    return error