from pydantic import BaseModel
from typing import List

class SKU(BaseModel):
    sku_id: str
    size: str
    color: str
    price: float
    stock: int
    facility_id: str
    facility_name: str

class Product(BaseModel):
    product_id: str
    product_name: str
    brand: str
    product_description: str
    category: str
    main_image: str
    product_highlights: str
    hsn_code: str
    skus: List[SKU]

class ProductIngestion(BaseModel):
    products: List[Product]

class SKUResponse(SKU):
    pass

class ProductResponse(Product):
    skus: List[SKUResponse]