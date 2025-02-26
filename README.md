# AI Abridger for EPUB Books
Python script to use a local llm to abridge an epub book

## Description
This script reads an EPUB file, extracts its text, splits it into manageable chunks, sends each chunk to an AI model running on Ollama to abridge it, and then writes the abridged text to an output file.

## Installation
Install the required packages:
```
pip install -r requirments.txt
```

## Usage
Run the script from the command line:
```
python aiabridge.py <input_file.epub>
```
The output will be saved to output.txt by default.

## Setup Notes
- Need an **Ollama** server running on your local network
- Tested models: This script is primarily tested with the models
  - llama3.2:3b
  - llama3.1:8b
- Prompt may need to be tweaked to get desired output depending on the model being used
  
<br/>
<sup> Smaller models are much less reliable and often hallucinate or partially ignore the prompt
