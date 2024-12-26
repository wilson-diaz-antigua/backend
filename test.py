from pprint import pprint

from backend.services.database import engine
from backend.services.models import Stop, StopSchema
from sqlmodel import Session, select

StopSchema = StopSchema()
with Session(engine) as session:
    stops = session.exec(select(Stop)).all()
    stops = StopSchema.dump(
        stops,
        many=True,
    )

    pprint(stops[0:10])
