from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import Company, SustainabilityMetric, FleetSummary, EmissionsSummary, AltFuelsSummary, CleanEnergyPartnersSummary, RegulatoryPressureSummary
from database import get_db
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class SavedReportMetrics(BaseModel):
    cngFleetPresence: bool
    cngFleetSize: str
    cngFleetSizeActual: int
    totalFleetSize: int
    emissionReporting: bool
    emissionGoals: int
    alternativeFuels: bool
    cleanEnergy: bool
    regulatoryPressure: bool

class SavedReport(BaseModel):
    id: str
    companyName: str
    overallScore: int
    summary: str
    dateCreated: str
    websiteUrl: Optional[str]
    industry: Optional[str]
    csoLinkedinUrl: Optional[str]
    metrics: SavedReportMetrics

router = APIRouter(
    prefix="/api/saved-reports",
    tags=["Saved Reports"]
)

@router.get("/", response_model=List[SavedReport])
async def get_saved_reports(db: AsyncSession = Depends(get_db)):
    try:
        # Get all companies with their sustainability metrics
        result = await db.execute(
            select(Company, SustainabilityMetric).outerjoin(
                SustainabilityMetric, Company.company_id == SustainabilityMetric.company_id
            )
        )
        
        saved_reports = []
        for company, metric in result:
            if not metric:
                continue

            # Map CNG fleet size range to string
            cng_fleet_size_map = {
                0: "None",
                1: "1-10",
                2: "11-50",
                3: "50+"
            }

            # Use the cng_adopt_score from the database instead of calculating
            overall_score = metric.cng_adopt_score or 0

            saved_report = SavedReport(
                id=str(company.company_id),
                companyName=company.company_name,
                overallScore=overall_score,
                summary=company.company_summary or "No summary available",
                dateCreated=company.created_at.strftime("%Y-%m-%d"),
                websiteUrl=company.website_url,
                industry=company.industry,
                csoLinkedinUrl=company.cso_linkedin_url,
                metrics=SavedReportMetrics(
                    cngFleetPresence=metric.owns_cng_fleet,
                    cngFleetSize=cng_fleet_size_map.get(metric.cng_fleet_size_range, "None"),
                    cngFleetSizeActual=metric.cng_fleet_size_actual,
                    totalFleetSize=metric.total_fleet_size,
                    emissionReporting=metric.emission_report,
                    emissionGoals=metric.emission_goals,
                    alternativeFuels=metric.alt_fuels,
                    cleanEnergy=metric.clean_energy_partners,
                    regulatoryPressure=metric.regulatory_pressure
                )
            )
            saved_reports.append(saved_report)

        return saved_reports

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving saved reports: {str(e)}")