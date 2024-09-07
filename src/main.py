import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.openapi.utils import get_openapi
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from contextlib import asynccontextmanager
from sqlalchemy.orm import selectinload
from dotenv import load_dotenv
import logging
from fastapi.responses import JSONResponse

from .db import get_db, init_db, Product
from .models import ProductResponse, SKUResponse
from .utils import process_excel, ingest_data


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title="Product Management API",
    description="API for ingesting and retrieving product data",
    version="1.0.0",
    lifespan=lifespan
)

@app.post("/ingest", 
    summary="Ingest product data",
    description="Upload an Excel file containing product data for ingestion",
    response_description="Ingestion result",
    responses={
        200: {
            "description": "Successful ingestion",
            "content": {
                "application/json": {
                    "example": {"message": "Data ingestion completed", "ingested_count": 10}
                }
            }
        },
        400: {"description": "Invalid file format"},
        500: {"description": "Internal server error"}
    }
)
async def ingest_products(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    try:
        if not file.filename.endswith('.xlsx'):
            raise HTTPException(status_code=400, detail="Only Excel files are allowed")
        
        products_data = await process_excel(file)
        result = await ingest_data(products_data, db)
        logger.info(f"Data ingestion completed. Ingested {result} products.")
        return {"message": "Data ingestion completed", "ingested_count": result}
    except Exception as e:
        logger.error(f"Error during data ingestion: {str(e)}")
        return JSONResponse(status_code=500, content={"message": "An error occurred during data ingestion"})

@app.get("/products",
    summary="Retrieve all products",
    description="Get a list of all products with their associated SKUs",
    response_description="List of products",
    responses={
        200: {
            "description": "Successful retrieval",
            "content": {
                "application/json": {
                    "example": {
                        "products": [
                            {
                                "product_id": "123",
                                "product_name": "Example Product",
                                "brand": "Example Brand",
                                "product_description": "This is an example product",
                                "category": "Example Category",
                                "main_image": "http://example.com/image.jpg",
                                "product_highlights": ["Feature 1", "Feature 2"],
                                "hsn_code": "1234",
                                "skus": [
                                    {
                                        "sku_id": "SKU123",
                                        "mrp": 100.00,
                                        "selling_price": 90.00,
                                        "currency": "USD",
                                        "stock_qty": 50
                                    }
                                ]
                            }
                        ]
                    }
                }
            }
        },
        500: {"description": "Internal server error"}
    }
)
async def read_products(db: AsyncSession = Depends(get_db)):
    try:
        async with db as session:
            stmt = select(Product).options(selectinload(Product.skus))
            result = await session.execute(stmt)
            products = result.scalars().all()

            product_responses = []
            for product in products:
                sku_responses = [SKUResponse(**sku.__dict__) for sku in product.skus]
                product_response = ProductResponse(
                    product_id=product.product_id,
                    product_name=product.product_name,
                    brand=product.brand,
                    product_description=product.product_description,
                    category=product.category,
                    main_image=product.main_image,
                    product_highlights=product.product_highlights,
                    hsn_code=product.hsn_code,
                    skus=sku_responses
                )
                product_responses.append(product_response)

        logger.info(f"Retrieved {len(product_responses)} products.")
        return {"products": product_responses}
    except Exception as e:
        logger.error(f"Error retrieving products: {str(e)}")
        return JSONResponse(status_code=500, content={"message": "An error occurred while retrieving products"})

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)