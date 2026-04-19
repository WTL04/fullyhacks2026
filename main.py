from fastapi import FastAPI

app = FastAPI(title="fullypack_fastapi")


@app.get("/")
async def root():
    return {"message": "Welcome to the fullypack_fastapi!"}
