from dataclasses import dataclass
from datetime import datetime
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

    # optional title which appears next to the date in bold
    title: str | None = None


@dataclass
class Invoice:
    """
    The data we need prior to generating an invoice.
    """

    sender_name: str
    sender_logo_url: str
    recipient_name: str
    items: List[InvoiceItem]
    due_date: datetime
    item_header: str = "Description"  # default item header
    quantity_header: str = "Hours"  # default quantity header (set for hourly billing)
    invoice_number: str = uuid4().hex[16:].upper()
    terms: str = ""  # default terms are empty


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

    # number of days after the invoice generation date that the invoice will say it's due
    due_date_days: int

    # the google sheet ID to keep track of your hours, see exmaple sheet here:
    # https://docs.google.com/spreadsheets/d/119i_TgxH7HClOA-ZGKgXn9koN8eZDN9yHTTyrMUpH-8/edit?usp=sharing.
    gsheet_id: str


@dataclass
class SenderProfile:
    """
    A configured sender profile to generate invoices from.
    """

    profilename: str
    invoice_from: str
    invoice_logo_url: str
    terms: str
