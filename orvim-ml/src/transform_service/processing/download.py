import requests

def download(url: str):
    return requests.get(url).content