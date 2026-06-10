import streamlit as st
import requests

STRAPI_URL = "http://localhost:1337"

# -------------------------
# Sayfa ayarları
# -------------------------
st.set_page_config(
    page_title="Mısır Gezi Rehberi",
    page_icon="🏛️",
    layout="wide"
)

st.title("🏛️ Mısır Gezi Rehberi")
st.markdown("---")

# -------------------------
# Şehirleri çek
# -------------------------
def sehirleri_getir():
    """Strapi'den şehir listesini çeker."""
    adres = f"{STRAPI_URL}/api/sehirlers"
    yanit = requests.get(adres)
    if yanit.status_code == 200:
        return yanit.json()["data"]
    return []

# -------------------------
# Mekanları çek
# -------------------------
def mekanlari_getir(sehir_id):
    """Seçilen şehre ait mekanları çeker."""
    # populate=* kullanarak hem kapak görselini hem de sehir ilişkisini eksiksiz çekiyoruz.
    # Eğer Strapi'de ilişki adını küçük harfle 'sehir' değil de 'sehirler' yaptıysan, 
    # aşağıdaki 'filters[sehir]' kısmını 'filters[sehirler]' olarak değiştirebilirsin.
    adres = f"{STRAPI_URL}/api/mekanlars?filters[sehirler][id][$eq]={sehir_id}&populate=*"
    yanit = requests.get(adres)
    if yanit.status_code == 200:
        return yanit.json()["data"]
    return []

# -------------------------
# Şehir seçimi
# -------------------------
sehirler = sehirleri_getir()

if not sehirler:
    st.error("Strapi'den şehir verisi alınamadı. Strapi çalışıyor mu?")
else:
    # DÜZELTME: Anahtarı 'id' yaparak 'Mısır' yazan şehirlerin birbirini ezmesini engelledik.
    # Strapi'deki büyük 'Ad' alanını güvenli bir şekilde çekiyoruz.
    sehir_isimleri = {s["id"]: s.get("Ad") or s.get("ad") or "İsimsiz Şehir" for s in sehirler}
    
    secilen_id = st.selectbox(
        "Bir şehir seçin:",
        options=list(sehir_isimleri.keys()),
        format_func=lambda x: sehir_isimleri[x]
    )

    # Dil seçimi
    dil = st.radio("Dil / Language:", ["Türkçe", "English"], horizontal=True)

    st.markdown("---")

    # -------------------------
    # Mekanları listele
    # -------------------------
    mekanlar = mekanlari_getir(secilen_id)

    if not mekanlar:
        st.warning("Bu şehre ait mekan bulunamadı.")
    else:
        st.subheader(f"📍 {sehir_isimleri[secilen_id]} - Gezilecek Yerler")
        
        # 3 sütunlu kart düzeni
        sutunlar = st.columns(3)
        
        for index, mekan in enumerate(mekanlar):
            with sutunlar[index % 3]:
                # Görsel işleme
                kapak = mekan.get("kapak")
                if kapak and kapak.get("url"):
                    gorsel_url = f"{STRAPI_URL}{kapak['url']}"
                    st.image(gorsel_url, use_container_width=True)
                else:
                    st.image("https://via.placeholder.com/400x300?text=Gorsel+Yok", use_container_width=True)

                # Mekan adı (Strapi field ismine göre küçük 'ad' veya büyük 'Ad')
                mekan_adi = mekan.get("ad") or mekan.get("Ad") or "İsimsiz Mekan"
                st.markdown(f"### {mekan_adi}")

                # Açıklama (dile göre)
                if dil == "Türkçe":
                    st.write(mekan.get("aciklama") or mekan.get("Aciklama") or "Açıklama yok.")
                else:
                    st.write(mekan.get("aciklama_en") or mekan.get("Aciklama_en") or "No description available.")

                st.markdown("---")