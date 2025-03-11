import gspread
from google.oauth2.service_account import Credentials

# Define scope for Google Sheets & Drive
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

# Load credentials from service account JSON file
creds = Credentials.from_service_account_file("google-key.json", scopes=scope)

# Authorize gspread with credentials
client = gspread.authorize(creds)

# Open the spreadsheet using its ID
sheet = client.open_by_key("1qoG8XBBKPJiAA-2r0XHNc_RfktJI1S4n3qwDtRWS1uI").sheet1

# Fetch all values from the spreadsheet
data = sheet.get_all_values()

# Print the data from the spreadsheet
for i in range(1, len(data)):  # Start from row 1 (skip headers)
    row = data[i]
    if not row:  # Stop if an emwayw pty row is encountered
        break
    print(row)  # Process row
