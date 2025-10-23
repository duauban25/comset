# CompSet Dashboard - Daun Bali Seminyak

## Setup Shared Data
1. Install Google Drive app dari drive.google.com (atau Dropbox).
2. Join shared folder "CompSet-Data" (link: [paste link Google Drive]).
3. Sync folder ke komputer kamu (biar file CSV otomatis tersedia).

## Persiapan App
1. Install Python 3.8+ dari python.org.
2. Masuk folder app: `cd path/ke/comp-set-dashboard`.
3. Install library: `pip install -r requirements.txt`.

## Jalankan App
- `streamlit run app.py`
- Buka di browser: http://localhost:8501.
- Input data → otomatis save ke shared CSV, tim lain langsung lihat update setelah sync!

## Tips
- Sync Drive harus ON agar data real-time.
- Kalau konflik edit (dua orang edit bareng), Drive kasih versi konflik – pilih yang baru.
- Stop app: Ctrl+C.
