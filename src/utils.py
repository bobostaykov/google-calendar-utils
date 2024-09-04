import os
from datetime import datetime

from googleapiclient.discovery import build

from constants import DATETIME_FORMAT, DATETIME_FORMAT_NO_TIMEZONE


def get_all_calendars(credentials):
    """ Returns all calendars of the current user, with the primary one at the front """

    with build('calendar', 'v3', credentials=credentials) as service:
        calendars = service.calendarList().list().execute()['items']
        calendars.sort(key=lambda calendar: calendar['id'] != os.environ.get('PRIMARY_CALENDAR_ID'))
        return [{
            'id': calendar['id'],
            'name': calendar['summary']
        } for calendar in calendars if calendar['accessRole'] == 'owner']


def get_event_duration(event):
    """ Finds the duration of the event in seconds """

    if 'dateTime' in event['start'] and 'dateTime' in event['end']:
        start = datetime.strptime(event['start']['dateTime'], DATETIME_FORMAT)
        end = datetime.strptime(event['end']['dateTime'], DATETIME_FORMAT)
    elif 'date' in event['start'] and 'date' in event['end']:
        start = datetime.strptime(f'{event["start"]["date"]}T00:00:00', DATETIME_FORMAT_NO_TIMEZONE)
        end = datetime.strptime(f'{event["end"]["date"]}T23:59:59', DATETIME_FORMAT_NO_TIMEZONE)
    else:
        return 0
    duration = end - start
    return duration.total_seconds()
