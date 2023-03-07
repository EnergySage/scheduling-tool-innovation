"""Module: main

Boot application, authenticate user and provide all API endpoints.
"""
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from datetime import timedelta, datetime
from tempfile import NamedTemporaryFile
from .config import config

# database
from sqlalchemy.orm import Session
from .database import repo, models, schemas
from .database.database import SessionLocal, engine
models.Base.metadata.create_all(bind=engine)

# authentication
from .controller.auth import Auth
from .controller.calendar import CalDavConnector, Tools

# init app
app = FastAPI()

# allow requests from own frontend running on a different port
app.add_middleware(
  CORSMiddleware,
  allow_origins=[config('FRONTEND_URL')],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

def get_db():
  """run database session"""
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()


@app.get("/login")
def login(db: Session = Depends(get_db)):
  """endpoint to get authentication status of current user"""
  me = Auth(db).subscriber
  return me


@app.post("/me", response_model=schemas.Subscriber)
def create_me(subscriber: schemas.SubscriberBase, db: Session = Depends(get_db)):
  """endpoint to add an authenticated subscriber to db, if they doesn't exist yet"""
  if Auth(db).subscriber is None:
    raise HTTPException(status_code=401, detail="No valid authentication credentials provided")
  email_exists = repo.get_subscriber_by_email(db=db, email=subscriber.email)
  if email_exists:
    raise HTTPException(status_code=400, detail="Email already registered")
  username_exists = repo.get_subscriber_by_username(db=db, username=subscriber.username)
  if username_exists:
    raise HTTPException(status_code=400, detail="Username already registered")
  return repo.create_subscriber(db=db, subscriber=subscriber)


@app.get("/me", response_model=schemas.Subscriber)
def read_me(db: Session = Depends(get_db)):
  """endpoint to get data of authenticated subscriber from db"""
  if Auth(db).subscriber is None:
    raise HTTPException(status_code=401, detail="No valid authentication credentials provided")
  db_subscriber = repo.get_subscriber(db=db, subscriber_id=Auth(db).subscriber.id)
  if db_subscriber is None:
    raise HTTPException(status_code=404, detail="Subscriber not found")
  return db_subscriber


@app.put("/me", response_model=schemas.Subscriber)
def update_me(subscriber: schemas.SubscriberBase, db: Session = Depends(get_db)):
  """endpoint to update an authenticated subscriber"""
  if Auth(db).subscriber is None:
    raise HTTPException(status_code=401, detail="No valid authentication credentials provided")
  db_subscriber = repo.get_subscriber(db=db, subscriber_id=Auth(db).subscriber.id)
  if db_subscriber is None:
    raise HTTPException(status_code=404, detail="Subscriber not found")
  return repo.update_subscriber(db=db, subscriber=subscriber, subscriber_id=Auth(db).subscriber.id)


@app.get("/me/calendars", response_model=list[schemas.CalendarOut])
def read_my_calendars(db: Session = Depends(get_db)):
  """get all calendar connections of authenticated subscriber"""
  if Auth(db).subscriber is None:
    raise HTTPException(status_code=401, detail="No valid authentication credentials provided")
  calendars = repo.get_calendars_by_subscriber(db, subscriber_id=Auth(db).subscriber.id)
  return [schemas.CalendarOut(id=c.id, title=c.title, color=c.color) for c in calendars]


@app.get("/me/appointments", response_model=list[schemas.Appointment])
def read_my_appointments(db: Session = Depends(get_db)):
  """get all appointments of authenticated subscriber"""
  if Auth(db).subscriber is None:
    raise HTTPException(status_code=401, detail="No valid authentication credentials provided")
  appointments = repo.get_appointments_by_subscriber(db, subscriber_id=Auth(db).subscriber.id)
  return appointments


@app.post("/cal", response_model=schemas.CalendarOut)
def create_my_calendar(calendar: schemas.CalendarConnection, db: Session = Depends(get_db)):
  """endpoint to add a new calendar connection for authenticated subscriber"""
  if Auth(db).subscriber is None:
    raise HTTPException(status_code=401, detail="No valid authentication credentials provided")
  calendars = repo.get_calendars_by_subscriber(db, subscriber_id=Auth(db).subscriber.id)
  limit = repo.get_connections_limit(db=db, subscriber_id=Auth(db).subscriber.id)
  # check for connection limit
  if limit > 0 and len(calendars) >= limit:
    raise HTTPException(status_code=403, detail="Maximum number of calendar connections reached")
  cal = repo.create_subscriber_calendar(db=db, calendar=calendar, subscriber_id=Auth(db).subscriber.id)
  return schemas.CalendarOut(id=cal.id, title=cal.title, color=cal.color)


@app.get("/cal/{id}", response_model=schemas.CalendarConnectionOut)
def read_my_calendar(id: int, db: Session = Depends(get_db)):
  """endpoint to get a calendar from db"""
  if Auth(db).subscriber is None:
    raise HTTPException(status_code=401, detail="No valid authentication credentials provided")
  cal = repo.get_calendar(db, calendar_id=id)
  if cal is None:
    raise HTTPException(status_code=404, detail="Calendar not found")
  if not repo.calendar_is_owned(db, calendar_id=id, subscriber_id=Auth(db).subscriber.id):
    raise HTTPException(status_code=403, detail="Calendar not owned by subscriber")
  return schemas.CalendarConnectionOut(id=cal.id, title=cal.title, color=cal.color, url=cal.url, user=cal.user)


@app.put("/cal/{id}", response_model=schemas.CalendarOut)
def update_my_calendar(id: int, calendar: schemas.CalendarConnection, db: Session = Depends(get_db)):
  """endpoint to update an existing calendar connection for authenticated subscriber"""
  if Auth(db).subscriber is None:
    raise HTTPException(status_code=401, detail="No valid authentication credentials provided")
  if not repo.calendar_exists(db, calendar_id=id):
    raise HTTPException(status_code=404, detail="Calendar not found")
  if not repo.calendar_is_owned(db, calendar_id=id, subscriber_id=Auth(db).subscriber.id):
    raise HTTPException(status_code=403, detail="Calendar not owned by subscriber")
  cal = repo.update_subscriber_calendar(db=db, calendar=calendar, calendar_id=id)
  return schemas.CalendarOut(id=cal.id, title=cal.title, color=cal.color)


@app.delete("/cal/{id}", response_model=schemas.CalendarOut)
def delete_my_calendar(id: int, db: Session = Depends(get_db)):
  """endpoint to remove a calendar from db"""
  if Auth(db).subscriber is None:
    raise HTTPException(status_code=401, detail="No valid authentication credentials provided")
  if not repo.calendar_exists(db, calendar_id=id):
    raise HTTPException(status_code=404, detail="Calendar not found")
  if not repo.calendar_is_owned(db, calendar_id=id, subscriber_id=Auth(db).subscriber.id):
    raise HTTPException(status_code=403, detail="Calendar not owned by subscriber")
  cal = repo.delete_subscriber_calendar(db=db, calendar_id=id)
  return schemas.CalendarOut(id=cal.id, title=cal.title, color=cal.color)


@app.post("/rmt/calendars", response_model=list[schemas.CalendarConnectionOut])
def read_caldav_calendars(connection: schemas.CalendarConnection, db: Session = Depends(get_db)):
  """endpoint to get calendars from a remote CalDAV server"""
  if Auth(db).subscriber is None:
    raise HTTPException(status_code=401, detail="No valid authentication credentials provided")
  con = CalDavConnector(connection.url, connection.user, connection.password)
  return con.list_calendars()


@app.get("/rmt/cal/{id}/{start}/{end}", response_model=list[schemas.Event])
def read_caldav_events(id: int, start: str, end: str, db: Session = Depends(get_db)):
  """endpoint to get events in a given date range from a remote calendar"""
  if Auth(db).subscriber is None:
    raise HTTPException(status_code=401, detail="No valid authentication credentials provided")
  db_calendar = repo.get_calendar(db, calendar_id=id)
  if db_calendar is None:
    raise HTTPException(status_code=404, detail="Calendar not found")
  con = CalDavConnector(db_calendar.url, db_calendar.user, db_calendar.password)
  events = con.list_events(start, end)
  for e in events:
    e.calendar_title = db_calendar.title
    e.calendar_color = db_calendar.color
  return events


@app.post("/apmt", response_model=schemas.Appointment)
def create_my_calendar_appointment(a_s: schemas.AppointmentSlots, db: Session = Depends(get_db)):
  """endpoint to add a new appointment with slots for a given calendar"""
  if Auth(db).subscriber is None:
    raise HTTPException(status_code=401, detail="No valid authentication credentials provided")
  if not repo.calendar_exists(db, calendar_id=a_s.appointment.calendar_id):
    raise HTTPException(status_code=404, detail="Calendar not found")
  if not repo.calendar_is_owned(db, calendar_id=a_s.appointment.calendar_id, subscriber_id=Auth(db).subscriber.id):
    raise HTTPException(status_code=403, detail="Calendar not owned by subscriber")
  return repo.create_calendar_appointment(db=db, appointment=a_s.appointment, slots=a_s.slots)


@app.get("/apmt/{id}", response_model=schemas.Appointment)
def read_my_appointment(id: str, db: Session = Depends(get_db)):
  """endpoint to get an appointment from db by id"""
  if Auth(db).subscriber is None:
    raise HTTPException(status_code=401, detail="No valid authentication credentials provided")
  db_appointment = repo.get_appointment(db, appointment_id=id)
  if db_appointment is None:
    raise HTTPException(status_code=404, detail="Appointment not found")
  if not repo.appointment_is_owned(db, appointment_id=id, subscriber_id=Auth(db).subscriber.id):
    raise HTTPException(status_code=403, detail="Appointment not owned by subscriber")
  return db_appointment


@app.put("/apmt/{id}", response_model=schemas.Appointment)
def update_my_appointment(id: int, a_s: schemas.AppointmentSlots, db: Session = Depends(get_db)):
  """endpoint to update an existing appointment with slots"""
  if Auth(db).subscriber is None:
    raise HTTPException(status_code=401, detail="No valid authentication credentials provided")
  db_appointment = repo.get_appointment(db, appointment_id=id)
  if db_appointment is None:
    raise HTTPException(status_code=404, detail="Appointment not found")
  if not repo.appointment_is_owned(db, appointment_id=id, subscriber_id=Auth(db).subscriber.id):
    raise HTTPException(status_code=403, detail="Appointment not owned by subscriber")
  return repo.update_calendar_appointment(db=db, appointment=a_s.appointment, slots=a_s.slots, appointment_id=id)


@app.delete("/apmt/{id}", response_model=schemas.Appointment)
def delete_my_appointment(id: int, db: Session = Depends(get_db)):
  """endpoint to remove an appointment from db"""
  if Auth(db).subscriber is None:
    raise HTTPException(status_code=401, detail="No valid authentication credentials provided")
  db_appointment = repo.get_appointment(db, appointment_id=id)
  if db_appointment is None:
    raise HTTPException(status_code=404, detail="Appointment not found")
  if not repo.appointment_is_owned(db, appointment_id=id, subscriber_id=Auth(db).subscriber.id):
    raise HTTPException(status_code=403, detail="Appointment not owned by subscriber")
  return repo.delete_calendar_appointment(db=db, appointment_id=id)


@app.get("/apmt/public/{slug}", response_model=schemas.AppointmentOut)
def read_public_appointment(slug: str, db: Session = Depends(get_db)):
  """endpoint to retrieve an appointment from db via public link and only expose necessary data"""
  a = repo.get_public_appointment(db, slug=slug)
  s = repo.get_subscriber_by_appointment(db=db, appointment_id=a.id)
  if a is None or s is None:
    raise HTTPException(status_code=404, detail="Appointment not found")
  slots = [schemas.SlotOut(id=sl.id, start=sl.start, duration=sl.duration) for sl in a.slots]
  return schemas.AppointmentOut(id=a.id, title=a.title, details=a.details, slug=a.slug, owner_name=s.name, slots=slots)


@app.put("/apmt/public/{slug}", response_model=schemas.SlotAttendee)
def update_public_appointment_slot(slug: str, s_a: schemas.SlotAttendee, db: Session = Depends(get_db)):
  """endpoint to update a time slot for an appointment via public link and create an event in remote calendar"""
  db_appointment = repo.get_public_appointment(db, slug=slug)
  if db_appointment is None:
    raise HTTPException(status_code=404, detail="Appointment not found")
  db_calendar = repo.get_calendar(db, calendar_id=db_appointment.calendar_id)
  if db_calendar is None:
    raise HTTPException(status_code=404, detail="Calendar not found")
  if not repo.appointment_has_slot(db, appointment_id=db_appointment.id, slot_id=s_a.slot_id):
    raise HTTPException(status_code=404, detail="Time slot not found for Appointment")
  if not repo.slot_is_available(db, slot_id=s_a.slot_id):
    raise HTTPException(status_code=403, detail="Time slot not available anymore")
  slot = repo.get_slot(db=db, slot_id=s_a.slot_id)
  event = schemas.Event(
    title=db_appointment.title,
    start=slot.start.isoformat(),
    end=(slot.start + timedelta(minutes=slot.duration)).isoformat(),
    description=db_appointment.details
  )
  con = CalDavConnector(db_calendar.url, db_calendar.user, db_calendar.password)
  con.create_event(event=event, attendee=s_a.attendee)
  repo.update_slot(db=db, slot_id=s_a.slot_id, attendee=s_a.attendee)
  return schemas.SlotAttendee(slot_id=s_a.slot_id, attendee=s_a.attendee)


@app.get("/serve/ics/{slug}/{slot_id}", response_model=schemas.FileDownload)
def serve_ics(slug: str, slot_id: int, db: Session = Depends(get_db)):
  """endpoint to serve ICS file for time slot to download"""
  db_appointment = repo.get_public_appointment(db, slug=slug)
  if db_appointment is None:
    raise HTTPException(status_code=404, detail="Appointment not found")
  if not repo.appointment_has_slot(db, appointment_id=db_appointment.id, slot_id=slot_id):
    raise HTTPException(status_code=404, detail="Time slot not found for Appointment")
  slot = repo.get_slot(db=db, slot_id=slot_id)
  if slot is None:
    raise HTTPException(status_code=404, detail="Time slot not found")
  organizer = repo.get_subscriber_by_appointment(db=db, appointment_id=db_appointment.id)
  return schemas.FileDownload(
    name="test",
    content_type="text/calendar",
    data=Tools.create_vevent(db_appointment, slot, organizer)
  )
