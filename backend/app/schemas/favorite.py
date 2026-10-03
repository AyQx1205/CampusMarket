"""收藏相关 Schema。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.product import ProductBrief


class FavoriteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product: ProductBrief
    created_at: datetime
