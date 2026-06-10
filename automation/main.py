import os
import requests
from dotenv import load_dotenv
from deep_translator import GoogleTranslator
from groq import Groq

# -------------------------
# ENV
# -------------------------
load_dotenv()

GroqApiKey = os.getenv("GROQ_API_KEY")
StrapiUrl = os.getenv("STRAPI_URL")
Token = os.getenv("TOKEN")

# -------------------------
# VERİLER - 2 ŞEHİR
# -------------------------
Sehirler = [
    {
        "Ad": "Kahire",
        "Ulke": "Mısır",
        "Aciklama": "Mısır'ın başkenti ve Afrika'nın en kalabalık şehri.",
        "Mekanlar": [
            {"Ad": "Giza Piramitleri", "Aciklama": "Dünyanın yedi harikasından biri olan Giza Piramitleri, MÖ 2560 yılında inşa edilmiştir."},
            {"Ad": "Sfenks", "Aciklama": "Giza ovasında bulunan dev taş heykel, aslan gövdeli ve insan yüzlüdür."},
            {"Ad": "Mısır Müzesi", "Aciklama": "Kahire'nin kalbinde yer alan müze, 120.000'den fazla tarihi esere ev sahipliği yapar."},
        ]
    },
    {
        "Ad": "Luksor",
        "Ulke": "Mısır",
        "Aciklama": "Antik Mısır'ın açık hava müzesi olarak bilinen tarihi şehir.",
        "Mekanlar": [
            {"Ad": "Karnak Tapınağı", "Aciklama": "Antik Mısır'ın en büyük dini yapı kompleksi."},
            {"Ad": "Luksor Tapınağı", "Aciklama": "Nil kıyısında yer alan, MÖ 1400 yıllarına tarihlenen görkemli tapınak."},
            {"Ad": "Kraliçeler Vadisi", "Aciklama": "Antik Mısır kraliçe ve prenseslerinin gömüldüğü tarihi vadi."},
        ]
    }
]


# -------------------------
# GROQ
# -------------------------
def Zenginlestir(MekanAd, Aciklama):
    print(f"  → Groq ile zenginleştiriliyor: {MekanAd}")
    Istemci = Groq(api_key=GroqApiKey)
    Istek = f"""
Sen bir Mısır turizm uzmanısın.
Mekan: {MekanAd}
Bilgi: {Aciklama}
Türkçe, max 3 cümle yaz.
"""
    Yanit = Istemci.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": Istek}],
        max_tokens=300
    )
    return Yanit.choices[0].message.content.strip()


# -------------------------
# ÇEVİRİ
# -------------------------
def Cevir(Metin):
    print("  → İngilizceye çevriliyor...")
    return GoogleTranslator(source='tr', target='en').translate(Metin)


# -------------------------
# GÖRSEL
# -------------------------
def GorselUret(MekanAd, DosyaAdi):
    print(f"  → Görsel üretiliyor: {MekanAd}")
    IstekMetni = f"Touristic photo of {MekanAd}, Egypt, ancient architecture"
    Kodlanmis = requests.utils.quote(IstekMetni)
    Adres = f"https://image.pollinations.ai/prompt/{Kodlanmis}?width=800&height=600&nologo=true"
    Yanit = requests.get(Adres, timeout=120)
    if Yanit.status_code == 200:
        os.makedirs("gorseller", exist_ok=True)
        DosyaYolu = f"gorseller/{DosyaAdi}.jpg"
        with open(DosyaYolu, "wb") as Dosya:
            Dosya.write(Yanit.content)
        print(f"  → Görsel kaydedildi: {DosyaYolu}")
        return DosyaYolu
    else:
        print("  → Görsel üretilemedi!")
        return None


# -------------------------
# ŞEHİR EKLE
# -------------------------
def SehirEkle(Token, Ad, Ulke, Aciklama):
    print(f"Şehir ekleniyor: {Ad}")
    Adres = f"{StrapiUrl}/api/sehirlers"
    Basliklar = {"Authorization": f"Bearer {Token}"}
    Veri = {"data": {"Ad": Ad, "Ulke": Ulke, "Aciklama": Aciklama}}
    Yanit = requests.post(Adres, json=Veri, headers=Basliklar)
    if Yanit.status_code in [200, 201]:
        SehirId = Yanit.json()["data"]["id"]
        print(f"  → Şehir eklendi ID: {SehirId}")
        return SehirId
    else:
        print(f"  → Hata: {Yanit.text}")
        return None


# -------------------------
# GÖRSEL YÜKLE
# -------------------------
def GorselYukle(Token, DosyaYolu, DosyaAdi):
    print("  → Görsel Strapi'ye yükleniyor...")
    Adres = f"{StrapiUrl}/api/upload"
    Basliklar = {"Authorization": f"Bearer {Token}"}
    with open(DosyaYolu, "rb") as Dosya:
        Dosyalar = {"files": (f"{DosyaAdi}.jpg", Dosya, "image/jpeg")}
        Yanit = requests.post(Adres, headers=Basliklar, files=Dosyalar)
    if Yanit.status_code in [200, 201]:
        MedyaId = Yanit.json()[0]["id"]
        print(f"  → Görsel yüklendi. Medya ID: {MedyaId}")
        return MedyaId
    else:
        print(f"  → Görsel yüklenemedi: {Yanit.text}")
        return None


# -------------------------
# MEKAN EKLE
# -------------------------
def MekanEkle(Token, Mekan, SehirId, MedyaId, AciklamaEn):
    print(f"  → Mekan ekleniyor: {Mekan['Ad']}")
    Adres = f"{StrapiUrl}/api/mekanlars"
    Basliklar = {"Authorization": f"Bearer {Token}"}
    Veri = {
        "data": {
            "Ad": Mekan["Ad"],
            "Aciklama": Mekan["Aciklama"],
            "Aciklama_en": AciklamaEn,
            "Sehir": SehirId,
            "Kapak": MedyaId
        }
    }
    Yanit = requests.post(Adres, json=Veri, headers=Basliklar)
    if Yanit.status_code in [200, 201]:
        print("  → Mekan eklendi!")
    else:
        print(f"  → Hata: {Yanit.text}")


# -------------------------
# ANA PROGRAM
# -------------------------
def Main():
    print("=" * 50)
    print("MISIR GEZI REHBERI BASLIYOR")
    print("=" * 50)

    for Sehir in Sehirler:
        SehirId = SehirEkle(Token, Sehir["Ad"], Sehir["Ulke"], Sehir["Aciklama"])
        if not SehirId:
            print(f"{Sehir['Ad']} eklenemedi, sonraki şehre geçiliyor.")
            continue

        for Mekan in Sehir["Mekanlar"]:
            print(f"\n--- {Mekan['Ad']} ---")
            Mekan["Aciklama"] = Zenginlestir(Mekan["Ad"], Mekan["Aciklama"])
            AciklamaEn = Cevir(Mekan["Aciklama"])
            DosyaAdi = Mekan["Ad"].lower().replace(" ", "_")
            GorselYolu = GorselUret(Mekan["Ad"], DosyaAdi)
            MedyaId = None
            if GorselYolu:
                MedyaId = GorselYukle(Token, GorselYolu, DosyaAdi)
            MekanEkle(Token, Mekan, SehirId, MedyaId, AciklamaEn)

    print("\n" + "=" * 50)
    print("TAMAMLANDI!")
    print("=" * 50)


if __name__ == "__main__":
    Main()