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
            # Fatura verilerini tutacak sözlük
            invoice_data = InvoiceCreate(
                company_name=None,
                date=None,
                total_amount=None,
                tax_number=None,
                raw_text=text
            )

            lines = text.split('\n')

            # Tarih formatı regex
            date_pattern = r'\d{2}[/.]\d{2}[/.]\d{4}'

            # Vergi numarası formatı regex
            tax_pattern = r'VKN?:?\s*(\d{10})'

            # Para miktarı formatı regex
            amount_pattern = r'(?:TOPLAM|TOP\.|TUTAR)?\s*(?:TL)?\s*([\d,.]+)\s*(?:TL)?'

            for line in lines:
                # Tarih arama
                date_match = re.search(date_pattern, line)
                if date_match and not invoice_data.date:
                    date_str = date_match.group()
                    invoice_data.date = OCRService.parse_date(date_str)

                # Vergi numarası arama
                tax_match = re.search(tax_pattern, line)
                if tax_match and not invoice_data.tax_number:
                    invoice_data.tax_number = tax_match.group(1)

                # Toplam tutar arama
                amount_match = re.search(amount_pattern, line)
                if amount_match and not invoice_data.total_amount:
                    amount_str = amount_match.group(
                        1).replace(".", "").replace(",", ".")
                    try:
                        invoice_data.total_amount = float(amount_str)
                    except ValueError:
                        pass

                # Şirket adı için ilk satırları kontrol et
                if not invoice_data.company_name and len(line.strip()) > 3:
                    invoice_data.company_name = line.strip()

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
 