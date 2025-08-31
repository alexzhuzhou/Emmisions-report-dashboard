from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import SustainabilityMetric, Company
from database import get_db
from pydantic import BaseModel, Field
from typing import Optional

class CNGAdoptionScoreCreate(BaseModel):
	company_id: int
	score: int = Field(..., ge=0, le=100)
	score_explanation: Optional[str] = None
	source_description: Optional[str] = None

class CNGAdoptionScoreUpdate(BaseModel):
	score: Optional[int] = Field(None, ge=0, le=100)
	score_explanation: Optional[str] = None
	source_description: Optional[str] = None

router = APIRouter(
	prefix="/api/cng-adoption-scores",
	tags=["CNG Adoption Scores"]
)

# GET all CNG scores
@router.get("/", summary="Retrieve all CNG adoption scores")
async def get_cng_adoption_scores(db: AsyncSession = Depends(get_db)):
	result = await db.execute(select(SustainabilityMetric))
	metrics = result.scalars().all()
	return {"success": True, "scores": [{"company_id": m.company_id, "score": m.cng_adopt_score} for m in metrics]}

# GET CNG score by company id
@router.get("/{company_id}", summary="Retrieve a CNG adoption score by company ID")
async def get_cng_adoption_score(company_id: int, db: AsyncSession = Depends(get_db)):
	result = await db.execute(select(SustainabilityMetric).filter(SustainabilityMetric.company_id == company_id))
	metric = result.scalars().first()
	if not metric:
		raise HTTPException(status_code=404, detail="Company metrics not found")
	return {"success": True, "score": {"company_id": metric.company_id, "score": metric.cng_adopt_score}}

# POST a new CNG score
@router.post("/", summary="Create a new CNG adoption score")
async def create_cng_adoption_score(score: CNGAdoptionScoreCreate, db: AsyncSession = Depends(get_db)):
	result = await db.execute(select(Company).filter(Company.company_id == score.company_id))
	if not result.scalars().first():
		raise HTTPException(status_code=404, detail="Company not found")

	db_score = SustainabilityMetric(
		company_id=score.company_id,
		cng_adopt_score=score.score,
		score_explanation=score.score_explanation,
		source_description=score.source_description
	)
	db.add(db_score)
	try:
		await db.commit()
		await db.refresh(db_score)
		return {"success": True, "message": "CNG adoption score created."}
	except Exception as e:
		await db.rollback()
		raise HTTPException(status_code=400, detail=f"Error creating CNG adoption score: {str(e)}")

# UPDATE an existing CNG score
@router.put("/{company_id}", summary="Update a CNG adoption score")
async def update_cng_adoption_score(company_id: int, score: CNGAdoptionScoreUpdate, db: AsyncSession = Depends(get_db)):
	result = await db.execute(select(SustainabilityMetric).filter(SustainabilityMetric.company_id == company_id))
	metric = result.scalars().first()
	if not metric:
		raise HTTPException(status_code=404, detail="Company metrics not found")

	if score.score is not None:
		metric.cng_adopt_score = score.score
	if score.score_explanation is not None:
		metric.score_explanation = score.score_explanation
	if score.source_description is not None:
		metric.source_description = score.source_description

	try:
		await db.commit()
		await db.refresh(metric)
		return {"success": True, "message": "CNG adoption score updated."}
	except Exception as e:
		await db.rollback()
		raise HTTPException(status_code=400, detail=f"Error updating CNG adoption score: {str(e)}")

# DELETE an existing CNG score
@router.delete("/{company_id}", summary="Delete a CNG adoption score")
async def delete_cng_adoption_score(company_id: int, db: AsyncSession = Depends(get_db)):
	result = await db.execute(select(SustainabilityMetric).filter(SustainabilityMetric.company_id == company_id))
	metric = result.scalars().first()
	if not metric:
		raise HTTPException(status_code=404, detail="CNG adoption score not found")

	try:
		await db.delete(metric)
		await db.commit()
		return {"success": True, "message": "CNG adoption score deleted."}
	except Exception as e:
		await db.rollback()
		raise HTTPException(status_code=400, detail=f"Error deleting CNG adoption score: {str(e)}")