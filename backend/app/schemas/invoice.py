from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class InvoiceBase(BaseModel):
    company_name: Optional[str] = None
    date: Optional[datetime] = None
    total_amount: Optional[float] = None
    tax_number: Optional[str] = None
    raw_text: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    pass


class InvoiceInDB(InvoiceBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InvoiceResponse(BaseModel):
    success: bool
    data: Optional[InvoiceInDB] = None
    error: Optional[str] = None
 