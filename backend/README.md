# IDS (Invoice Detection System) - Backend API

Bu proje, fatura ve fiş görsellerinden veri çıkarma ve işleme yapan bir REST API'dir.

## Özellikler

- Fatura/fiş görsellerinden OCR ile veri çıkarma
- Çıkarılan verileri yapılandırılmış JSON formatına dönüştürme
- Kullanıcı kimlik doğrulama ve yetkilendirme
- Fatura verilerini veritabanında saklama
- RESTful API endpoints

## Kurulum

1. Python sanal ortamını aktifleştirin:
```bash
source venv/bin/activate  # Unix/macOS
.\venv\Scripts\activate  # Windows
```

2. Gerekli paketleri yükleyin:
```bash
pip install -r requirements.txt
```

3. .env dosyasını düzenleyin:
```bash
cp .env.example .env
# .env dosyasını düzenleyin
```

4. Veritabanı migrasyonlarını çalıştırın:
```bash
alembic upgrade head
```

5. API'yi başlatın:
```bash
uvicorn main:app --reload
```

## API Dokümantasyonu

API çalıştıktan sonra aşağıdaki URL'lerden dokümantasyona erişebilirsiniz:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
