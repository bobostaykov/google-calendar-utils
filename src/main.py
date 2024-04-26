import os

from dotenv import load_dotenv
from gooey import GooeyParser, Gooey
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from src.constants import CREDENTIALS_FILE, SCOPES, CLIENT_SECRETS_FILE, ALL_CALENDARS, PRIMARY
from src.features import get_total_duration
from src.utils import get_all_calendars


@Gooey(program_name='Google Calendar Utils')
def main():
    load_dotenv()
    credentials = authenticate()
    calendars = get_all_calendars(credentials)
    calendar_choices = [ALL_CALENDARS,
                        *[(PRIMARY if calendar['id'] == os.environ.get('PRIMARY_CALENDAR_ID') else calendar['name']) for
                          calendar in calendars]]

    arg_parser = GooeyParser()

    total_events_arg_group = arg_parser.add_argument_group('Total duration for events',
                                                           description='Calculate the duration sum of the specified events.\nNote: If neither min date, nor max date are set, the current week is taken.')
    total_events_arg_group.add_argument('--min_date', help='If left empty, today is chosen', widget='DateChooser')
    total_events_arg_group.add_argument('--max_date', help='If left empty, today is chosen', widget='DateChooser')
    total_events_arg_group.add_argument('--calendar', help='In which calendar to search for events',
                                        widget='Dropdown', choices=calendar_choices, default=ALL_CALENDARS)
    total_events_arg_group.add_argument('--event_titles',
                                        help='If left empty, all events in the chosen calendar are selected. You can set multiple titles, separated by /')
    total_events_arg_group.add_argument('--show_events', help='  Show information about the selected events',
                                        widget='CheckBox', action='store_true')
    total_events_arg_group.add_argument('--title_contains',
                                        help='  Title contains search term (whole words) or is exact match',
                                        widget='CheckBox', action='store_true')

    args = arg_parser.parse_args()

    get_total_duration(credentials,
                       args.min_date,
                       args.max_date,
                       args.calendar,
                       args.event_titles,
                       args.title_contains,
                       args.show_events,
                       calendars)


def authenticate():
    """ Let user log in or use stored access/refresh tokens """

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
    return credentials


if __name__ == '__main__':
    main()
