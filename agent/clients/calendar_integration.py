"""
Calendar Integration Module
Handles Google Calendar API integration for proactive scheduling assistance
"""

import os
import pickle
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

class CalendarManager:
    """
    Manages Google Calendar integration for proactive agent
    """
    
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self, credentials_file: str = 'credentials.json', token_file: str = 'token.pickle'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self._setup_service()
    
    def _setup_service(self):
        """Set up Google Calendar API service"""
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, request authorization
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:
                    creds = None
            
            if not creds and os.path.exists(self.credentials_file):
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.SCOPES)
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    print(f"Calendar setup failed: {e}")
                    return
            
            # Save credentials
            if creds:
                with open(self.token_file, 'wb') as token:
                    pickle.dump(creds, token)
        
        if creds:
            try:
                self.service = build('calendar', 'v3', credentials=creds)
            except Exception as e:
                print(f"Failed to build calendar service: {e}")
    
    def setup_oauth(self):
        """Interactive OAuth setup for calendar access"""
        if not os.path.exists(self.credentials_file):
            raise FileNotFoundError(
                f"Please download your Google Calendar API credentials to {self.credentials_file}\n"
                "Get them from: https://console.cloud.google.com/apis/credentials"
            )
        
        # Force re-authentication
        if os.path.exists(self.token_file):
            os.remove(self.token_file)
        
        self._setup_service()
        
        if self.service:
            # Test the connection
            try:
                calendar_list = self.service.calendarList().list().execute()
                print(f"Successfully connected! Found {len(calendar_list['items'])} calendars.")
                return True
            except Exception as e:
                print(f"Calendar test failed: {e}")
                return False
        
        return False
    
    def get_upcoming_events(self, limit: int = 10, days_ahead: int = 7, all_calendars: bool = True) -> List[Dict]:
        """Get upcoming calendar events from all calendars or just primary"""
        if not self.service:
            return []
        
        try:
            # Calculate time range
            now = datetime.utcnow().isoformat() + 'Z'
            time_max = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat() + 'Z'
            
            all_events = []
            
            if all_calendars:
                # Get list of all calendars
                try:
                    calendar_list = self.service.calendarList().list().execute()
                    calendars = calendar_list.get('items', [])
                except Exception as e:
                    print(f"Error fetching calendar list: {e}")
                    calendars = [{'id': 'primary'}]  # Fallback to primary
                
                # Fetch events from each calendar
                for calendar in calendars:
                    cal_id = calendar['id']
                    try:
                        events_result = self.service.events().list(
                            calendarId=cal_id,
                            timeMin=now,
                            timeMax=time_max,
                            maxResults=limit,
                            singleEvents=True,
                            orderBy='startTime'
                        ).execute()
                        
                        events = events_result.get('items', [])
                        # Add calendar name to each event
                        for event in events:
                            event['calendar_name'] = calendar.get('summary', cal_id)
                        all_events.extend(events)
                    except Exception as e:
                        print(f"Error fetching events from calendar {cal_id}: {e}")
                        continue
                
                # Sort all events by start time
                all_events.sort(key=lambda x: x['start'].get('dateTime', x['start'].get('date')))
                events = all_events[:limit]  # Limit total results
            else:
                # Just query primary calendar
                events_result = self.service.events().list(
                    calendarId='primary',
                    timeMin=now,
                    timeMax=time_max,
                    maxResults=limit,
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                
                events = events_result.get('items', [])
            
            # Process events
            processed_events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                
                processed_event = {
                    'id': event['id'],
                    'summary': event.get('summary', 'No title'),
                    'start': start,
                    'description': event.get('description', ''),
                    'location': event.get('location', ''),
                    'attendees': len(event.get('attendees', [])),
                    'calendar_name': event.get('calendar_name', 'Primary'),
                }
                
                # Add time until event
                try:
                    if 'T' in start:  # DateTime event
                        event_time = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    else:  # All-day event
                        event_time = datetime.fromisoformat(start + 'T00:00:00')
                    
                    time_until = event_time - datetime.now(event_time.tzinfo if event_time.tzinfo else None)
                    processed_event['time_until'] = time_until
                    processed_event['is_soon'] = time_until < timedelta(hours=2)
                    processed_event['is_today'] = time_until < timedelta(days=1)
                    
                except Exception as e:
                    processed_event['time_until'] = None
                    processed_event['is_soon'] = False
                    processed_event['is_today'] = False
                
                processed_events.append(processed_event)
            
            return processed_events
            
        except Exception as e:
            print(f"Error fetching calendar events: {e}")
            return []
    
    def get_events_for_date(self, target_date: datetime, all_calendars: bool = True) -> List[Dict]:
        """Get events for a specific date from all calendars or just primary"""
        if not self.service:
            return []
        
        try:
            # Set time range for the specific date
            start_time = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = start_time + timedelta(days=1)
            
            time_min = start_time.isoformat() + 'Z'
            time_max = end_time.isoformat() + 'Z'
            
            all_events = []
            
            if all_calendars:
                # Get list of all calendars
                try:
                    calendar_list = self.service.calendarList().list().execute()
                    calendars = calendar_list.get('items', [])
                except Exception as e:
                    print(f"Error fetching calendar list: {e}")
                    calendars = [{'id': 'primary'}]
                
                # Fetch events from each calendar
                for calendar in calendars:
                    cal_id = calendar['id']
                    try:
                        events_result = self.service.events().list(
                            calendarId=cal_id,
                            timeMin=time_min,
                            timeMax=time_max,
                            singleEvents=True,
                            orderBy='startTime'
                        ).execute()
                        
                        events = events_result.get('items', [])
                        # Add calendar name to each event
                        for event in events:
                            event['calendar_name'] = calendar.get('summary', cal_id)
                        all_events.extend(events)
                    except Exception as e:
                        print(f"Error fetching events from calendar {cal_id}: {e}")
                        continue
                
                # Sort by start time
                all_events.sort(key=lambda x: x['start'].get('dateTime', x['start'].get('date')))
            else:
                # Just query primary calendar
                events_result = self.service.events().list(
                    calendarId='primary',
                    timeMin=time_min,
                    timeMax=time_max,
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                all_events = events_result.get('items', [])
            
            return self._process_events(all_events)
            
        except Exception as e:
            print(f"Error fetching events for date: {e}")
            return []
    
    def find_free_time(self, date: datetime, duration_minutes: int = 60) -> List[Dict]:
        """Find free time slots on a given date"""
        if not self.service:
            return []
        
        try:
            events = self.get_events_for_date(date)
            
            # Define working hours (9 AM to 6 PM)
            work_start = date.replace(hour=9, minute=0, second=0, microsecond=0)
            work_end = date.replace(hour=18, minute=0, second=0, microsecond=0)
            
            # Create list of busy periods
            busy_periods = []
            for event in events:
                start_str = event['start']
                if 'T' in start_str:  # Skip all-day events
                    start_time = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                    # Assume 1 hour duration if not specified
                    end_time = start_time + timedelta(hours=1)
                    busy_periods.append((start_time, end_time))
            
            # Sort busy periods
            busy_periods.sort()
            
            # Find free slots
            free_slots = []
            current_time = work_start
            
            for busy_start, busy_end in busy_periods:
                # Check if there's a free slot before this busy period
                if current_time + timedelta(minutes=duration_minutes) <= busy_start:
                    free_slots.append({
                        'start': current_time,
                        'end': busy_start,
                        'duration_minutes': int((busy_start - current_time).total_seconds() / 60)
                    })
                
                current_time = max(current_time, busy_end)
            
            # Check for free time after the last event
            if current_time + timedelta(minutes=duration_minutes) <= work_end:
                free_slots.append({
                    'start': current_time,
                    'end': work_end,
                    'duration_minutes': int((work_end - current_time).total_seconds() / 60)
                })
            
            return free_slots
            
        except Exception as e:
            print(f"Error finding free time: {e}")
            return []
    
    def get_calendar_insights(self) -> Dict:
        """Analyze calendar patterns for proactive suggestions"""
        if not self.service:
            return {}
        
        try:
            # Get events from the past week and next week
            past_week = datetime.utcnow() - timedelta(days=7)
            next_week = datetime.utcnow() + timedelta(days=7)
            
            time_min = past_week.isoformat() + 'Z'
            time_max = next_week.isoformat() + 'Z'
            
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Analyze patterns
            insights = {
                'total_events': len(events),
                'busiest_day': None,
                'average_meetings_per_day': 0,
                'most_common_meeting_time': None,
                'upcoming_busy_days': [],
                'free_time_today': []
            }
            
            # Count events by day
            events_by_day = {}
            events_by_hour = {}
            
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                if 'T' in start:
                    event_date = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    day_key = event_date.strftime('%A')
                    hour_key = event_date.hour
                    
                    events_by_day[day_key] = events_by_day.get(day_key, 0) + 1
                    events_by_hour[hour_key] = events_by_hour.get(hour_key, 0) + 1
            
            if events_by_day:
                insights['busiest_day'] = max(events_by_day, key=events_by_day.get)
                insights['average_meetings_per_day'] = sum(events_by_day.values()) / len(events_by_day)
            
            if events_by_hour:
                most_common_hour = max(events_by_hour, key=events_by_hour.get)
                insights['most_common_meeting_time'] = f"{most_common_hour}:00"
            
            # Find free time for today
            today = datetime.now()
            insights['free_time_today'] = self.find_free_time(today)
            
            return insights
            
        except Exception as e:
            print(f"Error analyzing calendar: {e}")
            return {}
    
    def _process_events(self, events: List[Dict]) -> List[Dict]:
        """Process raw calendar events into structured format"""
        processed = []
        
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            
            processed_event = {
                'id': event['id'],
                'summary': event.get('summary', 'No title'),
                'start': start,
                'description': event.get('description', ''),
                'location': event.get('location', ''),
                'attendees': len(event.get('attendees', [])),
                'is_all_day': 'T' not in start,
                'calendar_name': event.get('calendar_name', 'Primary')
            }
            
            processed.append(processed_event)
        
        return processed
    
    def suggest_meeting_times(self, duration_minutes: int = 60, days_ahead: int = 7) -> List[Dict]:
        """Suggest optimal meeting times based on calendar analysis"""
        suggestions = []
        
        for i in range(1, days_ahead + 1):
            target_date = datetime.now() + timedelta(days=i)
            
            # Skip weekends for work meetings
            if target_date.weekday() >= 5:
                continue
            
            free_slots = self.find_free_time(target_date, duration_minutes)
            
            for slot in free_slots:
                if slot['duration_minutes'] >= duration_minutes:
                    suggestions.append({
                        'date': target_date.strftime('%A, %B %d'),
                        'time': slot['start'].strftime('%I:%M %p'),
                        'duration_available': slot['duration_minutes'],
                        'confidence': self._calculate_suggestion_confidence(slot['start'])
                    })
        
        # Sort by confidence
        suggestions.sort(key=lambda x: x['confidence'], reverse=True)
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def _calculate_suggestion_confidence(self, slot_time: datetime) -> float:
        """Calculate confidence score for meeting time suggestion"""
        confidence = 0.5  # Base confidence
        
        hour = slot_time.hour
        
        # Prefer mid-morning and early afternoon
        if 9 <= hour <= 11 or 14 <= hour <= 16:
            confidence += 0.3
        elif 8 <= hour <= 9 or 11 <= hour <= 14 or 16 <= hour <= 17:
            confidence += 0.1
        
        # Prefer Tuesday through Thursday
        weekday = slot_time.weekday()
        if 1 <= weekday <= 3:  # Tue-Thu
            confidence += 0.2
        elif weekday == 0 or weekday == 4:  # Mon or Fri
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def is_available(self) -> bool:
        """Check if calendar integration is available"""
        return self.service is not None
    
    def create_event(self, summary: str, start_time: datetime, end_time: datetime, 
                    description: str = "", location: str = "", 
                    attendees: Optional[List[str]] = None) -> Optional[Dict]:
        """
        Create a new calendar event
        
        Args:
            summary: Event title
            start_time: Event start datetime
            end_time: Event end datetime
            description: Event description (optional)
            location: Event location (optional)
            attendees: List of attendee email addresses (optional)
        
        Returns:
            Created event details or None if failed
        """
        if not self.service:
            print("Calendar service not available")
            return None
        
        try:
            # Build event body
            event_body = {
                'summary': summary,
                'description': description,
                'location': location,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'UTC',
                },
            }
            
            # Add attendees if provided
            if attendees:
                event_body['attendees'] = [{'email': email} for email in attendees]
            
            # Create the event
            event = self.service.events().insert(
                calendarId='primary',
                body=event_body,
                sendUpdates='all' if attendees else 'none'
            ).execute()
            
            return {
                'id': event.get('id'),
                'summary': event.get('summary'),
                'start': event['start'].get('dateTime', event['start'].get('date')),
                'end': event['end'].get('dateTime', event['end'].get('date')),
                'htmlLink': event.get('htmlLink'),
                'status': event.get('status')
            }
            
        except Exception as e:
            print(f"Error creating calendar event: {e}")
            return None
