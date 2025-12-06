from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

Base.metadata.create_all(bind=engine)

app = FastAPI(title='Мини-CRM распределения лидов', version='1.0.0')

