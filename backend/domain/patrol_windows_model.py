from sqlalchemy import Boolean, CheckConstraint, Column, Float, ForeignKey, Integer, JSON, String, Table

from core.db import metadata


patrol_windows = Table('patrol_windows', metadata,
    Column('code', String(64), primary_key=True),
    Column('route', String(160), ForeignKey('trail_routes.code'), nullable=False),
    Column('opens', String(160), nullable=False),
    Column('closes', String(160), nullable=False),
    Column('opening_minute', Integer, nullable=False),
    Column('minutes', Integer, nullable=False),
    Column('phase', String(160), nullable=False),
    Column('tag', String(160), nullable=False),
    CheckConstraint('minutes BETWEEN 10 AND 180'),
    CheckConstraint('opening_minute BETWEEN 0 AND 1439'),
)
