import cv2
import numpy as np
import pytesseract
from PIL import Image
import re
from typing import Dict, Any, Optional
from datetime import datetime
import io
from app.core.config import settings
from app.schemas.invoice import InvoiceCreate


class OCRService:
    @staticmethod
    def preprocess_image(image_bytes: bytes) -> np.ndarray:
        try:
            # Görüntüyü byte array'den numpy array'e dönüştür
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if image is None:
                raise ValueError("Görüntü okunamadı")

            # Gri tonlamaya dönüştür
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Gürültü azaltma
            denoised = cv2.fastNlMeansDenoising(gray)

            # Kontrast artırma
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(denoised)

            # Eşikleme
            _, binary = cv2.threshold(
                enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            return binary
        except Exception as e:
            raise ValueError(f"Görüntü ön işleme hatası: {str(e)}")

    @staticmethod
    def extract_text(image: np.ndarray) -> str:
        try:
            # NumPy array'i PIL Image'e dönüştür
            pil_image = Image.fromarray(image)

            # OCR işlemi
            text = pytesseract.image_to_string(
                pil_image, lang=settings.TESSERACT_LANG)
            if not text.strip():
                raise ValueError("Metın çıkarılamadı")
            return text
        except Exception as e:
            raise ValueError(f"OCR işlemi hatası: {str(e)}")

    @staticmethod
    def parse_date(date_str: str) -> Optional[datetime]:
        try:
            # Farklı tarih formatlarını dene
            formats = [
                "%d.%m.%Y",
                "%d/%m/%Y",
                "%Y-%m-%d",
                "%d-%m-%Y"
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            return None
        except Exception:
            return None

    @staticmethod
    def parse_invoice_data(text: str) -> InvoiceCreate:
        try:
            import re
            from collections import defaultdict
            invoice_data = InvoiceCreate(
                company_name=None,
                date=None,
                total_amount=None,
                tax_number=None,
                raw_text=text
            )

            lines = [l.strip() for l in text.split('\n') if l.strip()]
            adres_keywords = ["MAH", "CAD", "NO:", "SOK", "BLOK", "KAT",
                              "D:", "EVLER", "APT", "CD", "SK", "İŞHANI", "B.EVLER"]
            firma_keywords = ["ECZANESİ", "MARKET", "TİC.", "LTD.",
                              "A.Ş.", "ECZANESI", "BRASSERIE", "MOTORLU", "ARAÇLAR", "ŞOK"]
            vergi_keywords = ["V.D.", "VNO", "VERGİ NO",
                              "VERGI NO", "TİCARİ SİCİL", "SİCİL NO", "SİCIL NO"]
            urunler = []
            adres = None
            kdv = None
            saat = None
            fis_no = None
            telefon = None

            # Tarih ve saat regex
            date_pattern = r'(\d{2}[./-]\d{2}[./-]\d{4})'
            time_pattern = r'(\d{2}:\d{2}:\d{2})'
            fis_pattern = r'FİŞ\s*NO[:\s]*([0-9]+)|FİŞNO[:\s]*([0-9]+)|FİŞ[:\s]*([0-9]+)'
            kdv_pattern = r'(KDV|TOPKDV|TOP\.KDV|TOPLAM KDV|K.D.V)[^\d]*(\d+[.,]\d{2})'
            toplam_pattern = r'(TOPLAM|TOPLAM TUTAR|TOPLAM TUTAR:|TOPLAM:|TOPLAM\\s*TL|TOPLAM\\s*\*)[^\d]*(\d+[.,]\d{2})'
            vergi_no_pattern = r'\b(\d{10,11})\b'
            tel_pattern = r'(TEL[:\s]*[0\s]*[1-9][0-9]{9,10})'
            amount_pattern = r'(\d+[.,]\d{2})'

            # Firma adı bul
            for line in lines[:5]:
                if any(fk in line.upper() for fk in firma_keywords):
                    invoice_data.company_name = line.strip()
                    break
            if not invoice_data.company_name:
                for line in lines[:5]:
                    if line.isupper() and len(line) > 3:
                        invoice_data.company_name = line.strip()
                        break

            # Adres bul
            for i, line in enumerate(lines):
                if any(ak in line.upper() for ak in adres_keywords):
                    adres = line.strip()
                    # Adres birden fazla satır olabilir
                    if i+1 < len(lines) and any(ak in lines[i+1].upper() for ak in adres_keywords):
                        adres += ", " + lines[i+1].strip()
                    break

            # Telefon numarası bul
            for line in lines:
                tel_match = re.search(tel_pattern, line.upper())
                if tel_match:
                    telefon = tel_match.group(0)
                    break

            # Vergi no bul (sadece ilgili anahtar kelimeler ve TEL içermeyen satırlar)
            for line in lines:
                if any(vk in line.upper() for vk in vergi_keywords) and "TEL" not in line.upper():
                    match = re.search(vergi_no_pattern, line)
                    if match:
                        invoice_data.tax_number = match.group(1)
                        break
            if not invoice_data.tax_number:
                for line in lines:
                    if "TEL" not in line.upper():
                        match = re.search(vergi_no_pattern, line)
                        if match:
                            invoice_data.tax_number = match.group(1)
                            break

            # Tarih ve saat bul (önce anahtar kelimeyle, yoksa fallback)
            for line in lines:
                date_match = re.search(date_pattern, line)
                if date_match and not invoice_data.date:
                    invoice_data.date = OCRService.parse_date(
                        date_match.group(1))
                time_match = re.search(time_pattern, line)
                if time_match and not saat:
                    saat = time_match.group(1)
            # Fallback: Hiç tarih bulunamazsa, tüm satırlarda ilk uygun tarihi ara
            if not invoice_data.date:
                for line in lines:
                    date_match = re.search(date_pattern, line)
                    if date_match:
                        invoice_data.date = OCRService.parse_date(
                            date_match.group(1))
                        break

            # Fiş no bul
            for line in lines:
                fis_match = re.search(fis_pattern, line.upper())
                if fis_match:
                    fis_no = next((g for g in fis_match.groups() if g), None)
                    break

            # KDV bul
            for line in lines:
                kdv_match = re.search(kdv_pattern, line.upper())
                if kdv_match:
                    kdv = kdv_match.group(2).replace(",", ".")
                    break

            # Toplam bul (önce anahtar kelimeyle, yoksa fallback)
            for line in lines[::-1]:
                toplam_match = re.search(toplam_pattern, line.upper())
                if toplam_match:
                    try:
                        invoice_data.total_amount = float(
                            toplam_match.group(2).replace(",", "."))
                        break
                    except:
                        pass
                # Alternatif: Satırda sadece büyük bir tutar varsa
                if not invoice_data.total_amount:
                    alt_match = re.findall(amount_pattern, line)
                    if alt_match:
                        try:
                            val = float(alt_match[-1].replace(",", "."))
                            if val > 10:  # mantıklı bir toplam
                                invoice_data.total_amount = val
                                break
                        except:
                            pass
            # Fallback: Hiç toplam bulunamazsa, en büyük tutarı al
            if not invoice_data.total_amount:
                max_val = 0
                for line in lines:
                    alt_match = re.findall(amount_pattern, line)
                    for v in alt_match:
                        try:
                            val = float(v.replace(",", "."))
                            if val > max_val:
                                max_val = val
                        except:
                            pass
                if max_val > 0:
                    invoice_data.total_amount = max_val

            # Ürünler: Satırda hem harf hem rakam hem de fiyat olanlar
            for line in lines:
                if re.search(amount_pattern, line) and any(c.isalpha() for c in line):
                    urun_adet_fiyat = re.findall(
                        r'([A-ZÇĞİÖŞÜa-zçğıöşü0-9 .,-]+)[^\d]*(\d+[.,]\d{2})', line)
                    for urun, fiyat in urun_adet_fiyat:
                        urunler.append(
                            {"urun": urun.strip(), "fiyat": float(fiyat.replace(",", "."))})

            # Sonuçları raw_text'e ekle (veya InvoiceCreate modeline yeni alanlar eklenebilir)
            ek_bilgi = f"\nADRES: {adres if adres else ''}\nSAAT: {saat if saat else ''}\nFIS_NO: {fis_no if fis_no else ''}\nKDV: {kdv if kdv else ''}\nURUNLER: {urunler if urunler else ''}\nTEL: {telefon if telefon else ''}"
            invoice_data.raw_text += ek_bilgi
            return invoice_data
        except Exception as e:
            raise ValueError(f"Veri ayrıştırma hatası: {str(e)}")

    def process_invoice(self, image_bytes: bytes) -> InvoiceCreate:
        try:
            # Görüntü ön işleme
            processed_image = self.preprocess_image(image_bytes)

            # Metin çıkarma
            extracted_text = self.extract_text(processed_image)

            # Veri ayrıştırma
            invoice_data = self.parse_invoice_data(extracted_text)

            return invoice_data
        except Exception as e:
            raise ValueError(f"Fatura işleme hatası: {str(e)}")
