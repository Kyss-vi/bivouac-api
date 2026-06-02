from __future__ import annotations

import os
from datetime import datetime, time
from typing import Literal, Optional, List, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, HttpUrl
import geopandas as gpd
from shapely.geometry import Point

APP_TITLE = "Bivouac Pays Basque API"
APP_VERSION = "1.0.0"
ENV = os.getenv("ENV", "development")

DecisionState = Literal["autorise", "autorise_sous_conditions", "interdit", "a_verifier_localement"]
ConfidenceLevel = Literal["high", "medium", "low"]
ZoneType = Literal["protected_area", "official_bivouac_area", "local_regulated_area"]
Activity = Literal["bivouac_tente"]

app = FastAPI(title=APP_TITLE, version=APP_VERSION)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class BivouacCheckRequest(BaseModel):
    lat: float
    lon: float
    datetime: datetime
    activity: Activity

class ZoneSummary(BaseModel):
    zone_id: str
    name: str
    zone_type: ZoneType

class BivouacCheckResponse(BaseModel):
    state: DecisionState
    zone: Optional[ZoneSummary] = None
    reason: str
    constraints: List[str] = []
    source_ref: str
    confidence: ConfidenceLevel

@app.get("/")
def root():
    return {"name": APP_TITLE, "version": APP_VERSION, "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/bivouac/check", response_model=BivouacCheckResponse)
def check_bivouac(payload: BivouacCheckRequest):
    t = payload.datetime.time()
    entre_19_et_9 = t >= time(19, 0) or t < time(9, 0)
    if entre_19_et_9:
        return BivouacCheckResponse(
            state="autorise_sous_conditions",
            reason="Bivouac autorisé entre 19h et 9h en cœur de parc, à plus d'1h d'un accès motorisé.",
            constraints=["tente montée après 19h", "tente démontée avant 9h", "pas de feu"],
            source_ref="S-001",
            confidence="high",
        )
    return BivouacCheckResponse(
        state="interdit",
        reason="En dehors des horaires autorisés (19h-9h).",
        constraints=["revenir après 19h"],
        source_ref="S-001",
        confidence="high",
    )
