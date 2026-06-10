import os
import requests
from dotenv import load_dotenv
from deep_translator import GoogleTranslator
from groq import Groq

# .env dosyasını yükle
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
STRAPI_URL = os.getenv("STRAPI_URL")
STRAPI_EMAIL = os.getenv("STRAPI_ADMIN_EMAIL")
STRAPI_PASSWORD = os.getenv("STRAPI_ADMIN_PASSWORD")
TOKEN = os.getenv("TOKEN")


# -------------------------
# Mısır'daki mekanların ham verisi
# -------------------------
SEHIR = "Kahire"
ULKE = "Mısır"
SEHIR_ACIKLAMA = "Mısır'ın başkenti ve Afrika'nın en kalabalık şehri."

MEKANLAR = [
    {
        "name": "Giza Piramitleri",
        "description": "Dünyanın yedi harikasından biri olan Giza Piramitleri, MÖ 2560 yılında inşa edilmiştir. Firavun Keops için yapılan büyük piramit, antik dünyanın en etkileyici yapılarından biridir.",
        "score": 9.8
    },
    {
        "name": "Sfenks",
        "description": "Giza ovasında bulunan dev taş heykel, aslan gövdeli ve insan yüzlüdür. MÖ 2500 yıllarına tarihlenen Sfenks, Mısır'ın en tanınan simgelerinden biridir.",
        "score": 9.5
    },
    {
        "name": "Mısır Müzesi",
        "description": "Kahire'nin kalbinde yer alan müze, Firavun Tutankhamun'un altın maskesi dahil 120.000'den fazla tarihi esere ev sahipliği yapar.",
        "score": 9.2
    },
    {
        "name": "Karnak Tapınağı",
        "description": "Luksor'daki dev tapınak kompleksi, binlerce yıl boyunca inşa edilmiştir. Antik Mısır'ın en büyük dini yapılarından biridir.",
        "score": 9.0
    },
    {
        "name": "Abu Simbel Tapınakları",
        "description": "Firavun II. Ramses tarafından yaptırılan bu dev kaya tapınakları, Asvan yakınlarında bulunur ve UNESCO Dünya Mirası listesindedir.",
        "score": 9.6
    }
]


# -------------------------
# 1. GROQ ile metin zenginleştirme
# -------------------------
def zenginlestir(mekan_adi, aciklama):
    """Groq API kullanarak mekan açıklamasını genişletir."""
    print(f"  → Groq ile zenginleştiriliyor: {mekan_adi}")
    client = Groq(api_key=GROQ_API_KEY)
    prompt = f"""
Sen bir Mısır turizm uzmanısın. Aşağıdaki mekan hakkında turistlere yönelik,
ilgi çekici ve bilgilendirici bir açıklama yaz. Türkçe yaz. Maksimum 3 cümle.

Mekan: {mekan_adi}
Mevcut bilgi: {aciklama}
"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300
    )
    return response.choices[0].message.content.strip()


# -------------------------
# 2. Çeviri (TR → EN)
# -------------------------
def cevir(metin):
    """deep-translator ile Türkçe metni İngilizceye çevirir."""
    print(f"  → Çevriliyor...")
    translated = GoogleTranslator(source='tr', target='en').translate(metin)
    return translated


# -------------------------
# 3. Pollinations AI ile görsel üretimi ve indirme
# -------------------------
def gorsel_uret_ve_indir(mekan_adi, dosya_adi):
    """Pollinations AI ile mekan görseli üretir ve kaydeder."""
    print(f"  → Görsel üretiliyor: {mekan_adi}")
    prompt = f"Touristic landscape photo of {mekan_adi}, Egypt, ancient architecture, golden hour, high quality, photorealistic"
    prompt_encoded = requests.utils.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=800&height=600&nologo=true"

    response = requests.get(url, timeout=60)
    if response.status_code == 200:
        os.makedirs("gorseller", exist_ok=True)
        dosya_yolu = f"gorseller/{dosya_adi}.jpg"
        with open(dosya_yolu, "wb") as f:
            f.write(response.content)
        print(f"  → Görsel kaydedildi: {dosya_yolu}")
        return dosya_yolu
    else:
        print(f"  → Görsel üretilemedi!")
        return None


# -------------------------
# 4. Strapi JWT Token al
# -------------------------


# -------------------------
# 5. Strapi'ye Şehir ekle
# -------------------------
def sehir_ekle(token, ad, ulke, aciklama):
    """Strapi'ye yeni şehir kaydı ekler."""
    print(f"Şehir ekleniyor: {ad}")
    url = f"{STRAPI_URL}/api/cities"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"data": {"name": ad, "country": ulke, "description": aciklama}}
    response = requests.post(url, json=data, headers=headers)
    if response.status_code in [200, 201]:
        sehir_id = response.json()["data"]["id"]
        print(f"  → Şehir eklendi. ID: {sehir_id}")
        return sehir_id
    else:
        print(f"  → Hata: {response.text}")
        return None


# -------------------------
# 6. Görseli Strapi Media Library'ye yükle
# -------------------------
def gorsel_yukle(token, dosya_yolu, dosya_adi):
    """Görseli Strapi Media Library'ye yükler, dosya ID'sini döner."""
    print(f"  → Görsel Strapi'ye yükleniyor...")
    url = f"{STRAPI_URL}/api/upload"
    headers = {"Authorization": f"Bearer {token}"}
    with open(dosya_yolu, "rb") as f:
        files = {"files": (f"{dosya_adi}.jpg", f, "image/jpeg")}
        response = requests.post(url, headers=headers, files=files)
    if response.status_code in [200, 201]:
        media_id = response.json()[0]["id"]
        print(f"  → Görsel yüklendi. Media ID: {media_id}")
        return media_id
    else:
        print(f"  → Görsel yüklenemedi: {response.text}")
        return None


# -------------------------
# 7. Strapi'ye Mekan ekle
# -------------------------
def mekan_ekle(token, mekan, sehir_id, media_id, description_en):
    """Strapi'ye mekan kaydı ekler (TR + EN açıklama + görsel)."""
    print(f"  → Mekan Strapi'ye ekleniyor: {mekan['name']}")
    url = f"{STRAPI_URL}/api/places"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "data": {
            "name": mekan["name"],
            "description": mekan["description"],
            "description_en": description_en,
            "score": mekan["score"],
            "city": sehir_id,
            "cover": media_id
        }
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code in [200, 201]:
        print(f"  → Mekan eklendi!")
    else:
        print(f"  → Hata: {response.text}")


# -------------------------
# ANA DÖNGÜ
# -------------------------
def main():
    print("=" * 50)
    print("Mısır Gezi Rehberi Otomasyon Başlıyor")
    print("=" * 50)

    # Token al
    token = TOKEN

    # Şehri ekle
    sehir_id = sehir_ekle(token, SEHIR, ULKE, SEHIR_ACIKLAMA)
    if not sehir_id:
        print("Şehir eklenemedi, işlem durduruluyor.")
        return

    # Her mekan için döngü
    for mekan in MEKANLAR:
        print(f"\n--- {mekan['name']} işleniyor ---")

        # 1. Groq ile zenginleştir
        mekan["description"] = zenginlestir(mekan["name"], mekan["description"])

        # 2. İngilizceye çevir
        description_en = cevir(mekan["description"])

        # 3. Görsel üret ve indir
        dosya_adi = mekan["name"].lower().replace(" ", "_")
        gorsel_yolu = gorsel_uret_ve_indir(mekan["name"], dosya_adi)

        # 4. Görseli Strapi'ye yükle
        media_id = None
        if gorsel_yolu:
            media_id = gorsel_yukle(token, gorsel_yolu, dosya_adi)

        # 5. Mekanı Strapi'ye kaydet
        mekan_ekle(token, mekan, sehir_id, media_id, description_en)

    print("\n" + "=" * 50)
    print("Tüm mekanlar başarıyla yüklendi!")
    print("=" * 50)


if __name__ == "__main__":
    main()