import datetime as dt
import json
import textwrap
import typing as t
import uuid

import pandas as pd
import requests


def get_config(config_path="config.json") -> t.Dict[str, t.Any]:
    with open(config_path, "r") as file:
        config = json.load(file) | {"config_path": config_path}
        return config


def get_hour_data(filename):
    df = pd.read_excel(filename, engine="odf")

    def row_to_line_item(i, row) -> t.Dict[str, t.Any]:
        note_data = str(row["Notes"]).split(" | ")
        if len(note_data) == 1:
            name = note_data[0]
            description = ""
        elif len(note_data) == 2:
            name = note_data[0]
            description = "\n".join(textwrap.wrap(note_data[1]))
        else:
            raise ValueError(f"Bad formatting in {note_data}")
        return {
            f"items[{i}][name]": f'{row["Date"].strftime("%b %d, %Y")} - {name}',
            f"items[{i}][quantity]": f'{float(row["Hours"]):0.1f}',
            f"items[{i}][unit_cost]": f'{float(row["Rate"]):0.0f}',
            f"items[{i}][description]": description,
        }

    data = dict()
    for i, row in df.iterrows():
        if row["Billing Status"] != "BILLED":
            data |= row_to_line_item(i, row)
    return data


config = get_config()
api_key = config["invoice_generator_api_key"]

# SAM TODO: Clean this up with a config.json file or something to store this data.
# SAM TODO: Add a CLI interface for this program so that I can just store it on my
# computer and not have to worry about opening up LibreOffice Calc.
# Sam TODO: Add a better README for this repository and double-check that it's public.

# prepare data
data = dict()
data["from"] = "Samuel Morris\ndodobird181@gmail.com"
data["to"] = "Roy Group"
data["logo"] = (
    "https://github.com/dodobird181/invoicing/blob/main/assets/logo.png?raw=true"
)
data["number"] = uuid.uuid4().hex[16:].upper()
data["date"] = dt.datetime.now().strftime("%b %d, %Y")
data["due_date"] = (dt.datetime.now() + dt.timedelta(days=30)).strftime("%b %d, %Y")
data |= get_hour_data("rush_hours.ods")
data["item_header"] = "Description"
data["quantity_header"] = "Hours"

# generate the invoice
url = "https://invoice-generator.com"
headers = {"Authorization": f"Bearer {api_key}"}
response = requests.post(url, headers=headers, data=data)
if response.status_code == 200:
    print("Generated invoice successfully!")
    save_path = f'smorris-invoice-{dt.datetime.now().strftime("%Y-%m-%d")}.pdf'
    with open(save_path, "wb") as pdf_file:
        pdf_file.write(response.content)
    print(f"Saved invoice successfully at: {save_path}!")
else:
    print("Error generating invoice:", response.status_code, response.text)
