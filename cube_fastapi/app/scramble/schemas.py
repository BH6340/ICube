"""
打乱模块 Pydantic 模型

定义请求参数和响应数据结构，FastAPI 自动做参数校验和文档生成。
"""
from pydantic import BaseModel, Field


class ScrambleResponse(BaseModel):
    """单个打乱公式响应"""
    cube_type: str
    scramble: str
    scramble_id: str
    from_cache: bool


class ScrambleBatchResponse(BaseModel):
    """批量打乱公式响应"""
    cube_type: str
    scrambles: list[str]
    count: int
    from_cache: int


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    env: str
    cache_enabled: bool
    pool_sizes: dict[str, int] = Field(default_factory=dict)
