from pydantic import BaseModel

from fastapi import APIRouter, Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.services.build_purchase_order import build_purchase_order
from app.services.chat_agent import chat_with_agent, chat_with_agent_stream
from app.db.session import get_db
from app.services.analyze_full_catalog import analyze_full_catalog
from app.services.dead_stock_recommendation import get_dead_stock_recommendation
from app.services.explain_decision import explain_decision_for_sku
from app.services.flag_dead_stock import flag_dead_stock
from app.services.forecast_demand import forecast_demand
from app.services.get_item_deep_dive import get_item_deep_dive

router = APIRouter(prefix="/agent-tools", tags=["agent-tools"])


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


@router.get("/analyze-full-catalog", summary="Analyze full catalog")
def analyze_full_catalog_route(db: Session = Depends(get_db)) -> dict:
    return analyze_full_catalog(db)


@router.post("/chat", summary="Chat with Stocky")
def chat_with_agent_route(payload: ChatRequest, db: Session = Depends(get_db)) -> dict:
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message must not be empty")
    return chat_with_agent(db, payload.message, conversation_id=payload.conversation_id)


@router.post("/chat/stream", summary="Chat with Stocky (SSE streaming)")
def chat_with_agent_stream_route(
    payload: ChatRequest, db: Session = Depends(get_db)
) -> StreamingResponse:
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message must not be empty")
    return StreamingResponse(
        chat_with_agent_stream(
            db, payload.message, conversation_id=payload.conversation_id
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/items/{sku}/deep-dive", summary="Get item deep dive")
def get_item_deep_dive_route(sku: str, db: Session = Depends(get_db)) -> dict:
    result = get_item_deep_dive(db, sku)
    if result is None:
        raise HTTPException(status_code=404, detail=f"SKU '{sku}' not found")
    return result


@router.get("/items/{sku}/forecast-demand", summary="Forecast demand for item")
def forecast_demand_route(sku: str, db: Session = Depends(get_db)) -> dict:
    result = forecast_demand(db, sku)
    if result is None:
        raise HTTPException(status_code=404, detail=f"SKU '{sku}' not found")
    return result


@router.get("/build-purchase-order", summary="Build purchase order plan")
def build_purchase_order_route(
    supplier_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict:
    return build_purchase_order(db, supplier_id=supplier_id)


@router.get("/flag-dead-stock", summary="Flag dead stock items")
def flag_dead_stock_route(db: Session = Depends(get_db)) -> dict:
    return flag_dead_stock(db)


@router.get("/items/{sku}/explain-decision", summary="Explain item decision")
def explain_decision_route(sku: str, db: Session = Depends(get_db)) -> dict:
    result = explain_decision_for_sku(db, sku)
    if result is None:
        raise HTTPException(status_code=404, detail=f"SKU '{sku}' not found")
    return result


@router.get(
    "/workflows/dead-stock-recommendation",
    summary="Run dead stock orchestration",
)
def dead_stock_recommendation_route(db: Session = Depends(get_db)) -> dict:
    return get_dead_stock_recommendation(db)
