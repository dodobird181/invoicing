import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from exceptions import GsheetsReadErr, GsheetsWriteErr

# scoped permission for reading and writing to gsheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def perform_local_desktop_oauth() -> Credentials:
    """
    Ripped from the google sheets API guide: https://developers.google.com/workspace/sheets/api/quickstart/python.

    TODO:   This will need to work on it's own in the future if I ever want invoices to be generated automatically
            at some regular interval.
    """

    creds = None

    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    # refresh from token file at the end again so we can get the same type (run_local_server returns a
    # slightly different credential type which is flattened when saved to token.json and then loaded again...)
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    return creds


def read_sheet_data(gsheet_id: str, range_name="Hours!A2:E"):

    try:
        creds = perform_local_desktop_oauth()
        service = build("sheets", "v4", credentials=creds)
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=gsheet_id, range=range_name).execute()
        data = result.get("values", [])

        if not data:
            raise GsheetsReadErr("No data found.")

        return data

    except HttpError as e:
        raise GsheetsReadErr from e
