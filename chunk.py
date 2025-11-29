import json
import os

def load_single_jsonl(file_path):

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)
    except FileNotFoundError:
        print("File not found: " + file_path + "\nMake sure the file path is correct.")
        return
    

def load_jsonl_files(folder_path):

    jsonl_files = os.listdir(folder_path)

    for file in jsonl_files:
        file_path = os.path.join(folder_path, file)
        yield from load_single_jsonl(file_path)

def load_single_txt(file_path):
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield line
    except FileNotFoundError:
        print("File not found: " + file_path + "\nMake sure the file path is correct.")
        return

def chunk_text(text, size=150, overlap=50):
    
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + size
        chunk = words[start:end]
        chunks.append(" ".join(chunk))
        start += size - overlap

    return chunks

def chunk_dataset(folder_path, size=150, overlap=50):
    
    all_chunks = []
    for item in load_jsonl_files(folder_path):
        text = item.get("text", "")
        if not text:
            continue
        
        local_chunks = chunk_text(text, size, overlap)
        for chunk in local_chunks:

            if not chunk.strip():
                continue

            all_chunks.append(chunk)

    return all_chunks

def chunk_jsonl_file(file_path, size=150, overlap=50):

    all_chunks = []

    for item in load_single_jsonl(file_path):
        text = item.get("text", "")
        if not text:
            continue

        local_chunks = chunk_text(text, size, overlap)
        for chunk in local_chunks:
            if chunk.strip():
                all_chunks.append(chunk)

    return all_chunks

def chunk_txt_file(file_path, size=150, overlap=50):
    all_chunks = []

    for item in load_single_jsonl(file_path):
        text = item.get("text", "")
        if not text:
            continue

        local_chunks = chunk_text(text, size, overlap)
        for chunk in local_chunks:
            if chunk.strip():
                all_chunks.append(chunk)

    return all_chunks