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

def crawl():
    url_rss = "https://www.cnbcindonesia.com/news/rss"
    
    target_keywords = [
        'lingkungan', 'iklim', 'emisi', 'karbon', 'esg', 'hijau', 
        'sustainability', 'energi', 'listrik', 'ev', 'ebt', 'plts', 
        'hutan', 'polusi', 'sampah', 'keberlanjutan', 'alam'
    ]
    
    print("📡 Mencari berita sesuai tema Environmental Sustainability...")
    
    try:
        response = requests.get(url_rss, headers=headers, timeout=20)
        soup = BeautifulSoup(response.content, 'xml')
        items = soup.find_all('item')
        
        results = []
        count = 0
        target_data = 5 
        
        for item in items:
            if count >= target_data:
                break
                
            judul = item.title.text
            link = item.link.text
            
            if any(key in judul.lower() for key in target_keywords):
                print(f"✅ Relevan ({count+1}): {judul[:50]}...")
                
                isi = ambil_isi_berita(link)
                
                res_det = requests.get(link, headers=headers, timeout=10)
                s_det = BeautifulSoup(res_det.text, 'lxml')
                img = s_det.find('meta', attrs={'property': 'og:image'})
                
                data = {
                    'url': link,
                    'judul': judul,
                    'tanggal_publish': item.pubDate.text,
                    'author': "Redaksi CNBC",
                    'tag_kategori': "Environmental Sustainability", 
                    'isi_berita': isi, 
                    'thumbnail': img['content'] if img else None,
                    'scraped_at': time.strftime("%Y-%m-%d %H:%M:%S")
                }
                
                results.append(InsertOne(data))
                count += 1
                time.sleep(3) 
            else:
                continue

        if results:
            collections.bulk_write(results)
            print(f"\n🚀 BERHASIL! {len(results)} data tema lingkungan sudah masuk ke MongoDB Atlas.")
        else:
            print("\n⚠️ Tidak ada berita lingkungan baru di RSS saat ini. Coba lagi nanti.")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    crawl()