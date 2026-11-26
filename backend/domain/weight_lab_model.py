from sqlalchemy import Column, Float, Integer, JSON, String, Table

from core.db import metadata


# Singleton row (code == ENABLED_CODE) holding the weights estimations use.
distance_weights = Table('distance_weights', metadata,
    Column('code', String(64), primary_key=True),
    Column('phase_weight', Float, nullable=False),
    Column('duration_weight', Float, nullable=False),
    Column('neighbor_count', Float, nullable=True),
    Column('updated_by', String(160), nullable=True),
    Column('updated_at', String(160), nullable=True),
    Column('trial_code', String(64), nullable=True),
)


# One weight trial evaluation. The frozen sample payload makes interruption /
# resume and concurrent re-comparison deterministic.
weight_trials = Table('weight_trials', metadata,
    Column('code', String(64), primary_key=True),
    Column('token', String(64), nullable=True),
    Column('state', String(32), nullable=False),
    Column('proposed', JSON, nullable=False),
    Column('baseline', JSON, nullable=True),
    Column('routes', JSON, nullable=False),
    Column('sample_codes', JSON, nullable=False),
    Column('samples', JSON, nullable=True),
    Column('neighbor_k', Integer, nullable=True),
    Column('missing_routes', JSON, nullable=True),
    Column('report', JSON, nullable=True),
    Column('detail', String(500), nullable=True),
    Column('requested_by', String(160), nullable=True),
    Column('created_at', String(64), nullable=True),
    Column('finished_at', String(64), nullable=True),
)
