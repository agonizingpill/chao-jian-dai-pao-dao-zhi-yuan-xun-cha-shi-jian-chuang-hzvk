from sqlalchemy import Boolean, CheckConstraint, Column, Float, ForeignKey, Integer, JSON, String, Table

from core.db import metadata


lead_shifts = Table('lead_shifts', metadata,
    Column('code', String(64), primary_key=True),
    Column('window', String(160), ForeignKey('patrol_windows.code'), nullable=False),
    Column('lead', String(160), nullable=False),
    Column('contact', String(160), nullable=False),
    Column('on_site', String(160), nullable=True),
    Column('checkpoint', String(160), nullable=True),
    Column('state', String(160), nullable=False),
    CheckConstraint("state IN ('已领班','已签到','已交回')"),
)
