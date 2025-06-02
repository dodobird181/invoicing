import os
from datetime import timedelta
from typing import Any, Dict, List

import requests

from datatypes import ClientConfig, GeneratedInvoice, Invoice, InvoiceItem
from dateutils import app_now, filename_datetime, pretty_date, pretty_datetime
from exceptions import (
    ClientDoesNotExist,
    GsheetsReadErr,
    GsheetsWriteErr,
    PdfGenFailed,
    PdfSaveFail,
)
from settings import config


def get_client_config(clientname: str) -> ClientConfig:
    try:
        client_config = config["clients"][clientname]
    except KeyError:
        raise ClientDoesNotExist(clientname)
    return ClientConfig(
        clientname=clientname,
        invoice_to=client_config["invoice_to"],
        pdf_save_folder=client_config["save_folder"],
        due_date_days=client_config["invoice_due_date_days"],
    )


def get_unbilled_invoice_items_from_gsheets() -> List[InvoiceItem]:
    return [
        InvoiceItem(app_now(), 3, 33, "I did some stuff!"),
        InvoiceItem(app_now(), 12, 33, "I did some MORE stuff for longer!"),
    ]


def build_invoice_for_client(
    items: List[InvoiceItem],
    clientname: str,
    sender_profile_name: str,
) -> Invoice:
    client = get_client_config(clientname)
    sender_profile = config["sender_profiles"][sender_profile_name]
    due_date = app_now() + timedelta(days=client.due_date_days)
    return Invoice(
        sender_name=sender_profile["invoice_from"],
        sender_logo_url=sender_profile["invoice_logo_url"],
        recipient_name=client.invoice_to,
        items=items,
        due_date=due_date,
    )


def _get_invoice_data_for_api(invoice: Invoice) -> Dict[str, Any]:

    data = {
        "from": invoice.sender_name,
        "to": invoice.recipient_name,
        "logo": invoice.sender_logo_url,
        "date": pretty_date(app_now()),
        "due_date": pretty_date(invoice.due_date),
        "item_header": invoice.item_header,
        "quantity_header": invoice.quantity_header,
        "number": invoice.invoice_number,
    }

    itemnum = 1
    for item in invoice.items:
        # special mapping of names here for the API to generate an invoice that looks correct
        data[f"items[{itemnum}][name]"] = pretty_date(item.date)
        data[f"items[{itemnum}][quantity]"] = f"{item.hours:0.1f}"
        data[f"items[{itemnum}][unit_cost]"] = f"{item.hourly_rate:0.0f}"
        data[f"items[{itemnum}][description]"] = item.description
        itemnum += 1

    return data


def generate_pdf_data(invoice: Invoice) -> GeneratedInvoice:
    """NatuRnD
    Create a generated invoice from an invoice object (assuming the invoice generator
    API is configured properly and the device has an internet connection).
    """
    url = config["invoice_generator_url"]
    headers = {"Authorization": f"Bearer {config['invoice_generator_api_key']}"}
    invoice_data = _get_invoice_data_for_api(invoice)
    response = requests.post(url, invoice_data, headers=headers)
    if response.status_code == 200:
        return GeneratedInvoice(
            invoice=invoice,
            pdf_data=response.content,
            generated_at=app_now(),
        )
    raise PdfGenFailed(f"Status code: {response.status_code}, API msg: {response.text}")


def save_pdf_for_client(generated_invoice: GeneratedInvoice, clientname: str) -> None:
    """
    Save an invoice PDF file for a client. The client must be configured in settings.py for
    this to work. Raise `ClientDoesNotExist` when a client isn't configured and `PdfSaveFail`
    if the data-saving operation fails.
    """
    client = get_client_config(clientname)
    try:
        os.makedirs(client.pdf_save_folder, exist_ok=True)
        save_filename = filename_datetime(generated_invoice.generated_at)
        savepath = f"{client.pdf_save_folder}/{save_filename}.pdf"
        with open(savepath, "wb") as savefile:
            savefile.write(generated_invoice.pdf_data)
    except Exception as e:
        raise PdfSaveFail from e


if __name__ == "__main__":
    clientname = "NatuRnD"
    sender_profile = "sammorris"
    items = get_unbilled_invoice_items_from_gsheets()
    invoice = build_invoice_for_client(items, clientname, sender_profile)
    generated_invoice = generate_pdf_data(invoice)
    save_pdf_for_client(generated_invoice, clientname)


# # SAM TODO: Clean this up with a config.json file or something to store this data.
# # SAM TODO: Add a CLI interface for this program so that I can just store it on my
# # computer and not have to worry about opening up LibreOffice Calc.
# # Sam TODO: Add a better README for this repository and double-check that it's public.

# # prepare data
# data = dict()
# data["from"] = "Samuel Morris\ndodobird181@gmail.com"
# data["to"] = "Roy Group"
# data["logo"] = (
#     "https://github.com/dodobird181/invoicing/blob/main/assets/logo.png?raw=true"
# )
# data["number"] = uuid.uuid4().hex[16:].upper()
# data["date"] = dt.datetime.now().strftime("%b %d, %Y")
# data["due_date"] = (dt.datetime.now() + dt.timedelta(days=30)).strftime("%b %d, %Y")
# data |= get_hour_data("rush_hours.ods")
# data["item_header"] = "Description"
# data["quantity_header"] = "Hours"

# # generate the invoice
# headers = {"Authorization": f"Bearer {config['invoice_generator_api_key']}"}
# response = requests.post(config["invoice_generator_url"], headers=headers, data=data)
# if response.status_code == 200:
#     print("Generated invoice successfully!")
#     save_path = f'smorris-invoice-{dt.datetime.now().strftime("%Y-%m-%d")}.pdf'
#     with open(save_path, "wb") as pdf_file:
#         pdf_file.write(response.content)
#     print(f"Saved invoice successfully at: {save_path}!")
# else:
#     print("Error generating invoice:", response.status_code, response.text)
