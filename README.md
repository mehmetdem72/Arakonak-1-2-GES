# ⚡ ARAKONAK GES — Kontrol Panosu (v3)

Streamlit tabanlı, kurumsal EPC ilerleme & bütçe kontrol panosu.
GES-1 + GES-2 + ORTAK, **197 iş kalemi**. Kazanılmış Değer (EVM) hesapları,
düzenlenebilir tablolar, S-eğrisi, Excel/PDF çıktı, kullanıcı girişi ve yedekleme.

---

## Yenilikler (v2 → v3)

| Alan | v2 | v3 |
|---|---|---|
| Giriş | yok | **Kullanıcı adı/parola + rol (admin/görüntüleyici)**, PBKDF2 hash |
| Logo | yok | **ANAS logosu** başlıkta + arka planda filigran + PDF'de vektörel |
| Hesap | temel SPI | **Tam EVM**: PV, EV, AC, SV, SPI, CV, CPI, EAC, ETC, VAC, TCPI |
| Grafik | 4 adet | **9+ grafik**: gauge, S-eğrisi, treemap, waterfall, Pareto, ısı… |
| Çıktı | yok | **Excel (7 sayfa) + PDF (logolu yönetici raporu)** indirme |
| Kalıcılık | sadece oturum | **SQLite** + CSV/Excel yedek-geri yükleme |
| Stok/İSG | salt-okunur | **düzenlenebilir** + stok akış grafiği |
| Ayarlar | yok | proje adı/konum/tarih + **parola hash üreteci** |

---

## Yerelde çalıştırma

```bash
pip install -r requirements.txt
streamlit run app.py
```

Varsayılan test hesapları (**dağıtımdan önce mutlaka değiştirin**):
- `admin` / `arakonak2025`  → düzenleyebilir
- `viewer` / `viewer2025`   → salt görüntüler

## Streamlit Community Cloud'da yayınlama

1. Bu klasörü bir GitHub reposuna yükleyin.
2. share.streamlit.io → **Create app** → repo → Main file: `app.py` → Deploy.
3. **Settings → Secrets** alanına `.streamlit/secrets.toml.example` içeriğini
   kendi hesaplarınızla doldurup yapıştırın. Parola hash'lerini uygulamadaki
   **Ayarlar** sekmesindeki üreteçle oluşturun.

---

## ⚠️ Dürüst sınırlar — lütfen okuyun

Bu araç ne yapar, ne yapmaz açıkça:

1. **Kalıcı veri:** SQLite oturumlar/sekmeler arası çalışır; **yerelde tam kalıcıdır.**
   Ancak **Streamlit Community Cloud deposu geçicidir** — uygulama uykuya dalıp
   yeniden başlarsa DB sıfırlanabilir. Bu yüzden **'Veri' sekmesinden düzenli CSV/Excel
   yedeği alın**; gerçek yedeğiniz odur. Kalıcı bulut için harici bir veritabanına
   (Postgres/Supabase) bağlanmak gerekir (kod buna hazırdır ama bu pakete dahil değildir).

2. **Giriş güvenliği:** PBKDF2 hash + rol içeren bir **uygulama kapısıdır.**
   Kurumsal SSO/SAML/2FA **değildir.** Çok hassas veriyi genel internette tek başına
   buna emanet etmeyin.

3. **Maliyet göstergeleri (CPI/EAC/VAC…):** yalnızca **'Fiili Maliyet ($)'** sütununu
   doldurduğunuzda hesaplanır. Girmezseniz "veri yok" yazar — **uydurma sayı gösterilmez.**

4. **S-eğrisi:** Poz-poz zaman planı verisi olmadığından **plan baseline'ı, proje
   başlangıç/bitiş tarihlerinden MODELLENİR** (yaklaşık S dağılımı). **Gerçek** eğri,
   siz periyodik olarak "anlık görüntü" aldıkça oluşur — zamanla gerçek tarihçe birikir.

5. **Rakamların doğruluğu:** tüm bütçe/miktar/birim fiyatlar sizin `seed_data.py`
   verinizden gelir; olduğu gibi kullanılır, doğruluğu tarafımızca denetlenmez.

---

## Dosya yapısı

```
app.py         → arayüz (giriş, sekmeler, düzenleme, indirme)
core.py        → hesap motoru + EVM (Streamlit'ten bağımsız, test edilebilir)
charts.py      → Plotly grafik kütüphanesi
exports.py     → Excel + PDF üretimi (Türkçe font + vektör logo)
auth.py        → giriş / rol yönetimi (bcrypt)
storage.py     → SQLite kalıcılık + anlık görüntüler
seed_data.py   → 197 iş kalemi + stok + İSG tohum verisi
assets/        → logo.svg + Türkçe PDF fontları
.streamlit/    → tema + secrets örneği
```
