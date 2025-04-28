from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from app.services.ocr_service import OCRService
from app.core.database import get_db
from app.models.invoice import Invoice
from app.schemas.invoice import InvoiceResponse, InvoiceInDB
from typing import Dict, Any
from datetime import datetime

router = APIRouter()
ocr_service = OCRService()


@router.get("/extract")
async def get_extract_info():
    """
    Fatura görselinden veri çıkarma endpoint'i hakkında bilgi
    """
    return {
        "description": "Fatura veya fiş görselinden veri çıkarma servisi",
        "usage": {
            "method": "POST",
            "endpoint": "/api/v1/ocr/extract",
            "content_type": "multipart/form-data",
            "parameters": {
                "file": "Fatura/fiş görseli (JPEG veya PNG formatında)"
            }
        },
        "supported_formats": ["image/jpeg", "image/png", "image/jpg"],
        "extracted_data": {
            "company_name": "Şirket adı",
            "date": "Fatura tarihi",
            "total_amount": "Toplam tutar",
            "tax_number": "Vergi numarası",
            "raw_text": "Faturadan çıkarılan ham metin"
        },
        "example_response": {
            "success": True,
            "data": {
                "company_name": "Örnek Market A.Ş.",
                "date": "2024-03-19T00:00:00",
                "total_amount": 156.75,
                "tax_number": "1234567890",
                "raw_text": "Faturadan çıkarılan örnek metin..."
            },
            "error": None
        }
    }


@router.post("/extract", response_model=InvoiceResponse)
async def extract_invoice_data(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Fatura görselinden veri çıkarma endpoint'i
    """
    try:
        # Desteklenen dosya formatlarını kontrol et
        print(file.content_type + "          kjbkbkbkbkbkhbkh")
        if not file.content_type in ["image/jpeg", "image/png", "image/jpg"]:
            return InvoiceResponse(
                success=False,
                error="Desteklenmeyen dosya formatı. Lütfen JPEG veya PNG formatında bir görsel yükleyin."
            )

        # Dosya içeriğini oku
        contents = await file.read()

        # OCR işlemini gerçekleştir
        invoice_data = ocr_service.process_invoice(contents)

        # Veritabanına kaydet
        db_invoice = Invoice(
            company_name=invoice_data.company_name,
            date=invoice_data.date,
            total_amount=invoice_data.total_amount,
            tax_number=invoice_data.tax_number,
            raw_text=invoice_data.raw_text
        )

        db.add(db_invoice)
        db.commit()
        db.refresh(db_invoice)

        return InvoiceResponse(
            success=True,
            data=InvoiceInDB.model_validate(db_invoice)
        )

    except ValueError as e:
        return InvoiceResponse(
            success=False,
            error=str(e)
        )
    except Exception as e:
        return InvoiceResponse(
            success=False,
            error=f"Beklenmeyen bir hata oluştu: {str(e)}"
        )
