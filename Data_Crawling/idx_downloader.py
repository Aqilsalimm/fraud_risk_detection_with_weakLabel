#!/usr/bin/env python3
"""
IDX Bulk Document Downloader
Created by Antigravity (Senior Data Engineer)

This script downloads Financial Statements and Annual Reports of listed non-financial companies
from the Indonesia Stock Exchange (IDX) website and saves them directly to Google Drive (or local storage).
It uses curl_cffi to bypass Cloudflare protection without Selenium.
"""

import os
import sys
import time
import random
import logging
import argparse
import urllib.parse
from typing import Dict, List, Set, Any

# Dynamically install curl_cffi if not present (useful in Google Colab)
try:
    import curl_cffi
except ImportError:
    import subprocess
    print("curl_cffi not found. Installing curl_cffi (Cloudflare bypass library)...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "curl_cffi"])

# Dynamically install tqdm if not present
try:
    from tqdm.auto import tqdm
except ImportError:
    import subprocess
    print("tqdm not found. Installing tqdm (progress bar)...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tqdm"])
    from tqdm.auto import tqdm

# Dynamically install pandas if not present
try:
    import pandas as pd
except ImportError:
    import subprocess
    print("pandas not found. Installing pandas...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas"])
    import pandas as pd

from curl_cffi import requests

# ==========================================
# CONFIGURATION & INITIALIZATION
# ==========================================

# Setup Google Drive path fallback
DEFAULT_DRIVE_PATH = "/content/drive/My Drive/Colab/IDX_Reports"

# Configure logging
log_filename = "idx_downloader.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Helper function to mount drive in Google Colab
def mount_google_drive():
    try:
        from google.colab import drive
        # Mount Google Drive
        drive.mount('/content/drive')
        
        # Tentukan direktori penyimpanan
        BASE_PATH = '/content/drive/My Drive/Colab/IDX_Reports'
        if not os.path.exists(BASE_PATH):
            os.makedirs(BASE_PATH)
            print(f"Folder dibuat: {BASE_PATH}")
        return True
    except ImportError:
        logging.info("Berjalan di lingkungan non-Colab. File akan disimpan secara lokal.")
        return False

# ==========================================
# URL CLEANER & NORMALIZER
# ==========================================

def clean_url(url: str) -> str:
    """
    Cleans and encodes the URL, handling spaces, special characters,
    and double slashes in paths.
    """
    if not url:
        return url
    try:
        parsed = urllib.parse.urlparse(url)
        path = parsed.path
        # Normalize double slashes in path (but keep single leading slash)
        while '//' in path:
            path = path.replace('//', '/')
        # Safely quote the path, keeping slashes safe
        quoted_path = urllib.parse.quote(path, safe='/')
        # Reconstruct URL
        return urllib.parse.urlunparse((
            parsed.scheme,
            parsed.netloc,
            quoted_path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
    except Exception as e:
        logging.warning(f"Gagal membersihkan URL '{url}': {e}")
        return url

# ==========================================
# REQUEST HANDLER WITH RETRY & BACKOFF
# ==========================================

def make_request(session: requests.Session, url: str, headers: Dict[str, str], params: Dict[str, Any] = None, retries: int = 3, backoff: float = 2.0, timeout: int = 90) -> requests.Response:
    """
    Sends a GET request with automatic retry and exponential backoff.
    Uses curl_cffi to impersonate Chrome.
    """
    for attempt in range(retries):
        try:
            # We impersonate chrome to bypass Cloudflare JA3 fingerprints
            response = session.get(url, headers=headers, params=params, impersonate="chrome", timeout=timeout)
            if response.status_code == 200:
                return response
            elif response.status_code in [429, 502, 503, 504]:
                wait_time = (backoff ** attempt) + random.uniform(0.5, 1.5)
                logging.warning(f"Terjadi HTTP {response.status_code} untuk {url}. Mencoba kembali dalam {wait_time:.2f} detik... (Percobaan {attempt + 1}/{retries})")
                time.sleep(wait_time)
            else:
                # Other status codes (e.g. 403, 404) are returned immediately to be logged
                return response
        except Exception as e:
            if attempt == retries - 1:
                raise e
            wait_time = (backoff ** attempt) + random.uniform(0.5, 1.5)
            logging.warning(f"Error koneksi untuk {url}: {e}. Mencoba kembali dalam {wait_time:.2f} detik... (Percobaan {attempt + 1}/{retries})")
            time.sleep(wait_time)
    
    return None

# ==========================================
# ATTACHMENT FETCHER & CATEGORIZER
# ==========================================

def fetch_attachments(session: requests.Session, ticker: str, year: int) -> List[Dict[str, Any]]:
    """
    Fetches the attachment list for a ticker and year.
    Queries both rdf and fs report types.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Referer': 'https://www.idx.co.id/id/perusahaan-tercatat/laporan-keuangan-dan-tahunan/',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9,id;q=0.8'
    }
    
    attachments = []
    seen_paths = set()
    
    # We query both 'rdf' and 'fs' report types
    for r_type in ['rdf', 'fs']:
        # Try 'audit' first, fall back to 'tahunan' if no results
        for period in ['audit', 'tahunan']:
            url = f"https://www.idx.co.id/primary/ListedCompany/GetFinancialReport?kodeEmiten={ticker}&year={year}&periode={period}&reportType={r_type}&indexFrom=1&pageSize=50"
            try:
                response = make_request(session, url, headers)
                status_code = response.status_code if response else "NO_RESPONSE"
                logging.info(f"API Request: {ticker} | Year: {year} | Type: {r_type} | Period: {period} | Status: {status_code}")
                
                if response and response.status_code == 200:
                    data = response.json()
                    results = data.get('Results', [])
                    if results:
                        att_count = 0
                        for result in results:
                            for att in result.get('Attachments', []):
                                file_path = att.get('File_Path')
                                if file_path and file_path not in seen_paths:
                                    seen_paths.add(file_path)
                                    attachments.append(att)
                                    att_count += 1
                        logging.info(f"Ditemukan {att_count} lampiran baru untuk {r_type}/{period}")
                        break  # Stop trying fallback periods if results are found
                    else:
                        logging.info(f"Tidak ada hasil (Results kosong) untuk {r_type}/{period}")
                else:
                    logging.warning(f"API Request gagal dengan status {status_code} untuk {r_type}/{period}")
            except Exception as e:
                logging.error(f"Gagal mengambil daftar dokumen {ticker} tahun {year} ({r_type}/{period}): {e}")
                
    return attachments

def categorize_file(filename: str) -> str:
    """
    Categorizes the file based on its name.
    Returns: 'Laporan_Keuangan', 'Laporan_Tahunan', or 'Dokumen_Lainnya'
    """
    fn_lower = filename.lower()
    
    # Checked indicators for Laporan Tahunan (Annual Report)
    annual_indicators = ["annualreport", "annual report", "annual_report", "laporan tahunan", "laporan_tahunan"]
    for ind in annual_indicators:
        if ind in fn_lower:
            return "Laporan_Tahunan"
    
    # Specific short codes for Annual Report
    if fn_lower.startswith("ar20") or fn_lower.startswith("ar_20") or fn_lower.startswith("ar-20") or fn_lower.startswith("ar 20"):
        return "Laporan_Tahunan"
        
    # Checked indicators for Laporan Keuangan (Financial Statement)
    financial_indicators = ["financialstatement", "financial statement", "financial_statement", "laporan keuangan", "laporan_keuangan", "lkb"]
    for ind in financial_indicators:
        if ind in fn_lower:
            return "Laporan_Keuangan"
            
    # Specific short codes for Laporan Keuangan
    if fn_lower.startswith("lk ") or fn_lower.startswith("lk_") or fn_lower.startswith("lk-") or fn_lower.startswith("lk20"):
        return "Laporan_Keuangan"
        
    # Heuristics based on key terms
    if "lk" in fn_lower or "financial" in fn_lower:
        return "Laporan_Keuangan"
    elif "annual" in fn_lower or "report" in fn_lower or "ar" in fn_lower:
        return "Laporan_Tahunan"
        
    return "Dokumen_Lainnya"

# ==========================================
# MAIN EXECUTION WORKFLOW
# ==========================================

def run_downloader(sheet_url: str, output_dir: str):
    # Ensure root output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    logging.info("==== IDX Bulk Document Downloader Started ====")
    logging.info(f"Membaca data daftar perusahaan dari: {sheet_url}")
    
    try:
        # Check if the file is an Excel file based on extension (case-insensitive)
        is_excel = sheet_url.lower().endswith(('.xlsx', '.xls'))
        
        if is_excel:
            try:
                import openpyxl
            except ImportError:
                import subprocess, sys
                logging.info("openpyxl tidak ditemukan. Menginstal openpyxl untuk membaca file Excel...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl"])
            df = pd.read_excel(sheet_url)
        else:
            # Assume CSV (either URL or local path)
            df = pd.read_csv(sheet_url)
            
        df.columns = [c.strip() for c in df.columns]
    except Exception as e:
        logging.error(f"Gagal membaca file daftar perusahaan: {e}")
        print(f"Error: Detail: {e}")
        return

    # Filter Valid Emiten
    original_count = len(df)
    df_valid = df[df['Status'].astype(str).str.strip().str.lower() == 'valid'].copy()
    valid_count = len(df_valid)
    
    logging.info(f"Total emiten di Sheet: {original_count}")
    logging.info(f"Total emiten Valid untuk diproses: {valid_count}")
    
    if valid_count == 0:
        logging.warning("Tidak ada emiten dengan status 'Valid' untuk diproses.")
        return

    # Years to process
    years = [2021, 2022, 2023, 2024]
    
    # Initialize statistics
    total_success_downloads = 0
    total_failed_downloads = 0
    total_bytes_downloaded = 0
    failed_emiten_list = []
    
    # Create persistent session with curl_cffi
    session = requests.Session()
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Referer': 'https://www.idx.co.id/id/perusahaan-tercatat/laporan-keuangan-dan-tahunan/',
        'Accept': 'application/pdf,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,id;q=0.8'
    }
    
    # Warm up session to get cookies and pass Cloudflare clearance
    logging.info("Memanaskan session scraping (mengakses idx.co.id)...")
    try:
        session.get("https://www.idx.co.id/", headers=headers, impersonate="chrome", timeout=20)
        time.sleep(2)
        logging.info("Session berhasil dipanaskan.")
    except Exception as e:
        logging.warning(f"Gagal memanaskan session: {e}")
    
    # Initialize Outer TQDM Progress Bar
    pbar = tqdm(df_valid.iterrows(), total=valid_count, desc="Memproses Emiten")
    
    for idx, row in pbar:
        ticker = str(row['Kode']).strip()
        company_name = str(row['Nama Perusahaan']).strip()
        
        pbar.set_description(f"Emiten: {ticker}")
        
        # Process each year
        for year in years:
            logging.info(f"Memproses {ticker} ({company_name}) - Tahun {year}...")
            
            # Fetch attachments list
            try:
                attachments = fetch_attachments(session, ticker, year)
            except Exception as e:
                logging.error(f"Gagal mencari dokumen untuk {ticker} {year}: {e}")
                failed_emiten_list.append({
                    "Kode Emiten": ticker,
                    "Nama Emiten": company_name,
                    "Tahun": year,
                    "Jenis Dokumen": "Daftar Lampiran",
                    "Alasan Kegagalan": f"Gagal fetch list: {e}"
                })
                total_failed_downloads += 1
                continue
                
            pdf_attachments = [a for a in attachments if a.get('File_Name', '').lower().endswith('.pdf')]
            
            if not pdf_attachments:
                logging.warning(f"Tidak ada file PDF ditemukan untuk {ticker} {year}")
                failed_emiten_list.append({
                    "Kode Emiten": ticker,
                    "Nama Emiten": company_name,
                    "Tahun": year,
                    "Jenis Dokumen": "Laporan Keuangan/Tahunan",
                    "Alasan Kegagalan": "Tidak ada file PDF ditemukan di IDX API"
                })
                total_failed_downloads += 1
                continue
                
            # Download files
            for att in pdf_attachments:
                filename = att.get('File_Name')
                file_path = att.get('File_Path')
                
                if not filename or not file_path:
                    continue
                
                category = categorize_file(filename)
                
                # Setup output folder structure: {root}/{Ticker}/{Year}/{Category}/
                dest_dir = os.path.join(output_dir, ticker, str(year), category)
                dest_file_path = os.path.join(dest_dir, filename)
                
                # Skip if file already exists with non-zero size
                if os.path.exists(dest_file_path) and os.path.getsize(dest_file_path) > 1000:
                    logging.info(f"File {filename} sudah ada. Melewati...")
                    continue
                
                # Handle full vs relative URLs
                if not file_path.startswith("http"):
                    download_url = f"https://www.idx.co.id{file_path}"
                else:
                    download_url = file_path
                
                # Clean and url-encode spaces/slashes in the URL
                download_url = clean_url(download_url)
                    
                logging.info(f"Mengunduh {filename} ({category})...")
                
                try:
                    # Download with temp file mechanism to avoid corrupt files
                    os.makedirs(dest_dir, exist_ok=True)
                    temp_file_path = dest_file_path + ".tmp"
                    
                    # File downloads are given a longer timeout (180 seconds)
                    response = make_request(session, download_url, headers, timeout=180)
                    if response and response.status_code == 200:
                        if len(response.content) < 2000 and b"Cloudflare" in response.content:
                            raise Exception("Terblokir tantangan Cloudflare saat download file")
                            
                        with open(temp_file_path, 'wb') as f:
                            f.write(response.content)
                        os.replace(temp_file_path, dest_file_path)
                        
                        file_size = len(response.content)
                        total_bytes_downloaded += file_size
                        total_success_downloads += 1
                        logging.info(f"Sukses mengunduh {filename} ({file_size / 1024 / 1024:.2f} MB)")
                    else:
                        status = response.status_code if response else "No Response"
                        raise Exception(f"HTTP Status {status}")
                except Exception as e:
                    logging.error(f"Gagal mengunduh file {filename}: {e}")
                    # Clean up temp file if it exists
                    if os.path.exists(temp_file_path):
                        try:
                            os.remove(temp_file_path)
                        except Exception:
                            pass
                    failed_emiten_list.append({
                        "Kode Emiten": ticker,
                        "Nama Emiten": company_name,
                        "Tahun": year,
                        "Jenis Dokumen": category,
                        "Alasan Kegagalan": f"Download gagal: {e}"
                    })
                    total_failed_downloads += 1
                    
            # Polite sleep between processing items
            time.sleep(random.uniform(1.0, 2.5))
            
    # Print execution summary
    print("\n" + "="*50)
    print("RINGKASAN EKSEKUSI DOWNLOAD")
    print("="*50)
    print(f"Total File Berhasil Diunduh : {total_success_downloads}")
    print(f"Total File/Emiten Gagal     : {total_failed_downloads}")
    print(f"Ukuran Total Penyimpanan    : {total_bytes_downloaded / 1024 / 1024:.2f} MB")
    print(f"File Log Tersimpan Di      : {os.path.abspath(log_filename)}")
    print(f"Dokumen Tersimpan Di       : {os.path.abspath(output_dir)}")
    print("="*50)
    
    if failed_emiten_list:
        print("\nTabel Kegagalan Unduh:")
        df_failures = pd.DataFrame(failed_emiten_list)
        # Format markdown table
        try:
            from IPython.display import display, HTML
            display(df_failures)
        except:
            try:
                print(df_failures.to_markdown(index=False))
            except ImportError:
                print(df_failures.to_string(index=False))
    else:
        print("\nSemua dokumen berhasil diunduh tanpa kegagalan!")

# ==========================================
# ENTRY POINT
# ==========================================

if __name__ == "__main__":
    # Auto-detect default sheet: local XLSX file if exists, otherwise Google Sheet URL
    default_sheet = "Rekap_Perusahaan_2021_2024.xlsx"
    if not os.path.exists(default_sheet):
        default_sheet = "https://docs.google.com/spreadsheets/d/1RzTcxLJ2dUH0_pL9ZIzqgOMQpNbAeCk-r-PZYNnE0d8/export?format=csv&gid=0"

    parser = argparse.ArgumentParser(description="IDX Bulk Document Downloader")
    parser.add_argument('--sheet', type=str, default=default_sheet,
                        help="Path ke file excel/csv daftar perusahaan atau URL Google Sheets")
    parser.add_argument('--output', type=str, default=None,
                        help="Output directory path (defaults to Google Drive in Colab)")
    args = parser.parse_args()

    # Mount Google Drive if in Google Colab environment
    is_colab = mount_google_drive()
    
    # Determine the target output directory
    if args.output:
        target_dir = args.output
    elif is_colab:
        target_dir = DEFAULT_DRIVE_PATH
    else:
        target_dir = r"G:\My Drive\Dataset PUI-PT\IDX_Downloads"
        
    run_downloader(args.sheet, target_dir)
