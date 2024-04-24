import os
from datetime import datetime, timezone
from pprint import pprint

from dotenv import load_dotenv
from google.auth.transport import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

CLIENT_SECRETS_FILE = 'client_secrets.json'
CREDENTIALS_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/calendar']


def main(name):
    load_dotenv()
    credentials = None

    if os.path.exists(CREDENTIALS_FILE):
        credentials = Credentials.from_authorized_user_file(CREDENTIALS_FILE, SCOPES)
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            credentials = flow.run_local_server()
        with open(CREDENTIALS_FILE, 'w') as credentials_file:
            credentials_file.write(credentials.to_json())

    with build('calendar', 'v3', credentials=credentials) as service:
        now = datetime.now(timezone.utc)
        start_of_day = now.strftime('%Y-%m-%dT00:00:00Z')
        end_of_day = now.strftime('%Y-%m-%dT23:59:59Z')

        events_result = service.events().list(
            calendarId=os.environ.get('PRIMARY_CALENDAR_ID'),
            timeMin=start_of_day,
            timeMax=end_of_day,
            singleEvents=True
        ).execute()
        pprint(events_result)
        events = events_result.get('items', [])

        print(f"Today's Events ({start_of_day[:-1]}):")
        if not events:
            print("No events found.")
        else:
            for event in events:
                start_time = event['start'].get('dateTime', event['start'].get('date'))
                print(f"{start_time} - {event['summary']}")


if __name__ == '__main__':
    main('PyCharm')
