import logging
import math
import mimetypes
import os
from dataclasses import asdict
from io import BytesIO
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator, model_validator
from model.calculator import calculate_all_scenarios, calculate_scenario
from model.defaults import RETAILER_DEFAULTS, WEEKS_PER_MONTH
from model.excel import build_excel_workbook, workbook_to_bytes

# Windows MIME fix — must run before StaticFiles mount
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")

logger = logging.getLogger(__name__)

app = FastAPI(title="Retailer Launch Cost Model")

# CORS — default restrictive; set ENVIRONMENT=development to open for local work
environment = os.getenv("ENVIRONMENT", "production")
allow_origins = ["https://cost-of-saying-yes.fly.dev"] if environment == "production" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next) -> Response:
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' https://cdn.plot.ly; "
        "style-src 'self' 'unsafe-inline'; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "img-src 'self' data:; "
        "frame-ancestors 'none'"
    )
    if request.url.path == "/api/download/excel":
        response.headers["Cache-Control"] = "no-store"
    return response


class ScenarioInput(BaseModel):
    retailer: str = "walmart"
    doors: int
    skus: int
    unit_price_wholesale: float
    cogs_per_unit: float
    velocity_units_per_door_per_week: float
    broker_projection_year1: float | None = None

    @field_validator("doors")
    @classmethod
    def doors_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("doors must be greater than 0")
        if v > 10_000:
            raise ValueError("doors must be 10,000 or fewer")
        return v

    @field_validator("skus")
    @classmethod
    def skus_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("skus must be greater than 0")
        if v > 100:
            raise ValueError("skus must be 100 or fewer")
        return v

    @field_validator("velocity_units_per_door_per_week")
    @classmethod
    def velocity_positive(cls, v: float) -> float:
        if not math.isfinite(v):
            raise ValueError("velocity must be a finite number")
        if v <= 0:
            raise ValueError("velocity must be greater than 0")
        if v > 1_000:
            raise ValueError("velocity must be 1,000 or fewer")
        return v

    @field_validator("unit_price_wholesale", "cogs_per_unit")
    @classmethod
    def price_positive(cls, v: float) -> float:
        if not math.isfinite(v):
            raise ValueError("price fields must be finite numbers")
        if v <= 0:
            raise ValueError("price fields must be greater than 0")
        if v > 10_000:
            raise ValueError("price fields must be $10,000 or less")
        return v

    @field_validator("broker_projection_year1")
    @classmethod
    def broker_positive_if_set(cls, v: float | None) -> float | None:
        if v is None:
            return v
        if not math.isfinite(v):
            raise ValueError("broker_projection_year1 must be a finite number")
        if v <= 0:
            raise ValueError("broker_projection_year1 must be greater than 0")
        if v > 50_000_000:
            raise ValueError("broker_projection_year1 must be $50,000,000 or less")
        return v

    @model_validator(mode="after")
    def cogs_less_than_price(self):
        if self.cogs_per_unit >= self.unit_price_wholesale:
            raise ValueError("cogs_per_unit must be less than unit_price_wholesale")
        return self

    @model_validator(mode="after")
    def retailer_valid(self):
        if self.retailer not in RETAILER_DEFAULTS:
            raise ValueError(f"retailer must be one of {list(RETAILER_DEFAULTS.keys())}")
        return self

    def effective_broker_projection(self) -> float:
        if self.broker_projection_year1 is not None:
            return self.broker_projection_year1
        return (
            self.doors
            * self.skus
            * self.velocity_units_per_door_per_week
            * WEEKS_PER_MONTH
            * 12
            * self.unit_price_wholesale
        )


RETAILER_LABELS = {
    "walmart": "Walmart",
    "whole_foods": "Whole Foods / UNFI",
    "costco": "Costco",
    "regional_chain": "Regional Chain",
}


class CompareInput(BaseModel):
    doors: int
    skus: int
    unit_price_wholesale: float
    cogs_per_unit: float
    velocity_units_per_door_per_week: float
    broker_projection_year1: float | None = None

    @field_validator("doors")
    @classmethod
    def doors_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("doors must be greater than 0")
        if v > 10_000:
            raise ValueError("doors must be 10,000 or fewer")
        return v

    @field_validator("skus")
    @classmethod
    def skus_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("skus must be greater than 0")
        if v > 100:
            raise ValueError("skus must be 100 or fewer")
        return v

    @field_validator("velocity_units_per_door_per_week")
    @classmethod
    def velocity_positive(cls, v: float) -> float:
        if not math.isfinite(v):
            raise ValueError("velocity must be a finite number")
        if v <= 0:
            raise ValueError("velocity must be greater than 0")
        if v > 1_000:
            raise ValueError("velocity must be 1,000 or fewer")
        return v

    @field_validator("unit_price_wholesale", "cogs_per_unit")
    @classmethod
    def price_positive(cls, v: float) -> float:
        if not math.isfinite(v):
            raise ValueError("price fields must be finite numbers")
        if v <= 0:
            raise ValueError("price fields must be greater than 0")
        if v > 10_000:
            raise ValueError("price fields must be $10,000 or less")
        return v

    @field_validator("broker_projection_year1")
    @classmethod
    def broker_positive_if_set(cls, v: float | None) -> float | None:
        if v is None:
            return v
        if not math.isfinite(v):
            raise ValueError("broker_projection_year1 must be a finite number")
        if v <= 0:
            raise ValueError("broker_projection_year1 must be greater than 0")
        if v > 50_000_000:
            raise ValueError("broker_projection_year1 must be $50,000,000 or less")
        return v

    @model_validator(mode="after")
    def cogs_less_than_price(self):
        if self.cogs_per_unit >= self.unit_price_wholesale:
            raise ValueError("cogs_per_unit must be less than unit_price_wholesale")
        return self

    def effective_broker_projection(self) -> float:
        if self.broker_projection_year1 is not None:
            return self.broker_projection_year1
        return (
            self.doors
            * self.skus
            * self.velocity_units_per_door_per_week
            * WEEKS_PER_MONTH
            * 12
            * self.unit_price_wholesale
        )


@app.post("/api/compare")
def compare(inp: CompareInput):
    try:
        broker = inp.effective_broker_projection()
        rows = []
        for key in RETAILER_DEFAULTS:
            result = calculate_scenario(
                retailer=key,
                doors=inp.doors,
                skus=inp.skus,
                unit_price_wholesale=inp.unit_price_wholesale,
                cogs_per_unit=inp.cogs_per_unit,
                velocity_units_per_door_per_week=inp.velocity_units_per_door_per_week,
                broker_projection_year1=broker,
                scenario="realistic",
            )
            rows.append({
                "key": key,
                "label": RETAILER_LABELS.get(key, key),
                "trough_value": result.trough_value,
                "trough_month": result.trough_month,
                "break_even_month": result.break_even_month,
                "net_cash_impact_year1": result.summary["net_cash_impact_year1"],
            })
        rows.sort(key=lambda r: r["net_cash_impact_year1"], reverse=True)
        return {"retailers": rows}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception:
        logger.exception("Compare calculation failed")
        raise HTTPException(status_code=500, detail="Compare calculation failed — please try again")


@app.post("/api/calculate")
def calculate(inp: ScenarioInput):
    try:
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
    except Exception:
        logger.exception("Calculation failed")
        raise HTTPException(status_code=500, detail="Calculation failed — please try again")


@app.post("/api/download/excel")
def download_excel(inp: ScenarioInput):
    try:
        results = calculate_all_scenarios(
            retailer=inp.retailer,
            doors=inp.doors,
            skus=inp.skus,
            unit_price_wholesale=inp.unit_price_wholesale,
            cogs_per_unit=inp.cogs_per_unit,
            velocity_units_per_door_per_week=inp.velocity_units_per_door_per_week,
            broker_projection_year1=inp.effective_broker_projection(),
        )
        scenarios_dict = {k: asdict(v) for k, v in results.items()}
        wb = build_excel_workbook(scenarios_dict)
        excel_bytes = workbook_to_bytes(wb)

        return StreamingResponse(
            BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=retailer-launch-model.xlsx"},
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Excel generation failed")
        raise HTTPException(status_code=500, detail="Excel generation failed — please try again")


@app.get("/api/health")
def health():
    return {"status": "ok"}

# StaticFiles MUST be mounted last — it is a catch-all
app.mount("/", StaticFiles(directory="static", html=True), name="static")
