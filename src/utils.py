import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile
from typing import List
import uuid
import asyncio
import aiohttp
import logging

from .db import Product as DBProduct, SKU as DBSKU
from .models import Product, SKU


logger = logging.getLogger(__name__)

S3_BUCKET = 'briskk-data-ingestion'

async def process_excel(file: UploadFile) -> List[Product]:
    try:
        df = pd.read_excel(file.file, sheet_name=0)
        products = {}
        
        for _, row in df.iterrows():
            product_id = row['product_id*']
            if product_id not in products:
                products[product_id] = Product(
                    product_id=product_id,
                    product_name=row['product_name*'],
                    brand=row['brand*'],
                    product_description=row['product_description*'],
                    category=row['category*'],
                    main_image=await process_image(row['main_image']),
                    product_highlights=row['product_highlights*'],
                    hsn_code=str(row['hsn_code*']),
                    skus=[]
                )
            
            sku = SKU(
                sku_id=row['sku_id*'],
                size=str(row['size*']),
                color=row['color*'],
                price=row['price*'],
                stock=row['stock*'],
                facility_id=row['facility_id*'],
                facility_name=row['facility_name*']
            )
            products[product_id].skus.append(sku)
        
        logger.info(f"Processed {len(products)} products from Excel file.")
        return list(products.values())
    except Exception as e:
        logger.error(f"Error processing Excel file: {str(e)}")
        raise

async def process_image(image_data):
    try:
        if isinstance(image_data, str):
            if image_data.startswith('http'):
                async with aiohttp.ClientSession() as session:
                    try:
                        async with session.head(image_data, timeout=10) as response:
                            if response.status == 200 and response.headers.get('Content-Type', '').startswith('image/'):
                                s3_url = await upload_to_s3(image_data)
                                logger.info(f"Uploaded image from URL to S3: {s3_url}")
                                return s3_url
                    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                        logger.warning(f"Error processing image URL: {str(e)}")
            else:
                s3_url = await upload_to_s3(image_data)
                logger.info(f"Uploaded image from local path to S3: {s3_url}")
                return s3_url

        elif image_data is None or pd.isna(image_data):
            logger.warning("Empty or NaN image data")
            return None
        else:
            raise ValueError(f"Unsupported image data type: {type(image_data)}")
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise

async def upload_to_s3(image):
    # Simulate upload delay
    await asyncio.sleep(2)
    
    # Generate a random file name
    file_name = f"{uuid.uuid4()}.jpg"
    
    # Return a simulated S3 URL
    return f"https://{S3_BUCKET}.s3.amazonaws.com/{file_name}"

async def ingest_data(products: List[Product], db: AsyncSession):
    try:
        ingested_count = 0
        for product in products:
            db_product = DBProduct(
                product_id=product.product_id,
                product_name=product.product_name,
                brand=product.brand,
                product_description=product.product_description,
                category=product.category,
                main_image=product.main_image,
                product_highlights=product.product_highlights,
                hsn_code=product.hsn_code
            )
            db.add(db_product)
            
            for sku in product.skus:
                db_sku = DBSKU(
                    sku_id=sku.sku_id,
                    product_id=product.product_id,
                    size=sku.size,
                    color=sku.color,
                    price=sku.price,
                    stock=sku.stock,
                    facility_id=sku.facility_id,
                    facility_name=sku.facility_name
                )
                db.add(db_sku)
            
            ingested_count += 1
        
        await db.commit()
        logger.info(f"Ingested {ingested_count} products into the database.")
        return ingested_count
    except Exception as e:
        logger.error(f"Error ingesting data: {str(e)}")
        await db.rollback()
        raise