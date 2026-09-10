from app.Repository.DbContext import dbcontext

class DailyMeasurement(dbcontext.Model):
    __tablename__ = 'daily_measurement'
    
    id = dbcontext.Column(dbcontext.Integer, primary_key=True)
    station_id = dbcontext.Column(dbcontext.String(10), dbcontext.ForeignKey('station.station_id'), nullable=False)
    date = dbcontext.Column(dbcontext.Date, nullable=False)
    
    # --- Qualitätsniveaus (Flags) ---
    qn3 = dbcontext.Column(dbcontext.Integer) # Qualität Winddaten
    qn4 = dbcontext.Column(dbcontext.Integer) # Qualität restliche Daten
    
    # --- Wind ---
    fx = dbcontext.Column(dbcontext.Float)    # Windspitze (m/s)
    fm = dbcontext.Column(dbcontext.Float)    # Tagesmittel Wind (m/s)
    
    # --- Niederschlag ---
    rsk = dbcontext.Column(dbcontext.Float)   # Niederschlagshöhe (mm)
    rskf = dbcontext.Column(dbcontext.Integer)# Niederschlagsform (z.B. 4=Schnee, 6=Regen)
    shk_tag = dbcontext.Column(dbcontext.Integer) # Schneehöhe (cm)
    
    # --- Sonne & Wolken ---
    sdk = dbcontext.Column(dbcontext.Float)   # Sonnenscheindauer (Stunden)
    nm = dbcontext.Column(dbcontext.Float)    # Bedeckungsgrad (in 1/8)
    
    # --- Luftdruck & Feuchte ---
    vpm = dbcontext.Column(dbcontext.Float)   # Dampfdruck (hPa)
    pm = dbcontext.Column(dbcontext.Float)    # Luftdruck (hPa)
    upm = dbcontext.Column(dbcontext.Float)   # Relative Feuchtigkeit (%)
    
    # --- Temperaturen ---
    tmk = dbcontext.Column(dbcontext.Float)   # Tagesmittel (°C)
    txk = dbcontext.Column(dbcontext.Float)   # Tagesmaximum (°C)
    tnk = dbcontext.Column(dbcontext.Float)   # Tagesminimum (°C)
    tgk = dbcontext.Column(dbcontext.Float)   # Minimum 5cm über Erdboden (°C)

    # Verhindert Duplikate beim Import (Upsert-Vorbereitung)
    __table_args__ = (
        dbcontext.UniqueConstraint('station_id', 'date', name='_station_date_uc'),
    )