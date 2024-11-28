from common.workflow import ConnectionS3
from common.schema import Document
from io import BytesIO
from common.s3_connector import s3

def process_s3(data: ConnectionS3, **kwargs) ->  tuple[list[Document], str]:
    result = []
    error = ""
    for file_s3 in data.s3_path:
        ext = file_s3[file_s3.rfind(".")+1:]
        if ext!=file_s3:
            try:
                link = s3.generate_link(file_s3)
                result.append(Document(type=ext, data=link, source=f"s3|{file_s3}"))
            except Exception as e:
                error += str(e)
    return result, error