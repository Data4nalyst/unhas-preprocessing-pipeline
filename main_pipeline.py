import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import re
import json
import pytesseract
from pdf2image import convert_from_path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from tqdm import tqdm

# --- KONFIGURASI ---
URL_BERITA = "https://www.unhas.ac.id/berita/?lang=id"
FOLDER_PDF = "data/pdf"
OUTPUT_JSONL = "output/knowledge_base_unhas.jsonl"
pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files/Tesseract-OCR/tesseract.exe'
POPPLER_PATH = 'C:/poppler-25.12.0/Library/bin' 

# Kamus Typo 
KAMUS_TYPO = {
    "SKEPUTUSAN": "KEPUTUSAN",
    "SKEP": "KEP",
    "mt ": "",      
    "ae ": "a. ",   
    "bs ": "b. ",   
    "cs ": "c. ",
    "Menimbang :": "\nMenimbang :",
    "Mengingat :": "\nMengingat :",
    "Memutuskan :": "\nMemutuskan :",
    "MEMUTUSKAN": "\nMEMUTUSKAN",
    "BABI": "BAB I",
    "BAB Ill": "BAB III",
    "Unhas": "Universitas Hasanuddin"
}

# --- 1. MODUL SCRAPING BERITA ---
def run_news_scraper():
    print("\n[1/4] 🕷️ Memulai Scraping Berita Unhas...")
    data_berita = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        # Request ke halaman indeks berita
        response = requests.get(URL_BERITA, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'lxml')
        articles = soup.find_all('a', class_='jet-smart-tiles__box-link')

        print(f"Ditemukan {len(articles)} potensi artikel. Sedang memproses...")
        
        for link_tag in tqdm(articles, desc="Scraping Berita"):
            title = link_tag.get('aria-label')
            url = link_tag.get('href')
            
            try:
                news_resp = requests.get(url, headers=headers, timeout=30)
                time.sleep(1)
                news_soup = BeautifulSoup(news_resp.text, 'lxml')
                
                paragraphs = news_soup.find_all('p')
                content = ' '.join([p.text.strip() for p in paragraphs if p.text.strip()])
                
                if len(content) > 50:
                    data_berita.append({
                        'title': title,
                        'source': url,
                        'content': content,
                        'type': 'berita'
                    })
            except Exception as e:
                continue

    except Exception as e:
        print(f"⚠️ Error koneksi: {e}")

    df = pd.DataFrame(data_berita)
    print(f"✅ Berhasil mengambil {len(df)} berita.")
    return df

# --- 2. MODUL INGESTION PDF TO TEXT (OCR - Poppler) ---
def run_ingestion_pdf():
    print(f"\n[2/4] 📂 Membaca Dokumen dari '{FOLDER_PDF}'...")
    data_pdf = []

    if not os.path.exists(FOLDER_PDF):
        print(f"Folder '{FOLDER_PDF}' tidak ditemukan.")
    else:
        files = [f for f in os.listdir(FOLDER_PDF) if f.lower().endswith('.pdf')]
        print(f"Mulai OCR untuk {len(files)} dokumen...")

        for filename in tqdm(files, desc="Proses OCR PDF"):
            pdf_path = os.path.join(FOLDER_PDF, filename)
            text = ""
            try:
                images = convert_from_path(pdf_path, poppler_path=POPPLER_PATH)
                for image in images:
                    page_text = pytesseract.image_to_string(image, lang='eng') 
                    text += page_text + " "
            except Exception as e:
                print(f"Error OCR: {e}")

            text = re.sub(r'\n', ' ', text)       # Hapus enter
            text = re.sub(r'\s+', ' ', text)      # Hapus spasi ganda
            text = re.sub(r'[^a-zA-Z0-9.,/:;()%\- ]', '', text) # Hapus karakter aneh
            text = text.strip()
            if len(text) > 50:
                data_pdf.append({
                    'title': filename.replace('.txt', ''),
                    'source': f"Dokumen PDF ({filename})", 
                    'content': text,
                    'type': 'pdf'
                })
            
    df = pd.DataFrame(data_pdf)
    print(f"✅ Berhasil membaca {len(df)} dokumen PDF.")
    return df

# --- 3. MODUL CLEANING & MERGING ---
def clean_text_logic(text):
    if not isinstance(text, str): return ""
    
    # 1. Hapus Metadata Web
    text = re.sub(r'Baca [Jj]uga.*?(?=\.|$)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*\([^)]*?Unhas.*?\)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'(Editor|Penulis)\s*[:|].*?$', '', text, flags=re.IGNORECASE)
    
    # 2. Perbaikan Typo OCR 
    for salah, benar in KAMUS_TYPO.items():
        text = text.replace(salah, benar)
        
    # 3. Fix Bullet Points
    text = re.sub(r'(?m)^\s*([a-z])\s+', r'\1. ', text)

    # 4. Final Trim (Hanya hapus spasi/tab berlebih)
    text = re.sub(r'[ \t]+', ' ', text) 
    text = re.sub(r'\n\s*\n', '\n', text) 
    
    return text.strip()

def run_cleaning_merging(df_news, df_docs):
    print("\n[3/4] 🧹 Membersihkan & Menggabungkan Data...")
    
    # Gabung
    df_master = pd.concat([df_news, df_docs], ignore_index=True)
    
    if df_master.empty:
        print("❌ Tidak ada data untuk diproses.")
        return df_master

    # Deduplikasi source
    total_awal = len(df_master)
    df_master = df_master.drop_duplicates(subset=['source'])
    
    # Cleaning Progress
    tqdm.pandas(desc="Cleaning Content")
    df_master['clean_content'] = df_master['content'].progress_apply(clean_text_logic)
    
    # Filter konten pendek
    df_master = df_master[df_master['clean_content'].str.len() > 50]
    
    print(f"✅ Data siap: {len(df_master)} items ({total_awal - len(df_master)} duplikat/sampah dibuang).")
    return df_master

# --- 4. MODUL CHUNKING ---
def run_chunking_export(df):
    print("\n[4/4] 🔪 Chunking & Export JSONL...")
    
    # chunk 1000, overlap 200
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    jsonl_data = []
    
    for index, row in tqdm(df.iterrows(), total=df.shape[0], desc="Chunking"):
        chunks = text_splitter.split_text(row['clean_content'])
        
        for i, chunk in enumerate(chunks):
            entry = {
                "id": f"{row['type']}_{index}_{i}",
                "title": row['title'],
                "source": row['source'], 
                "text": chunk
            }
            jsonl_data.append(entry)
            
    # Simpan
    with open(OUTPUT_JSONL, 'w', encoding='utf-8') as f:
        for entry in jsonl_data:
            json.dump(entry, f)
            f.write('\n')
            
    print(f"\n🎉 SELESAI! Pipeline sukses.")
    print(f"📂 Output File: knowledge_base_unhas.jsonl")
    print(f"📊 Total Chunks: {len(jsonl_data)}")

# --- MAIN ---
if __name__ == "__main__":
    # Langkah 1: Scrape Berita
    df_news = run_news_scraper()
    
    # Langkah 2: Baca PDF
    df_docs = run_ingestion_pdf()
    
    # Langkah 3: Gabung & Bersihkan
    df_master = run_cleaning_merging(df_news, df_docs)
    
    # Langkah 4: Potong & Simpan
    if not df_master.empty:
        run_chunking_export(df_master)
    else:
        print("\n❌ Pipeline berhenti: Data kosong.")