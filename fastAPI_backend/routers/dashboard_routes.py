from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from database import get_db
from models import Company, SustainabilityMetric, EmissionsSummary
from pydantic import BaseModel
from typing import List, Optional

class CompanyData(BaseModel):
    name: str
    cngFleetPresence: bool
    cngFleetSize: str
    emissionReporting: bool
    emissionReductionGoals: str
    alternativeFuels: bool
    cleanEnergyPartnerships: bool
    regulatoryPressure: bool

class EmissionDataPoint(BaseModel):
    year: int
    value: float

class SourceLink(BaseModel):
    title: str
    url: str

class EmissionGoalData(BaseModel):
    companyName: str
    targetYear: int
    currentYear: int
    goalDescription: str
    strategy: str
    additionalInfo: str
    sources: List[SourceLink]
    emissions: List[EmissionDataPoint]

router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"]
)

def map_cng_fleet_size(cng_fleet_size_range: int) -> str:
    """Map database cng_fleet_size_range to frontend expected values"""
    mapping = {
        0: "None",
        1: "1-10", 
        2: "11-50",
        3: "50+"
    }
    return mapping.get(cng_fleet_size_range, "None")

def map_emission_goals(emission_goals: int) -> str:
    """Map database emission_goals to frontend expected values"""
    mapping = {
        0: "No",
        1: "Goal mentioned",
        2: "Goal with timeline"
    }
    return mapping.get(emission_goals, "No")

@router.get("/companies", response_model=List[CompanyData])
async def get_companies_for_dashboard(db: AsyncSession = Depends(get_db)):
    """Get all companies with their sustainability metrics in the format expected by frontend"""
    try:
        # Join companies with their sustainability metrics
        result = await db.execute(
            select(Company, SustainabilityMetric).outerjoin(
                SustainabilityMetric, Company.company_id == SustainabilityMetric.company_id
            )
        )
        
        companies_data = []
        for company, metric in result:
            company_data = CompanyData(
                name=company.company_name,
                cngFleetPresence=metric.owns_cng_fleet if metric else False,
                cngFleetSize=map_cng_fleet_size(metric.cng_fleet_size_range if metric else 0),
                emissionReporting=metric.emission_report if metric else False,
                emissionReductionGoals=map_emission_goals(metric.emission_goals if metric else 0),
                alternativeFuels=metric.alt_fuels if metric else False,
                cleanEnergyPartnerships=metric.clean_energy_partners if metric else False,
                regulatoryPressure=metric.regulatory_pressure if metric else False
            )
            companies_data.append(company_data)
        
        return companies_data
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving companies: {str(e)}")

@router.get("/emissions/{company_name}", response_model=EmissionGoalData)
async def get_company_emissions(company_name: str, db: AsyncSession = Depends(get_db)):
    """Get emission data for a specific company"""
    try:
        # Get company
        company_result = await db.execute(
            select(Company).filter(Company.company_name == company_name)
        )
        company = company_result.scalars().first()
        
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Get sustainability metrics
        metric_result = await db.execute(
            select(SustainabilityMetric).filter(SustainabilityMetric.company_id == company.company_id)
        )
        metric = metric_result.scalars().first()
        
        # Get emissions summary if metric exists
        emissions_summary = None
        if metric:
            emissions_result = await db.execute(
                select(EmissionsSummary).filter(EmissionsSummary.metric_id == metric.metric_id)
            )
            emissions_summary = emissions_result.scalars().first()
        
        if not emissions_summary:
            # Return default data if no emissions data found
            return EmissionGoalData(
                companyName=company.company_name,
                targetYear=2050,
                currentYear=2025,
                goalDescription="No emission goals data available",
                strategy="No strategy information available",
                additionalInfo="No additional information available",
                sources=[],
                emissions=[]
            )
        
        # Create emission data points (simplified for now)
        emission_points = []
        if emissions_summary.current_emissions and emissions_summary.target_emissions:
            current_year = 2024
            emission_points = [
                EmissionDataPoint(year=current_year, value=float(emissions_summary.current_emissions)),
                EmissionDataPoint(year=emissions_summary.target_year, value=float(emissions_summary.target_emissions))
            ]
        
        return EmissionGoalData(
            companyName=company.company_name,
            targetYear=emissions_summary.target_year,
            currentYear=2025,
            goalDescription=emissions_summary.emissions_goals_summary,
            strategy=emissions_summary.emissions_summary,
            additionalInfo="CNG usage and sustainability information included in analysis",
            sources=[
                SourceLink(title=f"{company.company_name} Sustainability Report", url=company.website_url or "#")
            ],
            emissions=emission_points
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving emission data: {str(e)}") 