from langchain.text_splitter import RecursiveCharacterTextSplitter

def split_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    # Add other parameters as needed
) -> tuple[list[str], str]:
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
    return chunks