from fastapi import FastAPI, HTTPException, APIRouter
from database import PoppingDB, NotifyDB
from utils import run_once

@run_once
def WebApp(notifyDB : NotifyDB,pendingDB : PoppingDB):
    app = FastAPI()
    router = APIRouter(prefix="/api")

    @router.get("/notification")
    async def get_notification_sites():
        return notifyDB.get_all()
    
    @router.delete("/notification/{url:path}")
    async def delete_notification_sites(url: str):
        try:
            notifyDB.delete(url)
        except ValueError:
            raise HTTPException(status_code=404, detail="Site not found")
        return {"message": "Site deleted successfully"}
    
    @router.get("/pending")
    async def get_pending_sites():
        return pendingDB.get_all_url()

    @router.post("/pending")
    async def add_pending_sites(site: dict):
        try:
            pendingDB.post(site["url"])
        except ValueError:
            raise HTTPException(status_code=409 , detail="site already in db")
        return {"message": "Site added successfully"}

    @router.delete("/pending/{url:path}")
    async def delete_pending_sites(url: str):
        try:
            pendingDB.delete(url)
        except ValueError:
            raise HTTPException(status_code=404, detail="Site not found")
        return {"message": "Site deleted successfully"}
    

    app.include_router(router)
    return app


if __name__ == "__main__":
    from pymongo import MongoClient
    from fastapi.staticfiles import StaticFiles
    import uvicorn
    db_client = "mongodb://localhost:27017/"
    dbname = 'notification-db-test'
    client = MongoClient(db_client)  # Replace with your MongoDB connection
    database = NotifyDB(client, dbname)
    pending_db = PoppingDB(client,dbname, database)

    app = WebApp(database, pending_db)
    app.mount("/", StaticFiles(directory="static",html=True), name="static")
    uvicorn.run(app, host="localhost", port=5000)
