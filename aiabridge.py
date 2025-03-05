import html.parser
import requests
import sys
import os
import html
import xml.etree.ElementTree as ET
import ebooklib
import json
import time
from ebooklib import epub
import warnings
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from bs4 import BeautifulSoup
from openai import OpenAI



# These warnings aren't relevant to the end user
# Suppress all UserWarnings
warnings.simplefilter('ignore', category=UserWarning)
# Suppress all FutureWarnings
warnings.simplefilter('ignore', category=FutureWarning)

def load_config(config_file="config.json"):
    with open(config_file, "r", encoding="utf-8") as f:
        return json.load(f)
    #     Expected config format:
    # {
    #     "engine": "ollama" or "openai",
    #     "api_base": "http://10.0.0.247:11434/api/generate"  // For Ollama, or the OpenAI base URL
    #     "api_key": "",              // Only needed for OpenAI; leave empty for Ollama
    #     "model": "llama3.1:8b",       // Name of the model
    #     "stream": false             // True/False as desired
    # }


def getBookText(fileName):
    if fileName.lower().endswith(".txt"):
        with open(fileName, "r", encoding="utf-8") as f:
            return f.read()

    book=epub.read_epub(fileName)
    bookDocs=book.get_items_of_type(ebooklib.ITEM_DOCUMENT)
    bookText=""
    for doc in bookDocs:
        docContent=doc.get_body_content()
        decoded_html=html.unescape(docContent.decode('utf-8'))
        soup = BeautifulSoup(decoded_html, "html.parser")
        paragraphs = soup.find_all("p")
        for p in paragraphs:
            bookText+=p.get_text()
            bookText+="\n\n"
    return bookText

def splitChunks(text, soft_limit=500):
    """
    Splits into chunks of approximately `soft_limit`,
    but only ends a chunk on a word that ends with '.'
    Ensures it is not split mid quote
    Returns a list of chunk strings.
    """
    # Split text into words by whitespace
    words = text.split()

    chunks = []
    current_chunk_words = []
    word_count = 0
    quote_count = 0

    for word in words:
        current_chunk_words.append(word)
        word_count += 1

        #Tracking quotes
        quote_count += word.count('"') + word.count('“') + word.count('”')

        # If we reach soft_limit and we are NOT inside a quote,
        # and the word ends with a sentence-ending punctuation, then create a chunk
        if word_count >= soft_limit and word[-1] in {'.', '!', '?'} and quote_count % 2 == 0:
            chunk_text = ' '.join(current_chunk_words)
            chunks.append(chunk_text)
            current_chunk_words = []
            word_count = 0

    # Any leftover words go into a final chunk
    if current_chunk_words:
        chunk_text = ' '.join(current_chunk_words)
        chunks.append(chunk_text)

    return chunks



def query_llm(text_chunk):

    config=load_config()

    prompt = (
        "Your goal is to abridge this by half like how audiobooks are frequently abridged. "
        "Do not acknowledge the prompt under any circumstances or mention what you are doing—just begin the abridging. "
        "Start of text: " + text_chunk
    )
    
    engine = config.get("engine", "ollama").lower()
    
    if engine == "ollama":
        url = config.get("api_base")
        model = config.get("model")
        
        request_json = {
            "model": model,
            "prompt": prompt
        }
        
        response_text = []
        try:
            response = requests.post(url, json=request_json, stream=True, timeout=120)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Ollama API Error: {e}")
            return ""
        
        for line in response.iter_lines(decode_unicode=True):
            if line:
                try:
                    json_line = json.loads(line)
                    text = json_line.get("response", "")
                    response_text.append(text)
                    if json_line.get("done", False):
                        break
                except json.JSONDecodeError:
                    response_text.append(line)
                    
        return "".join(response_text)
    
    else:
        # For OpenAI-compatible API.
        base_url = config.get("api_base")
        api_key = config.get("api_key")
        model = config.get("model")
        stream = config.get("stream", False)

        # Instantiate the OpenAI client with your API key and base URL.
        client = OpenAI(
            base_url=base_url,
            api_key=api_key,
        )

        # Construct messages for the chat completion.
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that abridges texts."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        response_text = []
        try:
            # Use the new client method to create a chat completion.
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                stream=stream,
            )
            
            if stream:
                # If streaming, iterate over the chunks.
                for chunk in completion:
                    # Access chunk based on delta
                    delta = chunk.choices[0].delta
                    token = delta.content if hasattr(delta, "content") else ""
                    response_text.append(token)
            else:
                response_text.append(completion.choices[0].message.content)
        except Exception as e:
            print(f"OpenAI API Error: {e}")
            return ""
        return "".join(response_text)



def abridgeText(chunks,concurrentRequests=1):

    config=load_config()
    if config["engine"]!="ollama":
        concurrentRequests=5

    if concurrentRequests>1:
        with ThreadPoolExecutor(max_workers=concurrentRequests) as executor:
            results = list(tqdm(executor.map(query_llm, chunks), total=len(chunks)))

    else:
        results=[]
        for chunk in tqdm(chunks):
            results.append(query_llm(chunk))
    
    return results


def writeFile(txt,output_filename="output.txt"):
    with open(output_filename, 'w', encoding='utf-8') as out:
        for t in txt:
            out.write(t)


def main():
    txt=getBookText(sys.argv[1])
    chunks=splitChunks(txt)
    llmResponse=abridgeText(chunks)
    base, ext = os.path.splitext(sys.argv[1])
    writeFile(llmResponse,f"{base}_squish.txt")


if __name__=="__main__":
    if len(sys.argv) < 2:
        print("Usage: python aiabridge.py <input_file>")

    else:
        main()