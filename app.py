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
from model.defaults import RETAILER_DEFAULTS, SCENARIO_MULTIPLIERS, WEEKS_PER_MONTH
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


def compute_line_items(inp: ScenarioInput, scenario: str) -> list[dict]:
    """Decompose the model's costs into individual line items for the UI table."""
    defaults = RETAILER_DEFAULTS[inp.retailer]
    multipliers = SCENARIO_MULTIPLIERS[scenario]

    velocity = inp.velocity_units_per_door_per_week * multipliers["velocity"]
    cb_learning = defaults["chargeback_rate_learning"] * multipliers["chargeback_rate"]
    cb_steady = defaults["chargeback_rate_steady"] * multipliers["chargeback_rate"]

    units_per_month = inp.doors * inp.skus * velocity * WEEKS_PER_MONTH
    gross_monthly = units_per_month * inp.unit_price_wholesale
    gross_year1 = gross_monthly * 12

    new_store = defaults["new_store_allowance_per_sku_per_door"] * inp.skus * inp.doors
    slotting = defaults["slotting_per_sku"] * inp.skus
    free_fills = inp.skus * inp.doors * defaults["units_per_case"] * inp.cogs_per_unit

    trade_spend = gross_year1 * defaults["trade_spend_rate"]
    learning_cb = gross_monthly * cb_learning * 3
    steady_cb = gross_monthly * cb_steady * 9
    broker = gross_year1 * defaults["broker_commission_rate"]
    cogs = units_per_month * inp.cogs_per_unit * 12
    ops = defaults["ops_overhead_monthly"] * 12

    payment_lag = defaults["payment_lag_months"]
    last_ded_rate = defaults["trade_spend_rate"] + cb_steady + defaults["broker_commission_rate"]
    uncollected = gross_monthly * (1 - last_ded_rate) * payment_lag

    trade_pct = f"{defaults['trade_spend_rate']:.0%}"
    broker_pct = f"{defaults['broker_commission_rate']:.0%}"
    ops_monthly = f"${defaults['ops_overhead_monthly']:,.0f}"

    items = [{"label": "Gross Year 1 Revenue", "amount": round(gross_year1, 2)}]
    if new_store > 0:
        items.append({"label": "Upfront Allowances", "amount": round(-new_store, 2)})
    if slotting > 0:
        items.append({"label": "Slotting Fees", "amount": round(-slotting, 2)})
    items.extend([
        {"label": "Free Fills", "amount": round(-free_fills, 2)},
        {"label": f"Trade Spend ({trade_pct} of gross)", "amount": round(-trade_spend, 2)},
        {"label": "Learning-Curve Chargebacks (months 1–3)", "amount": round(-learning_cb, 2)},
        {"label": "Ongoing Deductions (months 4–12)", "amount": round(-steady_cb, 2)},
        {"label": f"Broker Commission ({broker_pct})", "amount": round(-broker, 2)},
        {"label": "COGS", "amount": round(-cogs, 2)},
        {"label": f"Ops Overhead ({ops_monthly}/mo)", "amount": round(-ops, 2)},
        {"label": "Cash Collection Lag (payment terms)", "amount": round(-uncollected, 2)},
    ])
    return items


RETAILER_LABELS = {
    "walmart": "Walmart",
    "whole_foods": "Whole Foods",
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
        response = {}
        for scenario, result in results.items():
            data = asdict(result)
            data["line_items"] = compute_line_items(inp, scenario)
            response[scenario] = data
        return response
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
