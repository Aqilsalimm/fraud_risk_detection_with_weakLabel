#!/usr/bin/env python3
"""
IDX Retry Downloader
Created by Antigravity (Senior Data Engineer)

This script parses 'idx_downloader.log' to find any failed file downloads,
then queries the IDX API to retry only those failed tickers/years.
It uses functions imported from idx_downloader.py to maintain consistency.
"""

import os
import re
import sys
import time
import random
import logging
import argparse
import pandas as pd
from typing import Dict, List, Set, Tuple, Any

# Ensure we can import from idx_downloader
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from idx_downloader import (
        make_request,
        fetch_attachments,
        categorize_file,
        mount_google_drive,
        DEFAULT_DRIVE_PATH,
        clean_url
    )
except ImportError:
    print("Error: idx_downloader.py tidak ditemukan di folder yang sama!")
    sys.exit(1)

try:
    from curl_cffi import requests
except ImportError:
    import subprocess
    print("Installing curl_cffi...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "curl_cffi"])
    from curl_cffi import requests

try:
    from tqdm.auto import tqdm
except ImportError:
    import subprocess
    print("Installing tqdm...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tqdm"])
    from tqdm.auto import tqdm

# Clear any existing logging handlers (to override idx_downloader's config)
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Configure logging
log_filename = "idx_retry.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

def parse_failed_from_log(log_path: str) -> Set[Tuple[str, int]]:
    """
    Parses the log file to identify ticker-year combinations that failed.
    """
    failed_pairs = set()
    if not os.path.exists(log_path):
        logging.warning(f"File log {log_path} tidak ditemukan!")
        return failed_pairs
        
    current_ticker = None
    current_year = None
    
    # Matches: 2026-06-20 21:05:05,704 [INFO] Memproses BTON (Betonjaya Manunggal Tbk) - Tahun 2021...
    proc_pattern = re.compile(r"Memproses\s+(\w+)\s+\(.*\)\s+-\s+Tahun\s+(\d{4})")
    # Matches: 2026-06-20 21:06:11,138 [ERROR] Gagal mengunduh file AnnualReport2021-BTON-att1.pdf: ...
    err_pattern = re.compile(r"\[ERROR\]\s+Gagal\s+mengunduh\s+file")
    # Matches: Gagal mencari dokumen untuk BTON 2021: ...
    err_list_pattern = re.compile(r"Gagal mencari dokumen untuk\s+(\w+)\s+(\d{4})")
    
    logging.info(f"Membaca file log: {log_path}...")
    
    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            proc_match = proc_pattern.search(line)
            if proc_match:
                current_ticker = proc_match.group(1)
                current_year = int(proc_match.group(2))
                continue
                
            if err_pattern.search(line):
                if current_ticker and current_year:
                    failed_pairs.add((current_ticker, current_year))
                    
            list_match = err_list_pattern.search(line)
            if list_match:
                failed_pairs.add((list_match.group(1), int(list_match.group(2))))
                    
    return failed_pairs

def run_retry(sheet_url: str, output_dir: str, log_path: str):
    failed_pairs = parse_failed_from_log(log_path)
    
    if not failed_pairs:
        logging.info("Tidak ditemukan riwayat kegagalan di file log. Semua file berhasil terunduh!")
        return

    logging.info(f"Ditemukan {len(failed_pairs)} kombinasi emiten-tahun yang sempat gagal:")
    for t, y in sorted(failed_pairs):
        logging.info(f"  - {t} ({y})")

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Read the sheet to verify company names
    try:
        is_excel = sheet_url.lower().endswith(('.xlsx', '.xls'))
        if is_excel:
            df = pd.read_excel(sheet_url)
        else:
            df = pd.read_csv(sheet_url)
        df.columns = [c.strip() for c in df.columns]
    except Exception as e:
        logging.error(f"Gagal membaca file daftar perusahaan: {e}")
        return

    # Filter dataframe to keep only valid companies
    df_valid = df[df['Status'].astype(str).str.strip().str.lower() == 'valid'].copy()

    # Filter dataframe to keep only the failed tickers to map company names
    failed_tickers = {t for t, y in failed_pairs}
    df_valid = df_valid[df_valid['Kode'].astype(str).str.strip().isin(failed_tickers)].copy()

    # Create session with curl_cffi
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Referer': 'https://www.idx.co.id/id/perusahaan-tercatat/laporan-keuangan-dan-tahunan/',
        'Accept': 'application/pdf,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,id;q=0.8'
    }

    logging.info("Memanaskan session scraping (mengakses idx.co.id)...")
    try:
        session.get("https://www.idx.co.id/", headers=headers, impersonate="chrome", timeout=20)
        time.sleep(2)
        logging.info("Session berhasil dipanaskan.")
    except Exception as e:
        logging.warning(f"Gagal memanaskan session: {e}")

    total_success = 0
    total_failed = 0
    total_bytes = 0
    failed_retry_list = []

    pbar = tqdm(sorted(failed_pairs), desc="Mengulang Unduhan Gagal")
    for ticker, year in pbar:
        pbar.set_description(f"Retry: {ticker} ({year})")
        
        # Get company name
        matching_rows = df_valid[df_valid['Kode'].astype(str).str.strip() == ticker]
        if matching_rows.empty:
            logging.info(f"Melewati retry {ticker} tahun {year} karena statusnya 'Tidak Valid' atau tidak ditemukan di Sheet.")
            continue
        company_name = str(matching_rows.iloc[0]['Nama Perusahaan']).strip()

        logging.info(f"Memproses ulang {ticker} ({company_name}) - Tahun {year}...")
        
        try:
            attachments = fetch_attachments(session, ticker, year)
        except Exception as e:
            logging.error(f"Gagal mencari dokumen untuk {ticker} {year}: {e}")
            failed_retry_list.append({
                "Kode Emiten": ticker,
                "Nama Emiten": company_name,
                "Tahun": year,
                "Jenis Dokumen": "Daftar Lampiran",
                "Alasan Kegagalan": f"Gagal fetch list: {e}"
            })
            total_failed += 1
            continue

        pdf_attachments = [a for a in attachments if a.get('File_Name', '').lower().endswith('.pdf')]
        
        if not pdf_attachments:
            logging.warning(f"Tidak ada file PDF ditemukan untuk {ticker} {year}")
            continue

        for att in pdf_attachments:
            filename = att.get('File_Name')
            file_path = att.get('File_Path')
            
            if not filename or not file_path:
                continue

            category = categorize_file(filename)
            dest_dir = os.path.join(output_dir, ticker, str(year), category)
            dest_file_path = os.path.join(dest_dir, filename)

            # Skip if file already exists with non-zero size
            if os.path.exists(dest_file_path) and os.path.getsize(dest_file_path) > 1000:
                logging.info(f"File {filename} sudah ada. Melewati...")
                continue

            if not file_path.startswith("http"):
                download_url = f"https://www.idx.co.id{file_path}"
            else:
                download_url = file_path

            # Clean and url-encode spaces/slashes in the URL
            download_url = clean_url(download_url)

            logging.info(f"Mengunduh {filename} ({category})...")

            try:
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
                    total_bytes += file_size
                    total_success += 1
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
                failed_retry_list.append({
                    "Kode Emiten": ticker,
                    "Nama Emiten": company_name,
                    "Tahun": year,
                    "Jenis Dokumen": category,
                    "Alasan Kegagalan": f"Download gagal: {e}"
                })
                total_failed += 1

        time.sleep(random.uniform(1.0, 2.5))

    # Print retry execution summary
    print("\n" + "="*50)
    print("RINGKASAN RE-DOWNLOAD RETRY")
    print("="*50)
    print(f"Total File Berhasil Diunduh : {total_success}")
    print(f"Total File Gagal            : {total_failed}")
    print(f"Ukuran Total Penyimpanan    : {total_bytes / 1024 / 1024:.2f} MB")
    print(f"File Log Retry Tersimpan Di : {os.path.abspath(log_filename)}")
    print("="*50)

    if failed_retry_list:
        print("\nTabel Kegagalan Unduh Ulang:")
        df_failures = pd.DataFrame(failed_retry_list)
        try:
            print(df_failures.to_markdown(index=False))
        except ImportError:
            print(df_failures.to_string(index=False))
    else:
        print("\nSemua dokumen retry berhasil diunduh tanpa kegagalan!")

if __name__ == "__main__":
    # Auto-detect default sheet: local XLSX file if exists, otherwise Google Sheet URL
    default_sheet = "Rekap_Perusahaan_2021_2024.xlsx"
    if not os.path.exists(default_sheet):
        default_sheet = "https://docs.google.com/spreadsheets/d/1RzTcxLJ2dUH0_pL9ZIzqgOMQpNbAeCk-r-PZYNnE0d8/export?format=csv&gid=0"

    parser = argparse.ArgumentParser(description="IDX Retry Failed Downloads")
    parser.add_argument('--sheet', type=str, default=default_sheet,
                        help="Path ke file excel/csv daftar perusahaan atau URL Google Sheets")
    parser.add_argument('--output', type=str, default=None,
                        help="Output directory path (defaults to Google Drive in Colab)")
    parser.add_argument('--log', type=str, default="idx_downloader.log",
                        help="Path ke file log downloader utama")
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
        
    run_retry(args.sheet, target_dir, args.log)
