import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient, InsertOne
import time

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
        
       
        body = soup.select_one('.detail_text') or \
               soup.select_one('.detail__body-text') or \
               soup.select_one('.itp_bodycontent') or \
               soup.select_one('.detail_video-text') 

        if body:
            paragraphs = body.find_all('p')
            if paragraphs:
                teks = " ".join([p.get_text(strip=True) for p in paragraphs])
            else:
                teks = body.get_text(strip=True)
        else:
            article_tag = soup.find('article')
            teks = article_tag.get_text(strip=True) if article_tag else "Isi tidak ditemukan"
            
        noise = ["ADVERTISEMENT", "SCROLL TO RESUME CONTENT", "Pilihan Redaksi", "Baca:"]
        for n in noise:
            teks = teks.replace(n, "")
            
        return teks[:1500].strip()
    except Exception as e:
        return f"Gagal akses: {str(e)}"

def crawl_3_data_perbaikan():
    url_rss = "https://www.cnbcindonesia.com/news/rss"
    print("📡 Menghubungkan ke RSS...")
    
    try:
        response = requests.get(url_rss, headers=headers, timeout=20)
        soup = BeautifulSoup(response.content, 'xml')
        items = soup.find_all('item')[:3] 
        
        results = []
        for i, item in enumerate(items):
            link = item.link.text
            judul = item.title.text
            print(f"📦 ({i+1}/3) Mendownload: {judul[:40]}...")
            
            isi = ambil_isi_berita(link)
            
            res_det = requests.get(link, headers=headers, timeout=10)
            s_det = BeautifulSoup(res_det.text, 'lxml')
            img = s_det.find('meta', attrs={'property': 'og:image'})
            
            data = {
                'url': link,
                'judul': judul,
                'tanggal_publish': item.pubDate.text,
                'author': "Redaksi CNBC",
                'tag_kategori': "News",
                'isi_berita': isi, 
                'thumbnail': img['content'] if img else None,
                'scraped_at': time.strftime("%Y-%m-%d %H:%M:%S")
            }
            results.append(InsertOne(data))
            time.sleep(3) 

        if results:
            collections.bulk_write(results)
            print(f"\n✅ BERHASIL! Cek MongoDB Compass kamu sekarang.")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    crawl_3_data_perbaikan()