from fastapi import APIRouter, Response, status

from context import HttpResponseContext
from manual_backtest import run_manual_backtest
from request_types import BodyCreateManualBacktest


router = APIRouter()


class RoutePaths:
    BACKTEST = "/"


@router.post(RoutePaths.BACKTEST)
async def route_create_manual_backtest(body: BodyCreateManualBacktest):
    with HttpResponseContext():
        backtest = run_manual_backtest(body)
        return {"data": backtest}
