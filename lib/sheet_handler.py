import os
import json
from lib.api_service import create_sheets_service
import googleapiclient.discovery
import googleapiclient.errors
from tkinter import messagebox


config_path = os.path.join('config.json')
with open(config_path, 'r') as f:
    config = json.load(f)

service = create_sheets_service()

# Pobierz dane z arkusza
def read_all_data():
    try:
        range_var = config['sheet_name']
        result = service.spreadsheets().values().get(
            spreadsheetId=config['spreadsheet_id'],
            range=f'{range_var}'
        ).execute()
        data = result.get('values', [])
        if data:
            headers = data[0]
            rows = data[1:]
            return headers, rows
        return None, None
    except googleapiclient.errors.HttpError as error:
        print(f'An error occurred: {error}')
        return None, None

# Filtruj dane według statusu event_accepted
def filter_data(status):
    headers, rows = read_all_data()
    if not headers or not rows:
        return []
    event_accepted_index = headers.index("event_accepted")
    if status == "Nowe":
        return [row for row in rows if len(row) <= event_accepted_index or not row[event_accepted_index]]
    elif status == "Zaakceptowane":
        return [row for row in rows if len(row) > event_accepted_index and row[event_accepted_index] == "TRUE"]
    elif status == "Odrzucone":
        return [row for row in rows if len(row) > event_accepted_index and row[event_accepted_index] == "FALSE"]
    return []

# Akceptuj wydarzenie
def update_event_status(row, row_number, event_header_index, is_accepted: bool):

    cell_value = "TRUE" if is_accepted else "FALSE"
    try:
        service.spreadsheets().values().update(
            spreadsheetId=config['spreadsheet_id'],
            range=f"{config['sheet_name']}!R{row_number+2}C{event_header_index+1}",
            valueInputOption="RAW",
            body={"values": [[cell_value]]}
        ).execute()
    except Exception as e:
        messagebox.showerror("Błąd", f"Nie udało się zaktualizować arkusza: {e}")


def delete_event_from_sheet(row_number):
    try:
        # Pobierz informacje o arkuszu, aby upewnić się, że sheet_id jest prawidłowy
        spreadsheet = service.spreadsheets().get(spreadsheetId=config['spreadsheet_id']).execute()

        # Znajdź poprawny sheet_id na podstawie nazwy arkusza
        sheet_metadata = spreadsheet.get('sheets', [])
        sheet_id = None

        for sheet in sheet_metadata:
            if sheet['properties']['title'] == config['sheet_name']:
                sheet_id = sheet['properties']['sheetId']
                break

        if sheet_id is None:
            raise ValueError(f"Nie znaleziono arkusza o nazwie {config['sheet_name']}")

        # Usunięcie wiersza w arkuszu
        service.spreadsheets().batchUpdate(
            spreadsheetId=config['spreadsheet_id'],
            body={
                "requests": [
                    {
                        "deleteDimension": {
                            "range": {
                                "sheetId": sheet_id,
                                "dimension": "ROWS",
                                "startIndex": row_number + 2,  # Indeks zaczyna się od 1
                                "endIndex": row_number + 3  # Zakres wierszy do usunięcia
                            }
                        }
                    }
                ]
            }
        ).execute()

    except Exception as e:
        messagebox.showerror("Błąd", f"Nie udało się usunąć wydarzenia: {e}")
