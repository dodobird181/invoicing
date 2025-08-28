import os
import signal
import subprocess
import textwrap
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

import requests
from google.auth.exceptions import RefreshError

from datatypes import (
    ClientConfig,
    GeneratedInvoice,
    Invoice,
    InvoiceItem,
    SenderProfile,
)
from dateutils import app_now, filename_datetime, pretty_date, pretty_datetime
from exceptions import (
    ClientDoesNotExist,
    PdfGenFailed,
    PdfSaveFail,
    SenderProfileDoesNotExist,
)
from gsheets import read_sheet_data
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
        gsheet_id=client_config["gsheet_id"],
    )


def get_sender_profile(profilename: str) -> SenderProfile:
    try:
        profile = config["sender_profiles"][profilename]
    except KeyError:
        raise SenderProfileDoesNotExist(profilename)
    return SenderProfile(
        profilename=profilename,
        invoice_from=profile["invoice_from"],
        invoice_logo_url=profile["invoice_logo_url"],
        terms=profile["terms"],
    )


def get_unbilled_invoice_items_from_gsheets(client: ClientConfig) -> List[InvoiceItem]:
    """
    Filter the client's hour tracking google sheet for unbilled invoice items and return them.
    """

    def parse_title_and_desc(item_notes: str) -> Tuple[str, str]:
        note_data = str(item_notes).split(" | ")
        if len(note_data) == 1:
            # just put everything in the description field
            title = ""
            description = note_data[0]
        elif len(note_data) == 2:
            title = note_data[0]
            description = "\n".join(textwrap.wrap(note_data[1]))
        else:
            raise ValueError(f"Bad formatting in {note_data}")
        return title, description

    data = read_sheet_data(gsheet_id=client.gsheet_id)
    unbilled = []
    for row in data:
        # a custom mapping is assumed here based on the sheet data
        if row[4] == "Not Billed" and row[0] != "":
            title, description = parse_title_and_desc(row[3])
            unbilled.append(
                InvoiceItem(
                    date=datetime.strptime(row[0], "%B %d, %Y"),
                    hours=float(row[1]),
                    hourly_rate=float(row[2]),
                    description=description,
                    title=title,
                )
            )
    return unbilled


def build_invoice_for_client(
    items: List[InvoiceItem],
    client: ClientConfig,
    profile: SenderProfile,
) -> Invoice:
    due_date = app_now() + timedelta(days=client.due_date_days)
    invoice = Invoice(
        sender_name=profile.invoice_from,
        sender_logo_url=profile.invoice_logo_url,
        recipient_name=client.invoice_to,
        items=items,
        due_date=due_date,
        terms=profile.terms,
    )
    return invoice


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

    if invoice.terms != "":
        data["terms"] = invoice.terms

    itemnum = 1
    for item in invoice.items:
        # special mapping of names here for the API to generate an invoice that looks correct
        date = pretty_date(item.date)
        name = f"{date} - {item.title}" if item.title else date
        data[f"items[{itemnum}][name]"] = name
        data[f"items[{itemnum}][quantity]"] = f"{item.hours:0.1f}"
        data[f"items[{itemnum}][unit_cost]"] = f"{item.hourly_rate:0.0f}"
        data[f"items[{itemnum}][description]"] = item.description
        itemnum += 1

    return data


def generate_pdf_data(invoice: Invoice) -> GeneratedInvoice:
    """
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


def save_pdf_for_client(
    generated_invoice: GeneratedInvoice,
    client: ClientConfig,
) -> str:
    """
    Save an invoice PDF file for a client. The client must be configured in settings.py for
    this to work. Raise `ClientDoesNotExist` when a client isn't configured and `PdfSaveFail`
    if the data-saving operation fails.
    """
    try:
        os.makedirs(client.pdf_save_folder, exist_ok=True)
        save_filename = filename_datetime(generated_invoice.generated_at)
        savepath = f"{client.pdf_save_folder}/{save_filename}.pdf"
        with open(savepath, "wb") as savefile:
            savefile.write(generated_invoice.pdf_data)
        return savepath
    except Exception as e:
        raise PdfSaveFail from e


if __name__ == "__main__":
    client = get_client_config("NatuRnD")
    profile = get_sender_profile("sammorris")
    try:
        items = get_unbilled_invoice_items_from_gsheets(client)
    except RefreshError as e:
        # sometimes the token needs to be refreshed (opens browser SSO flow)
        subprocess.run(["rm", "token.json"])
        items = get_unbilled_invoice_items_from_gsheets(client)
    invoice = build_invoice_for_client(items, client, profile)
    generated_invoice = generate_pdf_data(invoice)
    savepath = save_pdf_for_client(generated_invoice, client)
    preview = subprocess.Popen(
        ["librewolf", "--new-window", savepath],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        preexec_fn=os.setsid,
    )
    print(f"Savepath is: {savepath}")
    while True:
        keep = input("Do you want to keep this invoice? (y/n) ")
        if keep.lower().strip() == "y":
            keep = True
            break
        elif keep.lower().strip() == "n":
            keep = False
            break
        else:
            # ask again
            print("Please answer with a 'y/Y' for yes or 'n/N' for no to keep the invoice.")
            ...
    if keep == False:
        subprocess.run(["rm", savepath])
