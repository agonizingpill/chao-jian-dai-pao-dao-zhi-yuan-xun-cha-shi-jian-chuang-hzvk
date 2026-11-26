from sqlalchemy import Boolean, CheckConstraint, Column, Float, ForeignKey, Integer, JSON, String, Table

from core.db import metadata


trail_notices = Table('trail_notices', metadata,
    Column('code', String(64), primary_key=True),
    Column('route', String(160), ForeignKey('trail_routes.code'), nullable=False),
    Column('begins', String(160), nullable=False),
    Column('until', String(160), nullable=False),
    Column('reason', String(160), nullable=False),
    Column('status', String(160), nullable=False),
    CheckConstraint("status IN ('封闭','已解除')"),
)
