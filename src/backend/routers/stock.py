"""
Stock management endpoints for the High School Management System API
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

from ..database import stock_collection, teachers_collection

router = APIRouter(
    prefix="/stock",
    tags=["stock"]
)

class StockItem(BaseModel):
    item_id: str
    name: str
    category: str
    quantity: int
    unit: str
    location: str
    min_quantity: int

class StockUpdate(BaseModel):
    quantity: int

@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
def get_stock_items(
    category: Optional[str] = None,
    low_stock: Optional[bool] = None
) -> List[Dict[str, Any]]:
    """
    Get all stock items with optional filtering
    
    - category: Filter by category (e.g., 'Sports Equipment', 'Art Supplies')
    - low_stock: If true, only return items below minimum quantity threshold
    """
    query = {}
    
    if category:
        query["category"] = category
    
    items = list(stock_collection.find(query))
    
    # Remove MongoDB _id field
    for item in items:
        item.pop('_id', None)
    
    # Filter for low stock if requested
    if low_stock:
        items = [item for item in items if item["quantity"] < item["min_quantity"]]
    
    return items

@router.get("/categories", response_model=List[str])
def get_categories() -> List[str]:
    """Get a list of all stock categories"""
    categories = stock_collection.distinct("category")
    return sorted(categories)

@router.get("/{item_id}", response_model=Dict[str, Any])
def get_stock_item(item_id: str) -> Dict[str, Any]:
    """Get a specific stock item by ID"""
    item = stock_collection.find_one({"item_id": item_id})
    
    if not item:
        raise HTTPException(status_code=404, detail="Stock item not found")
    
    item.pop('_id', None)
    return item

@router.post("", response_model=Dict[str, Any])
@router.post("/", response_model=Dict[str, Any])
def create_stock_item(item: StockItem, teacher_username: Optional[str] = Query(None)) -> Dict[str, Any]:
    """Create a new stock item - requires teacher authentication"""
    # Check teacher authentication
    if not teacher_username:
        raise HTTPException(status_code=401, detail="Authentication required for this action")
    
    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")
    
    # Check if item_id already exists
    existing_item = stock_collection.find_one({"item_id": item.item_id})
    if existing_item:
        raise HTTPException(status_code=400, detail="Item ID already exists")
    
    # Insert the new item
    item_dict = item.model_dump()
    stock_collection.insert_one(item_dict)
    
    return {"message": f"Stock item {item.item_id} created successfully"}

@router.put("/{item_id}", response_model=Dict[str, Any])
def update_stock_quantity(
    item_id: str, 
    update: StockUpdate,
    teacher_username: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """Update stock item quantity - requires teacher authentication"""
    # Check teacher authentication
    if not teacher_username:
        raise HTTPException(status_code=401, detail="Authentication required for this action")
    
    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")
    
    # Check if item exists
    item = stock_collection.find_one({"item_id": item_id})
    if not item:
        raise HTTPException(status_code=404, detail="Stock item not found")
    
    # Update quantity
    result = stock_collection.update_one(
        {"item_id": item_id},
        {"$set": {"quantity": update.quantity}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to update stock item")
    
    return {"message": f"Stock item {item_id} quantity updated to {update.quantity}"}

@router.delete("/{item_id}", response_model=Dict[str, Any])
def delete_stock_item(item_id: str, teacher_username: Optional[str] = Query(None)) -> Dict[str, Any]:
    """Delete a stock item - requires teacher authentication"""
    # Check teacher authentication
    if not teacher_username:
        raise HTTPException(status_code=401, detail="Authentication required for this action")
    
    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")
    
    # Check if item exists
    item = stock_collection.find_one({"item_id": item_id})
    if not item:
        raise HTTPException(status_code=404, detail="Stock item not found")
    
    # Delete the item
    result = stock_collection.delete_one({"item_id": item_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=500, detail="Failed to delete stock item")
    
    return {"message": f"Stock item {item_id} deleted successfully"}
