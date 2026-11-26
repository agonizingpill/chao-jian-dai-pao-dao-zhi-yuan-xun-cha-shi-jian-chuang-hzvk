from sqlalchemy import Boolean, CheckConstraint, Column, Float, ForeignKey, Integer, JSON, String, Table

from core.db import metadata


trail_routes = Table('trail_routes', metadata,
    Column('code', String(64), primary_key=True),
    Column('name', String(160), nullable=False),
    Column('checkpoint', String(160), nullable=False, unique=True),
    Column('max_leads', Integer, nullable=False),
    Column('active', Boolean, nullable=False),
    CheckConstraint('max_leads BETWEEN 1 AND 8'),
)
