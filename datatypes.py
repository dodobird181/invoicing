from dataclasses import dataclass
from datetime import date, datetime
from typing import List
from uuid import uuid4

"""
All static datatypes used in this app.
"""


@dataclass
class InvoiceItem:
    """
    A single line-item that can appear on an invoice.
    """

    date: datetime
    hours: float
    hourly_rate: float
    description: str


@dataclass
class Invoice:
    """
    Complete data for an invoice.
    """

    sender_name: str
    sender_logo_url: str
    recipient_name: str
    items: List[InvoiceItem]
    due_date: datetime
    item_header: str = "Description"  # default item header
    quantity_header: str = "Hours"  # default quantity header (set for hourly billing)
    invoice_number: str = uuid4().hex[16:].upper()


@dataclass
class GeneratedInvoice:
    """
    A generated PDF invoice.
    """

    invoice: Invoice
    pdf_data: bytes
    generated_at: datetime


@dataclass
class ClientConfig:
    """
    A configured client to generate invoices for.
    """

    clientname: str
    invoice_to: str
    pdf_save_folder: str
    due_date_days: int
