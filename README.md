# AI Abridger for EPUB Books
Python script to use a local llm or api to abridge an epub book

## Description
This script reads an EPUB file, extracts its text, splits it into manageable chunks, sends each chunk to an AI model to abridge it, and then writes the abridged text to an output file.

## Installation
Install the required packages:
```
pip install -r requirements.txt
```

## Usage
Run the script from the command line:
```
python aiabridge.py <input_file.epub>
```
The output will be saved to <input_file>_squish.txt by default.

## Setup Notes
- Need an **Ollama** server running on your local network
- Or an api key to access inference using a provider
- Need to setup the config.json file
- Tested models: This script is primarily tested with the models
  - llama3.2:3b (with minor inconsistencies)
  - llama3.1:8b
  - llama-3.3-70b
- Prompt may need to be tweaked to get desired output depending on the model being used

## Config File Usage
```
{
    "engine": "ollama" or "openai",
    "api_base": "http://<your-server-ip>:11434/api/generate", // For Ollama, or the OpenAI base URL
    "api_key": "", // Only needed for OpenAI; leave empty for Ollama
    "model": "llama3.1:8b", // Name of the model
    "stream": false // True/False as desired
}

```
  
<br/>
<sup> Smaller models are much less reliable and often hallucinate or partially ignore the prompt
