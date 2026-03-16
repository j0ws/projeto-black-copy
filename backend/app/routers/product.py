from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.database import get_db
from app.models.product import Product

router = APIRouter(
    prefix="/api/v1/products",
    tags=["🧠 Product Intelligence (Module 2)"]
)

@router.get("/", summary="List all intelligence products")
def get_all_products(db: Session = Depends(get_db)):
    """
    Fetches the list of all seeded products and their core data.
    """
    products = db.query(Product).all()
    # Eager loading isn't strictly necessary for a simple dump if relationships are configured well,
    # but we can return a formatted dict to easily parse the relationships.

    result = []
    for p in products:
        result.append({
            "id": p.id,
            "name": p.name,
            "ingredients": p.ingredients,
            "use_cases": p.use_cases,
            "worst_alternatives": p.worst_alternatives,
            "benefits": [{"id": b.id, "description": b.description} for b in p.benefits],
            "pain_points": [{"id": pp.id, "description": pp.description, "lf8_trigger": pp.lf8_trigger} for pp in p.pain_points],
            "objections": [{"id": o.id, "type": o.type, "question": o.question, "answer": o.answer} for o in p.objections],
        })
    return {"data": result}

@router.get("/{product_id}", summary="Get specific product intelligence")
def get_product(product_id: int, db: Session = Depends(get_db)):
    """
    Fetch all strategic briefing elements for a single product to feed the Miner module.
    """
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")

    return {
        "id": p.id,
        "name": p.name,
        "ingredients": p.ingredients,
        "use_cases": p.use_cases,
        "worst_alternatives": p.worst_alternatives,
        "benefits": [{"id": b.id, "description": b.description} for b in p.benefits],
        "pain_points": [{"id": pp.id, "description": pp.description, "lf8_trigger": pp.lf8_trigger} for pp in p.pain_points],
        "objections": [{"id": o.id, "type": o.type, "question": o.question, "answer": o.answer} for o in p.objections],
    }

@router.post("/", summary="Create a new Product Briefing (Draft)")
def create_product(payload: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Draft endpoint for dynamically creating new products in the future (e.g. Product #2).
    In a real scenario, this would use strict Pydantic models for validation.
    """
    # ... CRUD Logic goes here
    return {"message": "Endpoint mapped for future dynamic creation."}
