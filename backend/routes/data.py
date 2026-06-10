"""
Data API routes — serve mock data from CSV files in the data/ folder.

These APIs mimic actual backend data endpoints and serve sample data for development.
"""

from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/data", tags=["data"])

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "expanded" / "csv"


def load_csv_data(filename: str) -> list[dict[str, Any]]:
    """Load CSV file and return as list of dictionaries."""
    file_path = DATA_DIR / f"{filename}.csv"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Data file '{filename}' not found")
    
    try:
        df = pd.read_csv(file_path)
        df = df.where(pd.notna(df), None)
        return df.to_dict("records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")


@router.get("/entities", summary="Get all entities")
async def get_entities(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> dict[str, Any]:
    """Retrieve list of entities with pagination."""
    data = load_csv_data("entities")
    total = len(data)
    paginated = data[skip : skip + limit]
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": paginated,
    }


@router.get("/invoices", summary="Get all invoices")
async def get_invoices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: str | None = Query(None),
) -> dict[str, Any]:
    """Retrieve list of invoices with optional filtering and pagination."""
    data = load_csv_data("invoices")
    
    if status:
        data = [item for item in data if item.get("status") == status]
    
    total = len(data)
    paginated = data[skip : skip + limit]
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "status_filter": status,
        "data": paginated,
    }


@router.get("/payments", summary="Get all payments")
async def get_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> dict[str, Any]:
    """Retrieve list of payments with pagination."""
    data = load_csv_data("payments")
    total = len(data)
    paginated = data[skip : skip + limit]
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": paginated,
    }


@router.get("/purchase-orders", summary="Get all purchase orders")
async def get_purchase_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> dict[str, Any]:
    """Retrieve list of purchase orders with pagination."""
    data = load_csv_data("purchase_orders")
    total = len(data)
    paginated = data[skip : skip + limit]
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": paginated,
    }


@router.get("/vendors", summary="Get all vendors")
async def get_vendors(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> dict[str, Any]:
    """Retrieve list of vendors with pagination."""
    data = load_csv_data("vendors")
    total = len(data)
    paginated = data[skip : skip + limit]
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": paginated,
    }


@router.get("/contracts", summary="Get all contracts")
async def get_contracts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> dict[str, Any]:
    """Retrieve list of contracts with pagination."""
    data = load_csv_data("contracts")
    total = len(data)
    paginated = data[skip : skip + limit]
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": paginated,
    }


@router.get("/approvals", summary="Get all approvals")
async def get_approvals(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> dict[str, Any]:
    """Retrieve list of approvals with pagination."""
    data = load_csv_data("approvals")
    total = len(data)
    paginated = data[skip : skip + limit]
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": paginated,
    }


@router.get("/projects", summary="Get all projects")
async def get_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> dict[str, Any]:
    """Retrieve list of projects with pagination."""
    data = load_csv_data("projects")
    total = len(data)
    paginated = data[skip : skip + limit]
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": paginated,
    }


@router.get("/alerts", summary="Get all alerts")
async def get_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> dict[str, Any]:
    """Retrieve list of alerts with pagination."""
    data = load_csv_data("alerts_seed")
    total = len(data)
    paginated = data[skip : skip + limit]
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": paginated,
    }
