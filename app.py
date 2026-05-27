import mimetypes
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator, model_validator
from typing import Optional

# Windows MIME fix — must run before StaticFiles mount
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")

app = FastAPI(title="Retailer Launch Cost Model")

# CORS — open in dev, restrict in prod
environment = os.getenv("ENVIRONMENT", "development")
allow_origins = ["*"] if environment == "development" else ["https://cost-of-saying-yes.fly.dev"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ScenarioInput(BaseModel):
    retailer: str = "walmart"
    doors: int
    skus: int
    unit_price_wholesale: float
    cogs_per_unit: float
    velocity_units_per_door_per_week: float
    broker_projection_year1: Optional[float] = None

    @field_validator("doors")
    @classmethod
    def doors_positive(cls, v):
        if v <= 0:
            raise ValueError("doors must be greater than 0")
        return v

    @field_validator("skus")
    @classmethod
    def skus_positive(cls, v):
        if v <= 0:
            raise ValueError("skus must be greater than 0")
        return v

    @field_validator("velocity_units_per_door_per_week")
    @classmethod
    def velocity_positive(cls, v):
        if v <= 0:
            raise ValueError("velocity must be greater than 0")
        return v

    @field_validator("unit_price_wholesale", "cogs_per_unit")
    @classmethod
    def price_positive(cls, v):
        if v <= 0:
            raise ValueError("price fields must be greater than 0")
        return v

    @model_validator(mode="after")
    def cogs_less_than_price(self):
        if self.cogs_per_unit >= self.unit_price_wholesale:
            raise ValueError("cogs_per_unit must be less than unit_price_wholesale")
        return self

    @model_validator(mode="after")
    def retailer_valid(self):
        if self.retailer not in ("walmart", "whole_foods"):
            raise ValueError("retailer must be 'walmart' or 'whole_foods'")
        return self

    def effective_broker_projection(self) -> float:
        if self.broker_projection_year1 is not None:
            return self.broker_projection_year1
        return self.doors * self.skus * self.velocity_units_per_door_per_week * 4.33 * 12 * self.unit_price_wholesale


@app.post("/api/calculate")
def calculate(inp: ScenarioInput):
    from dataclasses import asdict
    from model.calculator import calculate_all_scenarios

    results = calculate_all_scenarios(
        retailer=inp.retailer,
        doors=inp.doors,
        skus=inp.skus,
        unit_price_wholesale=inp.unit_price_wholesale,
        cogs_per_unit=inp.cogs_per_unit,
        velocity_units_per_door_per_week=inp.velocity_units_per_door_per_week,
        broker_projection_year1=inp.effective_broker_projection(),
    )
    return {scenario: asdict(result) for scenario, result in results.items()}


@app.get("/api/download/excel")
def download_excel(retailer: str = "walmart", scenario: str = "realistic"):
    from io import BytesIO
    from fastapi.responses import StreamingResponse
    from model.calculator import calculate_all_scenarios
    from model.excel import build_excel_workbook, workbook_to_bytes
    from dataclasses import asdict

    # Use default Cinderhaven-ish params for a standalone download
    # (In production, the user would pass their own inputs via query params or POST)
    # For MVP, calculate a default scenario so the download always works
    results = calculate_all_scenarios(
        retailer=retailer,
        doors=1200,
        skus=4,
        unit_price_wholesale=1.00,
        cogs_per_unit=0.45,
        velocity_units_per_door_per_week=2.0,
        broker_projection_year1=499_200,
    )
    scenarios_dict = {k: asdict(v) for k, v in results.items()}
    wb = build_excel_workbook(scenarios_dict)
    excel_bytes = workbook_to_bytes(wb)

    return StreamingResponse(
        BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=retailer-launch-model.xlsx"}
    )


@app.get("/api/health")
def health():
    return {"status": "ok"}

# StaticFiles MUST be mounted last — it is a catch-all
app.mount("/", StaticFiles(directory="static", html=True), name="static")
