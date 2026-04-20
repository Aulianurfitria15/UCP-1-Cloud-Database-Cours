import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient, InsertOne
import time

# 1. KONEKSI MONGODB
MONGO_URI = 'mongodb+srv://aulianurfitria17_db_user:Telagasari15@testingp2.dq53zyn.mongodb.net/'
client = MongoClient(MONGO_URI)
collections = client['BelajarUcp']['UCP1_BasisData']

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def ambil_isi_berita(url):
    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'lxml')
        
        # Cari di semua kemungkinan container teks CNBC
        # 1. detail_text (Berita Biasa)
        # 2. detail__body-text (Format baru)
        # 3. detail_text (Untuk Video)
        # 4. itp_bodycontent (Format cadangan)
        body = soup.select_one('.detail_text') or \
               soup.select_one('.detail__body-text') or \
               soup.select_one('.itp_bodycontent') or \
               soup.select_one('.detail_video-text') # Khusus untuk video

        if body:
            # Cari semua paragraf
            paragraphs = body.find_all('p')
            if paragraphs:
                teks = " ".join([p.get_text(strip=True) for p in paragraphs])
            else:
                # Jika tidak ada tag p, ambil semua teks yang ada di dalam container
                teks = body.get_text(strip=True)
        else:
            # FALLBACK TERAKHIR: Jika semua selector gagal, 
            # ambil semua teks di dalam tag <article>
            article_tag = soup.find('article')
            teks = article_tag.get_text(strip=True) if article_tag else "Isi tidak ditemukan"
            
        # Pembersihan teks dari iklan dan noise
        noise = ["ADVERTISEMENT", "SCROLL TO RESUME CONTENT", "Pilihan Redaksi", "Baca:"]
        for n in noise:
            teks = teks.replace(n, "")
            
        return teks[:1500].strip() # Ambil 1500 karakter pertama
    except Exception as e:
        return f"Gagal akses: {str(e)}"

def crawl_3_data_perbaikan():
    url_rss = "https://www.cnbcindonesia.com/news/rss"
    print("📡 Menghubungkan ke RSS...")
    
    try:
        response = requests.get(url_rss, headers=headers, timeout=20)
        soup = BeautifulSoup(response.content, 'xml')
        items = soup.find_all('item')[:3] # Kita ambil 3 saja dulu untuk tes
        
        results = []
        for i, item in enumerate(items):
            link = item.link.text
            judul = item.title.text
            print(f"📦 ({i+1}/3) Mendownload: {judul[:40]}...")
            
            # Ambil isi berita dengan fungsi baru yang lebih kuat
            isi = ambil_isi_berita(link)
            
            # Ambil thumbnail
            res_det = requests.get(link, headers=headers, timeout=10)
            s_det = BeautifulSoup(res_det.text, 'lxml')
            img = s_det.find('meta', attrs={'property': 'og:image'})
            
            data = {
                'url': link,
                'judul': judul,
                'tanggal_publish': item.pubDate.text,
                'author': "Redaksi CNBC",
                'tag_kategori': "News",
                'isi_berita': isi, # <--- SEKARANG HARUSNYA ADA ISINYA
                'thumbnail': img['content'] if img else None,
                'scraped_at': time.strftime("%Y-%m-%d %H:%M:%S")
            }
            results.append(InsertOne(data))
            time.sleep(3) # Jeda agar aman

        if results:
            collections.bulk_write(results)
            print(f"\n✅ BERHASIL! Cek MongoDB Compass kamu sekarang.")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    crawl_3_data_perbaikan()