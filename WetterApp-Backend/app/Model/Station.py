from app.Repository.DbContext import dbcontext

class Station(dbcontext.Model):
    __tablename__ = 'station'
    
    id = dbcontext.Column(dbcontext.Integer, primary_key=True)
    # DWD Station-IDs sind in der Regel 5-stellige Zahlen, String(10) ist sicher.
    station_id = dbcontext.Column(dbcontext.String(10), unique=True, nullable=False)

    name = dbcontext.Column(dbcontext.String(80), nullable=False, index=True)
    state = dbcontext.Column(dbcontext.String(60))
    height = dbcontext.Column(dbcontext.Integer)      # Stationshöhe (m über NN)
    latitude = dbcontext.Column(dbcontext.Float)
    longitude = dbcontext.Column(dbcontext.Float)
    # Zeitraum, in dem die Station Messwerte liefert.
    active_from = dbcontext.Column(dbcontext.Date)
    active_to = dbcontext.Column(dbcontext.Date)

    # Optional: Macht es später in Python einfacher, auf die Messungen einer Station zuzugreifen
    measurements = dbcontext.relationship('DailyMeasurement', backref='station_rel', lazy=True)