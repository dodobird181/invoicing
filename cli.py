import argparse
from typing import *
from datetime import datetime
import dataclasses


@dataclasses.dataclass
class AddCommand:
    client_name: str
    task_description: str
    extra_notes: str
    hours_worked: float
    hourly_rate: float
    timestamp: datetime


def get_client(config: Dict[str, Any]) -> Dict[str, Any]:
    clients = config['clients']
    if len(clients) == 0:
        raise ValueError(f"Please specify a client in {config['config_path']}.")
    client_name = config['default_client'] if len(clients) > 1 else [name for name in clients.keys()][0]
    return clients[client_name] | {'name': client_name}
    

def parse(config: Dict[str, Any]):
    
    # main parser
    parser = argparse.ArgumentParser(
        description=(
            "A small program to help people keep track of the work they do, "
            + "and generate invoices for their clients automatically."
        )
    )
    client = get_client(config)
    parser.add_argument('--client_name', required=False, default=client["name"], help=(
        f"The name of the client you created in {config['config_path']}. If you only have " + 
        f'one client, it will default to them. Otherwise, the default client from your config will be used.'
    ))
    subparsers = parser.add_subparsers(dest="command", required=True)

    # list command
    preview = subparsers.add_parser('preview', help="Preview your invoice.")

    # add command
    add_parser = subparsers.add_parser("add", help="Add an item to your invoice.")
    add_parser.add_argument(
        "hours_worked",
        type=int,
        help="The number of hours you worked.",
    )
    add_parser.add_argument(
        "task_description",
        type=str,
        help="A description of what you did.",
    )
    add_parser.add_argument(
        "--extra-notes",
        required=False,
        default="",
        type=str,
        help="Any extra notes to be displayed underneath the description.",
    )
    add_parser.add_argument(
        "--hourly-rate",
        required=False,
        default=client['hourly_rate'],
        type=str,
        help=(
            f"Your hourly rate ({client['hourly_rate']} by default "
            + f"from the config file {config['config_path']}.)"
        ),
    )
    add_parser.add_argument(
        "--timestamp",
        required=False,
        default=datetime.now(),
        type=datetime.fromisoformat,
        help="The timestamp to add to this item (defaults to the current date).",
    )
    return parser.parse_args()
