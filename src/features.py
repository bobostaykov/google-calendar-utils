import os
from datetime import date, timedelta, datetime, timezone

from googleapiclient.discovery import build

from src.constants import PRIMARY, DATETIME_FORMAT, ALL_CALENDARS
from src.utils import get_event_duration


def get_total_duration(credentials,
                       min_date_str,
                       max_date_str,
                       calendar,
                       event_titles,
                       title_contains,
                       show_events,
                       calendars):
    """ Sums the durations of events with a given title for a given period:
    - if just min_date is specified, max_date will take the value of today
    - if just max_date is specified, min_date will take the value of today
    - if neither min_date nor max_date are specified, the current week is taken
    - if event title is not specified, all events in the given calendar are selected
    - if calendar ID is not specified, events from all calendars are selected
    - title_contains == False means the title should be an exact match """

    if min_date_str is None and max_date_str is None:
        today = date.today()
        weekday = today.weekday()
        min_date_str = today - timedelta(days=weekday)
        max_date_str = min_date_str + timedelta(days=6)
    else:
        if min_date_str is None:
            min_date_str = date.today()
        else:
            min_date_str = datetime.strptime(min_date_str, '%Y-%m-%d')
        if max_date_str is None:
            max_date_str = date.today()
        else:
            max_date_str = datetime.strptime(max_date_str, '%Y-%m-%d')
    time_zone = datetime.now(timezone.utc).astimezone().strftime('%z')
    min_datetime = min_date_str.strftime(f'%Y-%m-%dT00:00:00{time_zone}')
    max_datetime = max_date_str.strftime(f'%Y-%m-%dT23:59:59{time_zone}')

    with build('calendar', 'v3', credentials=credentials) as service:
        if calendar is not None and calendar != ALL_CALENDARS:
            if calendar == PRIMARY:
                calendar = [calendar['name'] for calendar in calendars if
                            calendar['id'] == os.environ.get('PRIMARY_CALENDAR_ID')][0]
            calendar_id = [cal['id'] for cal in calendars if cal['name'] == calendar][0]
            calendars = [{
                'id': calendar_id,
                'name': calendar,
            }]
        events = []
        titles_list = [title.strip() for title in event_titles.split('/')] if event_titles else [None]
        for calendar in calendars:
            for title in titles_list:
                events_for_calendar = service.events().list(
                    calendarId=calendar['id'],
                    timeMin=min_datetime,
                    timeMax=max_datetime,
                    singleEvents=True,
                    q=title,
                ).execute()
                filtered = filter_by_title(events_for_calendar['items'], title, title_contains)
                filtered = filter_by_start_time(filtered, min_datetime, max_datetime)
                events.extend(filtered)

    if len(events) == 0:
        print('There are no events matching the search criteria for the selected period.\n')
        return

    total_duration_seconds = sum(get_event_duration(event) for event in events)
    hours = int(total_duration_seconds // 3600)
    minutes = int(total_duration_seconds // 60 % 60)
    event_s = 'event' if len(events) == 1 else 'events'
    print(f'The total duration of the selected events is {hours}:{f"{minutes:02d}"} h ({len(events)} {event_s}).')

    if show_events:
        print(f'{event_s.capitalize()}:')
        events.sort(key=lambda event: datetime.strptime(event['start']['dateTime'], DATETIME_FORMAT))
        for event in events:
            start_date_str = datetime.strptime(event['start']['dateTime'], DATETIME_FORMAT)
            end_date_str = datetime.strptime(event['end']['dateTime'], DATETIME_FORMAT)
            if start_date_str.date() == end_date_str.date():
                date_formatted = start_date_str.strftime('%d %B %Y')
                start_formatted = start_date_str.strftime('%H:%M')
                end_formatted = end_date_str.strftime('%H:%M')
                print(f'{event["summary"]}: on {date_formatted} from {start_formatted} to {end_formatted}')
            else:
                start_formatted = start_date_str.strftime('%d %B %Y, %H:%M')
                end_formatted = end_date_str.strftime('%d %B %Y, %H:%M')
                print(f'{event["summary"]}: from {start_formatted} to {end_formatted}')
    # Empty line for readability
    print()


def filter_by_title(events, title, title_contains):
    """ Filters the events based on the title and whether the match should be exact """

    if title and not title_contains:
        filtered = [event for event in events if event['summary'].lower() == title.lower()]
    else:
        filtered = events
    return filtered


def filter_by_start_time(events, min_time_str, max_time_str):
    """ Filters the events such that the event start time is between
    `min_time` and `max_time`. Needed because the Google Calendar API
     returns the events whose start time OR end time are between the
     given min and max. """

    min_time = datetime.strptime(min_time_str, DATETIME_FORMAT)
    max_time = datetime.strptime(max_time_str, DATETIME_FORMAT)
    return [event for event in events if
            min_time <= datetime.strptime(event['start']['dateTime'], DATETIME_FORMAT) <= max_time]
