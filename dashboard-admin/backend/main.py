# Create the file with nano or vim, or use `touch` and then edit
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
