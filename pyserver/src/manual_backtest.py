import json
from typing import Dict, List
from backtest_utils import (
    find_max_drawdown,
    get_backtest_profit_factor_comp,
    get_backtest_trade_details,
)
from code_gen_template import BACKTEST_MANUAL_TEMPLATE
from dataset import read_dataset_to_mem
from log import LogExceptionContext
from model_backtest import Positions
from query_backtest import BacktestQuery
from query_dataset import DatasetQuery
from query_trade import TradeQuery
from request_types import BodyCreateManualBacktest


START_BALANCE = 10000


def run_manual_backtest(backtestInfo: BodyCreateManualBacktest):
    with LogExceptionContext():
        dataset = DatasetQuery.fetch_dataset_by_id(backtestInfo.dataset_id)
        dataset_df = read_dataset_to_mem(dataset.dataset_name)

        replacements = {
            "{OPEN_LONG_TRADE_FUNC}": backtestInfo.open_long_trade_cond,
            "{OPEN_SHORT_TRADE_FUNC}": backtestInfo.open_short_trade_cond,
            "{CLOSE_LONG_TRADE_FUNC}": backtestInfo.close_long_trade_cond,
            "{CLOSE_SHORT_TRADE_FUNC}": backtestInfo.close_short_trade_cond,
        }

        backtest = ManualBacktest(
            START_BALANCE,
            backtestInfo.trading_fees_perc,
            backtestInfo.slippage_perc,
            replacements,
            backtestInfo.use_short_selling,
            backtestInfo.use_time_based_close,
            backtestInfo.klines_until_close if backtestInfo.klines_until_close else -1,
        )

        assert (
            dataset.timeseries_column is not None
        ), "Timeseries column has not been set"
        assert dataset.price_column is not None, "Price column has not been set"

        asset_starting_price = None
        asset_closing_price = None

        for i, row in dataset_df.iterrows():
            is_last_row = i == len(dataset_df) - 1
            backtest.process_df_row(
                row, dataset.price_column, dataset.timeseries_column, is_last_row
            )

            if i == 0:
                asset_starting_price = row[dataset.price_column]
            if is_last_row:
                asset_closing_price = row[dataset.price_column]

        end_balance = backtest.positions.total_positions_value

        profit_factor, gross_profit, gross_loss = get_backtest_profit_factor_comp(
            backtest.positions.trades
        )
        (
            share_of_winning_trades_perc,
            share_of_losing_trades_perc,
            best_trade_result_perc,
            worst_trade_result_perc,
        ) = get_backtest_trade_details(backtest.positions.trades)

        max_drawdown_perc = find_max_drawdown(backtest.positions.balance_history)

        backtest_id = BacktestQuery.create_entry(
            {
                "open_long_trade_cond": backtestInfo.open_long_trade_cond,
                "open_short_trade_cond": backtestInfo.open_short_trade_cond,
                "close_long_trade_cond": backtestInfo.close_long_trade_cond,
                "close_short_trade_cond": backtestInfo.close_short_trade_cond,
                "data": json.dumps(backtest.positions.balance_history),
                "dataset_id": dataset.id,
                "start_balance": START_BALANCE,
                "end_balance": end_balance,
                "profit_factor": profit_factor,
                "gross_profit": gross_profit,
                "gross_loss": gross_loss,
                "trade_count": len(backtest.positions.trades),
                "name": backtestInfo.name,
                "klines_until_close": backtestInfo.klines_until_close,
                "result_perc": (end_balance / START_BALANCE - 1) * 100,
                "share_of_winning_trades_perc": share_of_winning_trades_perc,
                "share_of_losing_trades_perc": share_of_losing_trades_perc,
                "best_trade_result_perc": best_trade_result_perc,
                "worst_trade_result_perc": worst_trade_result_perc,
                "buy_and_hold_result_net": (
                    (asset_closing_price / asset_starting_price * START_BALANCE)
                    - START_BALANCE
                )
                if asset_starting_price is not None and asset_closing_price is not None
                else None,
                "buy_and_hold_result_perc": (
                    (asset_closing_price / asset_starting_price - 1) * 100
                )
                if asset_starting_price is not None and asset_closing_price is not None
                else None,
                "max_drawdown_perc": max_drawdown_perc,
            }
        )

        backtest_from_db = BacktestQuery.fetch_backtest_by_id(backtest_id)
        TradeQuery.create_many_trade_entry(backtest_id, backtest.positions.trades)

        return backtest_from_db


class ManualBacktest:
    def __init__(
        self,
        start_balance: float,
        fees_perc: float,
        slippage_perc: float,
        enter_and_exit_criteria_placeholders: Dict,
        use_short_selling: bool,
        use_time_based_close: bool,
        max_klines_until_close: int,
    ) -> None:
        self.enter_and_exit_criteria_placeholders = enter_and_exit_criteria_placeholders
        self.positions = Positions(
            start_balance, 1 - (fees_perc / 100), 1 - (slippage_perc / 100)
        )
        self.history: List = []
        self.use_short_selling = use_short_selling
        self.use_time_based_close = use_time_based_close
        self.max_klines_until_close = max_klines_until_close
        self.pos_open_klines = 0

    def process_df_row(self, df_row, price_col, timeseries_col, is_last_row):
        code = BACKTEST_MANUAL_TEMPLATE
        for key, value in self.enter_and_exit_criteria_placeholders.items():
            code = code.replace(key, str(value))

        results_dict = {"df_row": df_row}
        exec(code, globals(), results_dict)

        ## Force close trades on last row to make accounting easier
        should_open_long = (
            results_dict["should_open_long"] if is_last_row is False else False
        )
        should_open_short = (
            results_dict["should_open_short"] if is_last_row is False else False
        )
        should_close_long = (
            results_dict["should_close_long"] if is_last_row is False else True
        )
        should_close_short = (
            results_dict["should_close_short"] if is_last_row is False else True
        )

        kline_open_time = df_row[timeseries_col]
        price = df_row[price_col]

        if (
            self.pos_open_klines == self.max_klines_until_close
            and self.use_time_based_close
        ):
            # auto close positions if time threshold is met
            should_close_short = True
            should_close_long = True

        self.tick(
            price,
            kline_open_time,
            should_open_long,
            should_open_short,
            should_close_long,
            should_close_short,
        )

    def close_trade_cleanup(self):
        self.pos_open_klines = 0

    def update_data(self, price: float, kline_open_time: int):
        self.positions.update_balance(price, 0, kline_open_time)
        self.pos_open_klines += 1

    def tick(
        self,
        price: float,
        kline_open_time: int,
        should_long: bool,
        should_short: bool,
        should_close_long: bool,
        should_close_short: bool,
    ):
        self.update_data(price, kline_open_time)

        if self.positions.position > 0 and should_close_long:
            self.positions.close_long(price, kline_open_time)

        if (
            self.positions.short_debt > 0
            and should_close_short is True
            and self.use_short_selling is True
        ):
            self.positions.close_short(price, kline_open_time)
            self.close_trade_cleanup()

        if self.positions.cash > 0 and should_long:
            self.positions.go_long(price, 0, kline_open_time)
            self.close_trade_cleanup()

        if (
            self.positions.short_debt == 0
            and should_short is True
            and self.use_short_selling is True
        ):
            self.positions.go_short(price, 0, kline_open_time)
