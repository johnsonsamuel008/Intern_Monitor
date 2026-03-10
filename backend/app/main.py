from fastapi import FastAPI

# Import routers directly from the 'routers' package
from app.routers import admin, auth, devices, intern_dashboard, activity, tasks

app = FastAPI(title="Intern Activity Monitoring System")

# Include routers
app.include_router(auth.router)
app.include_router(admin.router)       # Contains user/pairing logic
app.include_router(intern_dashboard.router)  # Contains intern/supervisor views
app.include_router(devices.router)     # Device registration
app.include_router(activity.router)    # Log ingestion/viewing
app.include_router(tasks.router)       # Task management
