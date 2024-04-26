import os
from datetime import datetime

from googleapiclient.discovery import build

from src.constants import DATETIME_FORMAT


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

    start = datetime.strptime(event['start']['dateTime'], DATETIME_FORMAT)
    end = datetime.strptime(event['end']['dateTime'], DATETIME_FORMAT)
    duration = end - start
    return duration.total_seconds()
