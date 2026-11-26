from domain.trail_routes_api import router as trail_routes
from domain.patrol_windows_api import router as patrol_windows
from domain.trail_notices_api import router as trail_notices
from domain.lead_shifts_api import router as lead_shifts

routers = (trail_routes, patrol_windows, trail_notices, lead_shifts,)
