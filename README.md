# Unhas Preprocessing Pipeline (ETL for RAG)

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Pandas](https://img.shields.io/badge/Pandas-Data_Processing-green)
![Tesseract](https://img.shields.io/badge/OCR-Tesseract-yellow)
![LangChain](https://img.shields.io/badge/LangChain-Chunking-orange)

## 📋 Deskripsi Proyek
Proyek ini adalah sebuah Data Ingestion Pipeline yang dirancang untuk membangun knowledge base chatbot berbasis RAG (Retrieval-Augmented Generation). Sistem ini secara otomatis mengumpulkan, membersihkan, dan memproses data dari dua sumber utama: Website Berita Universitas Hasanuddin dan Dokumen PDF (SOP/Peraturan Akademik).

Tujuan utamanya adalah mengubah data mentah yang tidak terstruktur menjadi format JSONL yang sudah terpotong-potong secara semantik (chunked), sehingga siap untuk diproses oleh embedding model dan disimpan ke dalam vector database.

## ✨ Fitur Utama
- Automated Web Scraping: Mengambil konten berita terbaru dari situs resmi Unhas menggunakan BeautifulSoup.
- OCR Document Digitization: Mengubah dokumen PDF hasil pemindaian (seperti aturan perpustakaan atau SOP) menjadi teks digital menggunakan Tesseract OCR dan Poppler.
- Cleaning:
  - Normalisasi teks dan pembersihan noise web (iklan, header, metadata).
  - Perbaikan kesalahan baca (OCR Typos) menggunakan kamus koreksi kustom.
  - Standardisasi format poin-poin (bullet points) dan spasi.
  - Chunking: Memotong teks menggunakan RecursiveCharacterTextSplitter dari LangChain dengan parameter chunk size 1000 dan overlap 200 untuk menjaga konteks antar potongan.

## 🛠️ Tech Stack
- Core: Python
- Data Analysis: Pandas, Numpy
- Scraping: Requests, BeautifulSoup4
- OCR & PDF: Pytesseract, Pdf2image, Poppler
- NLP Tools: LangChain (Text Splitters)
- Utility: TQDM (Progress Bar)

## 📂 Struktur Proyek
```
unhas-preprocessing-pipeline/
├── 📂 data/
│   ├── 📂 pdf/              # Tempat menaruh file PDF mentah (input)
│   └── 📂 processed/        # File CSV sementara hasil cleaning & merging
├── 📂 notebooks/            # File eksperimen (.ipynb) dan riset fungsi
├── 📂 output/               # Hasil akhir (knowledge_base_unhas.jsonl)
├── 📄 main_pipeline.py      # Script utama (Production-ready script)
├── 📄 requirements.txt      # Daftar library yang dibutuhkan
└── 📄 README.md             # Dokumentasi proyek
```

## ⚙️ Instalasi & Persiapan
1. Prasyarat Sistem
Pastikan kamu telah menginstall perangkat lunak pendukung OCR berikut di sistem operasi kamu:
  - Tesseract OCR: [Download Installer Windows (UB-Mannheim)](https://github.com/UB-Mannheim/tesseract/wiki)
  - Poppler: [Download Poppler Terbaru](https://github.com/oschwartz10612/poppler-windows/releases)

2. Instalasi Library
```Bash
git clone https://github.com/Data4nalyst/unhas-preprocessing-pipeline.git
cd unhas-preprocessing-pipeline
pip install -r requirements.txt
```

3. Konfigurasi Path 
Agar OCR berfungsi, Anda wajib memberi tahu program di mana lokasi Tesseract dan Poppler terinstall di komputer Anda.
  - Buka file main_pipeline.py.
  - Cari bagian KONFIGURASI (sekitar baris 15).
  - Ubah variabel berikut sesuai lokasi instalasi di komputer Anda:
  ```Python
  # CONTOH (Sesuaikan dengan path di komputer Anda):
  pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files/Tesseract-OCR/tesseract.exe'
  POPPLER_PATH = 'C:/poppler-25.12.0/Library/bin' 
  ```

## 🚀 Cara Penggunaan
1. Masukkan file PDF yang ingin diproses ke dalam folder data/pdf/.
2. Jalankan pipeline utama melalui terminal:
```Bash
python main_pipeline.py
```
3. Pantau prosesnya melalui loading bar yang muncul. Setelah selesai, file hasil akhir akan tersedia di output/knowledge_base_unhas.jsonl.

## 📄 Contoh Output (JSONL)
Setiap baris dalam file output merepresentasikan satu chunk data:
```JSON
{
  "id": "pdf_36_1",
  "title": "SK Rektor tentang Peraturan Pemanfaatan Koleksi Perpustakaan Unhas (2).pdf", 
  "source": "Dokumen PDF (SK Rektor tentang Peraturan Pemanfaatan Koleksi Perpustakaan Unhas (2).pdf)", 
  "text": "Menimbang : a. bahwa koleksi UPT Perpustakaan Universitas Hasanuddin merupakan asset..."
}
```