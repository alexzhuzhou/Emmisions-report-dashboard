from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import SustainabilityMetric, Company
from database import get_db
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SustainabilityMetricCreate(BaseModel):
	company_id: int
	owns_cng_fleet: bool = False
	cng_fleet_size_range: int = 0
	cng_fleet_size_actual: int = 0
	total_fleet_size: int = 0
	emission_report: bool = False
	emission_goals: int = 0
	alt_fuels: bool = False
	clean_energy_partners: bool = False
	regulatory_pressure: bool = False
	cng_adopt_score: int = 0

class SustainabilityMetricUpdate(BaseModel):
	owns_cng_fleet: Optional[bool] = None
	cng_fleet_size_range: Optional[int] = None
	cng_fleet_size_actual: Optional[int] = None
	total_fleet_size: Optional[int] = None
	emission_report: Optional[bool] = None
	emission_goals: Optional[int] = None
	alt_fuels: Optional[bool] = None
	clean_energy_partners: Optional[bool] = None
	regulatory_pressure: Optional[bool] = None
	cng_adopt_score: Optional[int] = None

router = APIRouter(
	prefix="/api/sustainability-metrics",
	tags=["Sustainability Metrics"]
)

# GET all sustainability metrics
@router.get("/", summary="Retrieve all sustainability metrics")
async def get_sustainability_metrics(db: AsyncSession = Depends(get_db)):
	result = await db.execute(select(SustainabilityMetric))
	metrics = result.scalars().all()
	return {"success": True, "metrics": metrics}

# GET a sustainability metric by ID
@router.get("/{metric_id}", summary="Retrieve a sustainability metric by ID")
async def get_sustainability_metric(metric_id: int, db: AsyncSession = Depends(get_db)):
	result = await db.execute(select(SustainabilityMetric).filter(SustainabilityMetric.metric_id == metric_id))
	metric = result.scalars().first()
	if not metric:
		raise HTTPException(status_code=404, detail="Sustainability metric not found")
	return {"success": True, "metric": metric}

# POST a new sustainability metric
@router.post("/", summary="Create a new sustainability metric")
async def create_sustainability_metric(metric: SustainabilityMetricCreate, db: AsyncSession = Depends(get_db)):
	result = await db.execute(select(Company).filter(Company.company_id == metric.company_id))
	if not result.scalars().first():
		raise HTTPException(status_code=404, detail="Company not found")

	db_metric = SustainabilityMetric(
		company_id=metric.company_id,
		owns_cng_fleet=metric.owns_cng_fleet,
		cng_fleet_size_range=metric.cng_fleet_size_range,
		cng_fleet_size_actual=metric.cng_fleet_size_actual,
		total_fleet_size=metric.total_fleet_size,
		emission_report=metric.emission_report,
		emission_goals=metric.emission_goals,
		alt_fuels=metric.alt_fuels,
		clean_energy_partners=metric.clean_energy_partners,
		regulatory_pressure=metric.regulatory_pressure,
		cng_adopt_score=metric.cng_adopt_score
	)
	
	db.add(db_metric)
	try:
		await db.commit()
		await db.refresh(db_metric)
		return {"success": True, "message": "Sustainability metric created."}
	except Exception as e:
		await db.rollback()
		raise HTTPException(status_code=400, detail=f"Error creating sustainability metric: {str(e)}")

# UPDATE an existing sustainability metric
@router.put("/{metric_id}", summary="Update a sustainability metric")
async def update_sustainability_metric(metric_id: int, metric: SustainabilityMetricUpdate, db: AsyncSession = Depends(get_db)):
	result = await db.execute(select(SustainabilityMetric).filter(SustainabilityMetric.metric_id == metric_id))
	db_metric = result.scalars().first()
	if not db_metric:
		raise HTTPException(status_code=404, detail="Sustainability metric not found")

	if metric.owns_cng_fleet is not None:
		db_metric.owns_cng_fleet = metric.owns_cng_fleet
	if metric.cng_fleet_size_range is not None:
		db_metric.cng_fleet_size_range = metric.cng_fleet_size_range
	if metric.cng_fleet_size_actual is not None:
		db_metric.cng_fleet_size_actual = metric.cng_fleet_size_actual
	if metric.total_fleet_size is not None:
		db_metric.total_fleet_size = metric.total_fleet_size
	if metric.emission_report is not None:
		db_metric.emission_report = metric.emission_report
	if metric.emission_goals is not None:
		db_metric.emission_goals = metric.emission_goals
	if metric.alt_fuels is not None:
		db_metric.alt_fuels = metric.alt_fuels
	if metric.clean_energy_partners is not None:
		db_metric.clean_energy_partners = metric.clean_energy_partners
	if metric.regulatory_pressure is not None:
		db_metric.regulatory_pressure = metric.regulatory_pressure
	if metric.cng_adopt_score is not None:
		db_metric.cng_adopt_score = metric.cng_adopt_score

	try:
		await db.commit()
		await db.refresh(db_metric)
		return {"success": True, "message": "Sustainability metric updated."}
	except Exception as e:
		await db.rollback()
		raise HTTPException(status_code=400, detail=f"Error updating sustainability metric: {str(e)}")

# DELETE an existing sustainability metric
@router.delete("/{metric_id}", summary="Delete a sustainability metric")
async def delete_sustainability_metric(metric_id: int, db: AsyncSession = Depends(get_db)):
	result = await db.execute(select(SustainabilityMetric).filter(SustainabilityMetric.metric_id == metric_id))
	metric = result.scalars().first()
	if not metric:
		raise HTTPException(status_code=404, detail="Sustainability metric not found")

	try:
		await db.delete(metric)
		await db.commit()
		return {"success": True, "message": "Sustainability metric deleted."}
	except Exception as e:
		await db.rollback()
		raise HTTPException(status_code=400, detail=f"Error deleting sustainability metric: {str(e)}")