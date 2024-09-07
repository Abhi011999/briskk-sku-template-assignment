from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship

DATABASE_URL = "postgresql+asyncpg://user:password@db:5432/product_db"

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

class Product(Base):
    __tablename__ = "products"

    product_id = Column(String, primary_key=True)
    product_name = Column(String, nullable=False)
    brand = Column(String, nullable=False)
    product_description = Column(String, nullable=False)
    category = Column(String, nullable=False)
    main_image = Column(String, nullable=False)
    product_highlights = Column(String, nullable=False)
    hsn_code = Column(String, nullable=False)
    skus = relationship("SKU", back_populates="product")

class SKU(Base):
    __tablename__ = "skus"

    sku_id = Column(String, primary_key=True)
    product_id = Column(String, ForeignKey("products.product_id"))
    size = Column(String, nullable=False)
    color = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False)
    facility_id = Column(String, nullable=False)
    facility_name = Column(String, nullable=False)
    product = relationship("Product", back_populates="skus")

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session