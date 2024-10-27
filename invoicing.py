import json
from typing import *
from datetime import datetime
import taskw
import pathlib
import requests
import cli


def get_config(config_path="config.json") -> Dict[str, Any]:
    with open(config_path, "r") as file:
        config = json.load(file) | {"config_path": config_path}
        return config


def get_warrior() -> taskw.TaskWarriorShellout:
    curr_path = pathlib.Path(__file__).parent.resolve()
    return taskw.TaskWarrior(
        config_overrides={"data.location": f"{curr_path}/.invoicing_database"}
    )


def get_save_path(config: Dict[str, Any]) -> str:
    directory = config["invoice_out_directory"]
    filename = f'invoice_{config["runtime"]["timestamp"].strftime("%Y-%m-%d_%H:%M:%S")}'
    return f"{directory}/{filename}"


config = get_config()
warrior = get_warrior()
parsed = cli.parse(config)
client_name = parsed.client_name.replace(' ', '_').lower()
client_display_name = parsed.client_name
parsed.__delattr__('client_name')
match parsed.command:
    case 'add':
        warrior.task_add(description=str(vars(parsed)).replace('\'', '\"'), tags=[client_name])
    case 'preview':
        print(f'=== Invoice for {client_display_name} from {config["invoice_from"]} ===')
        for i, line in enumerate(warrior.filter_tasks({'tag': client_name})):
            line_data = json.loads(line['description'])
            print('{n} {desc} {hours} {rate} {extras} {time}'.format(
                n=i + 1,
                desc=line_data["task_description"],
                hours=line_data["hours_worked"],
                rate=line_data["hourly_rate"],
                extras=line_data['extra_notes'],
                time=line_data['timestamp'],
            ))
            
        



def generate(api_key, data):
    url = "https://invoice-generator.com"
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        print("Generated invoice successfully!")
        save_path = f'{config["out-dir"]}/invoice-{dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        with open(save_path, "wb") as pdf_file:
            pdf_file.write(response.content)
        print("Saved invoice successfully at: {save_path}!")
    else:
        print("Error generating invoice:", response.status_code, response.text)


def get_line_items(csv_data):
    # TODO
    return {
        "items[0][name]": "Starter plan monthly",
        "items[0][quantity]": 5,
        "items[0][unit_cost]": 55.3,
        "items[0][description]": "This took a LOT of work!",
    }


if __name__ == "__main__":
    """
    cli_args = get_cli_args()
    config = get_config()

    data = config["default-invoice"]
    data["from"] = cli_args["from"] or data["from"]
    data["to"] = cli_args["to"] or data["to"]
    data["number"] = uuid.uuid4().hex[16:].upper()
    data["date"] = dt.datetime.now().strftime("%b %d, %Y")
    data["due_date"] = (dt.datetime.now() + dt.timedelta(days=14)).strftime("%b %d, %Y")
    data |= get_line_items(None)
    generate(api_key=config["invoice-generator-api-key"], data=data)
    """
