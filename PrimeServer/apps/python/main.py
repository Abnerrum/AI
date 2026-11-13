from fastapi import FastAPI
import sqlite3

app = FastAPI(title="PrimeServer Python")

@app.get("/")
def home():
    return {"servidor": "PrimeServer", "runtime": "Python", "status": "funcionando", "sqlite": sqlite3.sqlite_version}
