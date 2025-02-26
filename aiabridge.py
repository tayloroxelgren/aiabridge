import html.parser
import requests
import sys
import html
import xml.etree.ElementTree as ET
import ebooklib
import json
from ebooklib import epub
import warnings
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from bs4 import BeautifulSoup




# Suppress all UserWarnings
warnings.simplefilter('ignore', category=UserWarning)
# Suppress all FutureWarnings
warnings.simplefilter('ignore', category=FutureWarning)

def getBookText(fileName):
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


def query_ollama(text_chunk, model = "llama3.2:3b", url= "http://10.0.0.247:11434/api/generate"):

    prompt= "Your goal is to abridge this by half like how audiobooks are frequently abridged. Do not acknowledge the prompt under any circumstances or mention what you are doing just begin the abridging. Start of text:"

    request_json = {
        "model": model,
        "prompt": f"{prompt} {text_chunk}"
    }
    
    try:
        response = requests.post(url, json=request_json, stream=True, timeout=120)
        response.raise_for_status()  # Raise an error for non-200 status codes
    except requests.RequestException as e:
        print(f"Error: {e}")


    response_text = []
    
    for line in response.iter_lines(decode_unicode=True):
        if line:  # if the line is not empty
            try:
                json_line = json.loads(line)
                # Append the response part
                text=json_line.get("response", "")
                response_text.append(text)
                # If the response indicates it's done, break out of the loop.
                if json_line.get("done", False):
                    break
            except json.JSONDecodeError:
                response_text.append(line)
                
    return "".join(response_text)



def abridgeText(chunks,concurrentRequests=1):

    if concurrentRequests>1:
        with ThreadPoolExecutor(max_workers=concurrentRequests) as executor:
            results = list(tqdm(executor.map(query_ollama, chunks), total=len(chunks)))

    else:
        results=[]
        for chunk in tqdm(chunks):
            results.append(query_ollama(chunk))
    
    return results


def writeFile(txt,output_filename="output.txt"):
    with open(output_filename, 'w', encoding='utf-8') as out:
        for t in txt:
            out.write(t)

if __name__=="__main__":
    if len(sys.argv) < 2:
        print("Usage: python aiabridge.py <input_file>")

    else:
        txt=getBookText(sys.argv[1])
        chunks=splitChunks(txt)
        llmResponse=abridgeText(chunks)
        writeFile(llmResponse)