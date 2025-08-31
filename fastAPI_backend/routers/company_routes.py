from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import Company
from database import get_db
from pydantic import BaseModel
from typing import Optional

class CompanyCreate(BaseModel):
    company_name: str
    company_summary: str
    website_url: Optional[str] = None
    industry: Optional[str] = None
    cso_linkedin_url: Optional[str] = None

class CompanyUpdate(BaseModel):
    company_name: Optional[str] = None
    company_summary: Optional[str] = None
    website_url: Optional[str] = None
    industry: Optional[str] = None
    cso_linkedin_url: Optional[str] = None

router = APIRouter(
    prefix="/api/companies",
    tags=["Companies"] 
)

# GET all companies
@router.get("/", summary="Retrieve all companies")
async def get_companies(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Company))
    companies = result.scalars().all()
    return {"success": True, "companies": companies}

# POST a new company
@router.post("/", summary="Create a new company")
async def create_company(company: CompanyCreate, db: AsyncSession = Depends(get_db)):
    db_company = Company(
        company_name=company.company_name,
        company_summary=company.company_summary,
        website_url=company.website_url,
        industry=company.industry,
        cso_linkedin_url=company.cso_linkedin_url
    )
    db.add(db_company)
    try:
        await db.commit()
        await db.refresh(db_company)
        return {"success": True, "message": f"Company '{company.company_name}' created."}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Error creating company: {str(e)}")
    
# UPDATE a company
@router.put("/{company_id}", summary="Update an existing company")
async def update_company(company_id: int, company: CompanyUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Company).filter(Company.company_id == company_id))
    db_company = result.scalars().first()
    if not db_company:
        return HTTPException(status_code = 404, detail="Company not found")
    
    if company.company_name is not None:
        db_company.company_name = company.company_name
    if company.company_summary is not None:
        db_company.company_summary = company.company_summary
    if company.website_url is not None:
        db_company.website_url = company.website_url
    if company.industry is not None:
        db_company.industry = company.industry
    if company.cso_linkedin_url is not None:
        db_company.cso_linkedin_url = company.cso_linkedin_url

    try:
        await db.commit()
        await db.refresh(db_company)
        return {"success": True, "message": f"Company '{db_company.company_name}' updated."}
    except Exception as e:
        await db.rollback()
        return HTTPException(status_code = 400, detail=f"Error updating company: {str(e)}")    

# DELETE a company
@router.delete("/{company_id}", summary="Delete an existing company")
async def delete_company(company_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Company).filter(Company.company_id == company_id))
    company = result.scalars().first()
    if not company:
        raise HTTPException(status_code = 404, detail="Company not found")

    try:
        await db.delete(company)
        await db.commit()
        return {"success": True, "message": f"Company '{company.company_name}' deleted."}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Error deleting company: {str(e)}")
