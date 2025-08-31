from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db
from models import Company, SustainabilityMetric, FleetSummary, EmissionsSummary, AltFuelsSummary, CleanEnergyPartnersSummary, RegulatoryPressureSummary

router = APIRouter()

@router.get("/company_card/{company_id}")
async def get_company_card(company_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Company).filter(Company.company_id == company_id))
    company = result.scalars().first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    sustainability = (await db.execute(
        select(SustainabilityMetric).filter(SustainabilityMetric.company_id == company_id)
    )).scalars().first()

    fleet_summary = (await db.execute(
        select(FleetSummary).filter(FleetSummary.metric_id == sustainability.metric_id)
    )).scalars().first() if sustainability else None

    emissions_summary = (await db.execute(
        select(EmissionsSummary).filter(EmissionsSummary.metric_id == sustainability.metric_id)
    )).scalars().first() if sustainability else None

    alt_fuels_summary = (await db.execute(
        select(AltFuelsSummary).filter(AltFuelsSummary.metric_id == sustainability.metric_id)
    )).scalars().first() if sustainability else None

    clean_energy_summary = (await db.execute(
        select(CleanEnergyPartnersSummary).filter(CleanEnergyPartnersSummary.metric_id == sustainability.metric_id)
    )).scalars().first() if sustainability else None

    regulatory_summary = (await db.execute(
        select(RegulatoryPressureSummary).filter(RegulatoryPressureSummary.metric_id == sustainability.metric_id)
    )).scalars().first() if sustainability else None

    return {
        "company_name": company.company_name,
        "company_summary": company.company_summary,
        "website_url": company.website_url,
        "industry": company.industry,
        "cso_linkedin_url": company.cso_linkedin_url,
        "sustainability_metrics": {
            "owns_cng_fleet": sustainability.owns_cng_fleet,
            "cng_fleet_size_range": sustainability.cng_fleet_size_range,
            "cng_fleet_size_actual": sustainability.cng_fleet_size_actual,
            "total_fleet_size": sustainability.total_fleet_size,
            "emission_report": sustainability.emission_report,
            "emission_goals": sustainability.emission_goals,
            "alt_fuels": sustainability.alt_fuels,
            "clean_energy_partners": sustainability.clean_energy_partners,
            "regulatory_pressure": sustainability.regulatory_pressure,
            "cng_adopt_score": sustainability.cng_adopt_score
        } if sustainability else None,
        "summaries": {
            "fleet": fleet_summary.summary_text if fleet_summary else None,
            "emissions": {
                "summary": emissions_summary.emissions_summary if emissions_summary else None,
                "goals": emissions_summary.emissions_goals_summary if emissions_summary else None,
                "current_emissions": emissions_summary.current_emissions if emissions_summary else None,
                "target_year": emissions_summary.target_year if emissions_summary else None,
                "target_emissions": emissions_summary.target_emissions if emissions_summary else None
            },
            "alt_fuels": alt_fuels_summary.summary_text if alt_fuels_summary else None,
            "clean_energy": clean_energy_summary.summary_text if clean_energy_summary else None,
            "regulatory": regulatory_summary.summary_text if regulatory_summary else None
        }
    }
