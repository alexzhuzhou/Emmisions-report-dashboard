# app/api/routes/scorecards.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
import logging

logger = logging.getLogger(__name__)

from database import get_db
from models import Company, SustainabilityMetric, MetricSource
from models import ( # Import summary models
    FleetSummary, EmissionsSummary, AltFuelsSummary,
    CleanEnergyPartnersSummary, RegulatoryPressureSummary
)
from summary_schema import ScorecardDataCreate # Assuming schemas.py

router = APIRouter(
    prefix="/api/analyzed_report",
    tags=["Analyzed Report"]
)

@router.post("/", summary="Upload and process a new scorecard", status_code=status.HTTP_201_CREATED)
async def create_scorecard_data(
    scorecard_data: ScorecardDataCreate,
    db: AsyncSession = Depends(get_db)
):
    # 1. Find or Create Company
    company_stmt = select(Company).filter(Company.company_name == scorecard_data.company_name)
    result = await db.execute(company_stmt)
    db_company = result.scalars().first()

    if db_company:
        # Optionally update company details if provided
        if scorecard_data.website_url:
            db_company.website_url = scorecard_data.website_url
        if scorecard_data.industry:
            db_company.industry = scorecard_data.industry
        # Potentially a generic company summary from one of the scorecard summaries
        # For now, we'll assume company_summary is handled elsewhere or manually
    else:
        # Create new company
        # For a more complete company profile, you might require more fields or have defaults
        db_company = Company(
            company_name=scorecard_data.company_name,
            website_url=scorecard_data.website_url,
            industry=scorecard_data.industry,
            company_summary="Summary to be generated or added." # Placeholder
        )
        db.add(db_company)
        try:
            await db.flush() # Use flush to get company_id before full commit if needed for metrics
        except IntegrityError as e:
            await db.rollback()
            raise HTTPException(status_code=409, detail=f"Company '{scorecard_data.company_name}' might already exist or other integrity violation: {e.orig}")
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Error creating company: {str(e)}")

    # 2. Create or Update SustainabilityMetrics
    # Check if metrics for this company already exist
    metrics_stmt = select(SustainabilityMetric).filter(SustainabilityMetric.company_id == db_company.company_id)
    result = await db.execute(metrics_stmt)
    db_metrics = result.scalars().first()

    metrics_payload = scorecard_data.sustainability_metrics_payload

    if db_metrics:
        # Update existing metrics
        db_metrics.owns_cng_fleet = metrics_payload.owns_cng_fleet
        db_metrics.cng_fleet_size_range = metrics_payload.cng_fleet_size_range
        db_metrics.cng_fleet_size_actual = metrics_payload.cng_fleet_size_actual
        db_metrics.total_fleet_size = metrics_payload.total_fleet_size
        db_metrics.emission_report = metrics_payload.emission_report
        db_metrics.emission_goals = metrics_payload.emission_goals
        db_metrics.alt_fuels = metrics_payload.alt_fuels
        db_metrics.clean_energy_partners = metrics_payload.clean_energy_partners
        db_metrics.regulatory_pressure = metrics_payload.regulatory_pressure
        logger.info(f"Updating metrics for company ID: {db_company.company_id}")
    else:
        # Create new metrics
        db_metrics = SustainabilityMetric(
            company_id=db_company.company_id,
            **metrics_payload.model_dump() # Pydantic v2, use .dict() for v1
        )
        db.add(db_metrics)
        logger.info(f"Creating new metrics for company ID: {db_company.company_id}")
    
    try:
        await db.flush() # Get metric_id if new
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error preparing sustainability metrics: {str(e)}")


    # 3. Clear existing MetricSources for this metric_id (if updating) and add new ones
    if db_metrics.metric_id: # Only if metrics exist (either pre-existing or just flushed)
        # This is a simple way to handle updates: delete old, insert new.
        # For more complex scenarios, you might want to diff.
        existing_sources_stmt = select(MetricSource).filter(MetricSource.metric_id == db_metrics.metric_id)
        result = await db.execute(existing_sources_stmt)
        for old_source in result.scalars().all():
            await db.delete(old_source)
        
        await db.flush() # Process deletions

        for source_payload in scorecard_data.metric_sources_payload:
            db_metric_source = MetricSource(
                metric_id=db_metrics.metric_id,
                metric_name=source_payload.metric_name,
                source_url=source_payload.source_url,
                contribution_text=source_payload.contribution_text
            )
            db.add(db_metric_source)

    # 4. Create/Update Summary Tables
    summaries_data = scorecard_data.company_section_summaries
    
    # Fleet Summary (CNG Fleet Presence + CNG Fleet Size)
    # Combine relevant summaries or pick one. For now, using cng_fleet_presence_summary.
    # Your `analyze_scorecard.py` produces more specific summaries than the DB schema.
    # You'll need to map them.
    
    # Helper function to get summary text
    def get_summary_text(key: str, default_text="Summary not provided."):
        item = summaries_data.get(key)
        return item.summary_text if item else default_text

    # FleetSummary (combining cng_fleet_presence and cng_fleet_size logic might be needed)
    # For simplicity, let's use cng_fleet_presence_summary if available, or a combined one if you adapt your JSON
    fleet_summary_text_parts = []
    if "cng_fleet_presence_summary" in summaries_data:
        fleet_summary_text_parts.append(get_summary_text("cng_fleet_presence_summary"))
    if "cng_fleet_size_summary" in summaries_data:
        fleet_summary_text_parts.append(get_summary_text("cng_fleet_size_summary"))
    
    final_fleet_summary_text = " ".join(fleet_summary_text_parts) if fleet_summary_text_parts else "Fleet summary not available."

    fleet_summary_stmt = select(FleetSummary).filter(FleetSummary.metric_id == db_metrics.metric_id)
    result = await db.execute(fleet_summary_stmt)
    db_fleet_summary = result.scalars().first()
    if db_fleet_summary:
        db_fleet_summary.summary_text = final_fleet_summary_text
    elif db_metrics.metric_id: # Only create if metric exists
        db.add(FleetSummary(metric_id=db_metrics.metric_id, summary_text=final_fleet_summary_text))


    # EmissionsSummary
    emissions_report_summary_text = get_summary_text("emission_reporting_summary")
    emissions_goals_summary_text = get_summary_text("emission_reduction_goals_summary")
    
    emissions_summary_stmt = select(EmissionsSummary).filter(EmissionsSummary.metric_id == db_metrics.metric_id)
    result = await db.execute(emissions_summary_stmt)
    db_emissions_summary = result.scalars().first()
    if db_emissions_summary:
        db_emissions_summary.emissions_summary = emissions_report_summary_text
        db_emissions_summary.emissions_goals_summary = emissions_goals_summary_text
        # TODO: Populate current_emissions, target_year, target_emissions if available in payload
    elif db_metrics.metric_id:
        db.add(EmissionsSummary(
            metric_id=db_metrics.metric_id,
            emissions_summary=emissions_report_summary_text,
            emissions_goals_summary=emissions_goals_summary_text
            # TODO: Add current_emissions, target_year, target_emissions
        ))
        
    # AltFuelsSummary
    alt_fuels_summary_text = get_summary_text("alternative_fuels_summary")
    alt_fuels_summary_stmt = select(AltFuelsSummary).filter(AltFuelsSummary.metric_id == db_metrics.metric_id)
    result = await db.execute(alt_fuels_summary_stmt)
    db_alt_fuels_summary = result.scalars().first()
    if db_alt_fuels_summary:
        db_alt_fuels_summary.summary_text = alt_fuels_summary_text
    elif db_metrics.metric_id:
        db.add(AltFuelsSummary(metric_id=db_metrics.metric_id, summary_text=alt_fuels_summary_text))

    # CleanEnergyPartnersSummary
    clean_energy_summary_text = get_summary_text("clean_energy_initiatives_summary") # map from JSON key
    clean_energy_summary_stmt = select(CleanEnergyPartnersSummary).filter(CleanEnergyPartnersSummary.metric_id == db_metrics.metric_id)
    result = await db.execute(clean_energy_summary_stmt)
    db_clean_energy_summary = result.scalars().first()
    if db_clean_energy_summary:
        db_clean_energy_summary.summary_text = clean_energy_summary_text
    elif db_metrics.metric_id:
        db.add(CleanEnergyPartnersSummary(metric_id=db_metrics.metric_id, summary_text=clean_energy_summary_text))
        
    # RegulatoryPressureSummary
    regulatory_summary_text = get_summary_text("regulatory_pressure_summary")
    regulatory_summary_stmt = select(RegulatoryPressureSummary).filter(RegulatoryPressureSummary.metric_id == db_metrics.metric_id)
    result = await db.execute(regulatory_summary_stmt)
    db_regulatory_summary = result.scalars().first()
    if db_regulatory_summary:
        db_regulatory_summary.summary_text = regulatory_summary_text
    elif db_metrics.metric_id:
        db.add(RegulatoryPressureSummary(metric_id=db_metrics.metric_id, summary_text=regulatory_summary_text))

    # Commit all changes
    try:
        await db.commit()
        # Optionally refresh objects if you need their latest state from DB, e.g., with new IDs
        if db_company: await db.refresh(db_company)
        if db_metrics: await db.refresh(db_metrics)
        # ... refresh other objects as needed
        
        return {
            "success": True,
            "message": f"Scorecard data for company '{scorecard_data.company_name}' processed successfully.",
            "company_id": db_company.company_id if db_company else None,
            "metric_id": db_metrics.metric_id if db_metrics else None
        }
    except IntegrityError as e:
        await db.rollback()
        # A more specific error might have been caught earlier, but this is a catch-all
        logger.error(f"Database Integrity Error: {e.orig}")
        raise HTTPException(status_code=409, detail=f"Database integrity error: {e.orig}")
    except Exception as e:
        await db.rollback()
        logger.error(f"General Database Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving scorecard data: {str(e)}")