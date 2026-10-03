# RAG Chatbot

An AI chatbot that answers questions from your own documents (PDFs and text files) using Retrieval-Augmented Generation.

## How it works

1. `ingest.py` reads documents, splits them into chunks, and stores them as vectors in ChromaDB.
2. `ask.py` finds the most relevant chunks for a question and sends them to Claude to write the answer.
3. Keeps chat history for follow-up questions.

## Tech

Python, ChromaDB, Anthropic Claude API, pypdf

## Setup

```
pip install -r requirements.txt
```

Add your key to a `.env` file: `ANTHROPIC_API_KEY=your-key`

Put files in a `docs/` folder, then run:

```
python ingest.py
python ask.py
```
