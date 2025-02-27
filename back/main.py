from typing import Annotated, Optional, List

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select, Relationship
from datetime import datetime


# class Hero(SQLModel, table=True):
#     id: int | None = Field(default=None, primary_key=True)
#     name: str = Field(index=True)
#     age: int | None = Field(default=None, index=True)
#     secret_name: str

class Sensor(SQLModel, table=True):  # `table=True` makes this a database table
    id: Optional[int] = Field(default=None, primary_key=True)
    sensor_title: str = Field(max_length=255, nullable=False)

    # Establish relationship with SensorReading
    readings: List["SensorReading"] = Relationship(back_populates="sensor")

class SensorReading(SQLModel, table=True):  # `table=True` makes this a database table
    id: Optional[int] = Field(default=None, primary_key=True)
    sensor_id: int = Field(foreign_key="sensor.id", nullable=False)
    date_created: Optional[datetime] = Field(default=None)
    reading_value: Optional[str] = Field(max_length=255, default=None)

    # Establish relationship with Sensor
    sensor: Sensor = Relationship(back_populates="readings")

strtime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
sqlite_file_name = strtime + ".db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]

app = FastAPI()

# signals are dumped by 256 signal at a time, with 400Hz sampling rate. Count to 16 to get 4096 signals
signal_dumps_count = 0

last_annotations = []

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.post("/sensors/")
def create_sensor(sensor: Sensor, session: SessionDep) -> Sensor:
    session.add(sensor)
    session.commit()
    session.refresh(sensor)
    return sensor

@app.get("/sensors/")
def read_sensors(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[Sensor]:
    sensors = session.exec(select(Sensor).offset(offset).limit(limit)).all()
    return sensors

# use mysql documentation. write a query to add a list of sensor readings to a sensor with a given id
@app.put("/sensors/{sensor_id}")
def add_sensor_readings(sensor_id: int, readings: List[SensorReading], session: SessionDep):
    sensor = session.get(Sensor, sensor_id)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    for reading in readings:
        reading.sensor_id = sensor_id
        reading.date_created = datetime.now()
        session.add(reading)
    session.commit()
    signal_dumps_count += 1
    if signal_dumps_count == 16:
        signal_dumps_count = 0
        # process the 4096 signals
    return {"ok": True}

# use mysql documentation. write a query to get all sensor readings for a sensor with a given id
@app.get("/sensors/{sensor_id}")
def read_sensor_readings(sensor_id: int, session: SessionDep):
    sensor = session.get(Sensor, sensor_id)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    readings = session.exec(select(SensorReading).where(SensorReading.sensor_id == sensor_id)).all()
    return readings

# use mysql documentation. write a GET query to get the last 4096 samples from the sensor readings.
# Wait for the response to be ready before sending the next GET request
@app.get("/sensors/{sensor_id}/last4096")
def read_sensor_last4096(sensor_id: int, session: SessionDep):
    sensor = session.get(Sensor, sensor_id)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    readings = session.exec(select(SensorReading).where(SensorReading.sensor_id == sensor_id).order_by(SensorReading.date_created.desc()).limit(4096)).all()
    while signal_dumps_count != 0:
        pass
    return readings

# use mysql documentation. write a POST query that will update the last_annotations variable with the annotations
# that are sent in the request body
@app.post("/annotations/")
def update_annotations(annotations: str):
    last_annotations.append(annotations)
    if len(last_annotations) >= 10:
        last_annotations.pop(0)
    return {"ok": True}


# # use mysql documentation. write a get query to get the last_annotations variable
# # and return it as a response
@app.get("/annotations/")
def get_annotations():
    return last_annotations

# @app.delete("/heroes/{hero_id}")
# def delete_hero(hero_id: int, session: SessionDep):
#     hero = session.get(Hero, hero_id)
#     if not hero:
#         raise HTTPException(status_code=404, detail="Hero not found")
#     session.delete(hero)
#     session.commit()
#     return {"ok": True}