import datetime
import math
import time

from db.orm import update_trade_process, get_trade_process_by_id
from db.config import Session
from services.config import PositionType, TraderType
from pybit import unified_trading


class TradeProcessor:
    def __init__(
        self,
        id: str,
        symbol: str,
        type: str,
        capital: float,
        leverage: int,
        upper_bound: float,
        lower_bound: float,
        grid_count: int,
        db_session: Session,
        broker_session: unified_trading.HTTP,
    ):
        self._symbol = symbol

        self._type = TraderType.LONG_ONLY if type == "LONG" else TraderType.SHORT_ONLY

        self._capital = capital
        self._leverage = leverage
        self._price_step = None
        self._placed_orders_counter = 3
        self._upper_bound = upper_bound
        self._lower_bound = lower_bound
        self._grid_count = grid_count
        self._orders_count = 3
        self._last_check = 0
        self._grid_levels = None
        self._grid_position_size = None
        self._id = id
        self._session = db_session
        self._broker_session = broker_session
        self._direct_orders = {}
        self._reverse_orders = {}

        self._grid_pnl = 0

        self._set_up()

    def _set_up(self) -> None:
        self._grid_levels = dict(enumerate(self._construct_grid_levels()))

    def _construct_grid_levels(self) -> list[float]:
        size_step, price_step = self._get_symbol_info()

        diff = self._upper_bound - self._lower_bound
        grid_step = diff / self._grid_count

        init_grid_level = self._construnct_price(self._lower_bound, price_step)
        grid_levels = [init_grid_level]

        self._grid_position_size = self._construct_size(
            self._capital, init_grid_level, size_step
        )

        for _ in range(self._grid_count):
            grid_levels.append(
                self._construnct_price(grid_levels[-1] + grid_step, price_step)
            )

        return grid_levels

    def _get_symbol_info(self):
        try:
            symbol_info = self._broker_session.get_instruments_info(
                category="linear",
                symbol=self._symbol,
            )["result"]["list"][0]
            return float(symbol_info["lotSizeFilter"]["qtyStep"]), float(
                symbol_info["priceFilter"]["tickSize"]
            )
        except:
            raise Exception("_get_symbol_info")

    def _construnct_price(self, price: float, price_step: float):
        return round(price, int(-1 * round(math.log10(price_step))))

    def _get_last_traded_price(self) -> float:
        try:
            response = self._broker_session.get_tickers(
                category="linear", symbol=self._symbol
            )
            return float(response["result"]["list"][0]["lastPrice"])
        except:
            raise Exception("_get_last_traded_price")

    def _construct_size(self, capital: float, price: float, size_step: float) -> float:
        size = capital / price
        return round(size, int(-1 * round(math.log10(size_step))))

    def _place_order(self, price: float, side: str) -> str:
        try:
            resp = self._broker_session.place_order(
                category="linear",
                symbol=self._symbol,
                side=side.value,
                orderType="Limit",
                price=price,
                qty=self._grid_position_size,
                isLeverage=1,
                positionIdx=0,
            )
            return resp["result"]["orderId"]
        except:
            import traceback
            traceback.print_exc()
            raise Exception("_place_order")

    def _get_order_status(self, order_id) -> bool:
        try:
            resp = self._broker_session.get_order_history(
                category="linear",
                symbol=self._symbol,
                orderId=order_id,
            )

            return (
                resp.get("result", {}).get("list", [])
                and resp["result"]["list"][0]["orderStatus"] == "Filled"
            )
        except:
            raise Exception("_get_order_status")

    def _get_price_position(self, current_price) -> tuple[int, int]:
        sorted_levels = sorted(self._grid_levels.items(), key=lambda x: x[1])
        level1 = level2 = -1

        for i in range(len(sorted_levels) - 1):
            level1, price1 = sorted_levels[i]
            level2, price2 = sorted_levels[i + 1]

            if price1 <= current_price < price2:
                break

        return level1, level2

    def _complete(self) -> bool:
        try:
            target_trade_process = get_trade_process_by_id(self._session, self._id)
            if target_trade_process.completed_at:
                pending_orders = self._get_pending_orders(target_trade_process.symbol)
                self._cancel_pending_orders(pending_orders, target_trade_process.symbol)
                existing_position_info = self._get_existing_position_info(target_trade_process.symbol)
                self._close_position(existing_position_info)
                return True
        except:
            pass

        return False

    def _close_position(self, existing_position: dict) -> None:
        if float(existing_position['size']) != 0.0:
            self._broker_session.place_order(
                category="linear",
                symbol=existing_position['symbol'],
                side='Sell' if existing_position['side'] == 'Buy' else 'Buy',
                orderType="Market",
                qty=existing_position['size'],
                isLeverage=1,
            )

    def _get_existing_position_info(self, symbol) -> dict:
        response = self._broker_session.get_positions(category="linear", symbol=symbol)[
            "result"
        ]["list"]

        if response:
            return response[0]
        else:
            return {}

    def _cancel_pending_orders(self, pending_orders: list, symbol: str) -> None:
        for pending_order in pending_orders:
            try:
                self._broker_session.cancel_order(
                    category="linear",
                    symbol=symbol,
                    orderId=pending_order["orderId"],
                )
            except Exception:
                continue

    def _get_pending_orders(self, symbol: str) -> list:
        response = self._broker_session.get_open_orders(
            category="linear",
            symbol=symbol,
            openOnly=0,
            limit=100,
        )["result"]["list"]

        if response:
            return response
        else:
            return []

    def perform(self) -> None:
        while not self._complete():
            try:
                self._subperform()
            except Exception as e:
                print(e)
                continue
            time.sleep(2)

    def _subperform(self) -> None:
        last_price = self._get_last_traded_price()
        level1, level2 = self._get_price_position(last_price)

        directional_check = 0
        if (level1 > self._last_check and self._type == TraderType.SHORT_ONLY) or (
            level1 < self._last_check and self._type == TraderType.LONG_ONLY
        ):
            directional_check = 1
        elif (level1 < self._last_check and self._type == TraderType.SHORT_ONLY) or (
            level1 > self._last_check and self._type == TraderType.LONG_ONLY
        ):
            directional_check = 2

        self._last_check = level1

        if self._type == TraderType.LONG_ONLY:
            target_grid_levels = set(
                [level for level in range(level1 - self._orders_count, level1)]
            )
        else:
            target_grid_levels = set(
                [level for level in range(level2 + 1, level2 + self._orders_count + 1)]
            )

        taken_levels = set(self._direct_orders.keys())
        pending_levels = target_grid_levels - taken_levels
        taken_levels = list(taken_levels)
        if self._type == TraderType.LONG_ONLY:
            levels_to_cancel = sorted(taken_levels)[: -self._orders_count]
        else:
            levels_to_cancel = sorted(taken_levels)[self._orders_count :]

        positions_side = (
            PositionType.BUY
            if self._type == TraderType.LONG_ONLY
            else PositionType.SELL
        )

        close_positions_side = (
            PositionType.BUY
            if self._type == TraderType.SHORT_ONLY
            else PositionType.SELL
        )

        for pending_level in pending_levels:
            order_id = self._place_order(
                self._grid_levels[pending_level], positions_side
            )
            self._direct_orders[pending_level] = order_id

        filled_levels = set()
        for taken_level in taken_levels:
            if self._get_order_status(self._direct_orders[taken_level]):
                close_positions_grid_level = (
                    taken_level + 1
                    if self._type == TraderType.LONG_ONLY
                    else taken_level - 1
                )

                filled_levels.add(taken_level)

                reverse_position_id = self._place_order(
                    self._grid_levels[close_positions_grid_level], close_positions_side
                )
                self._reverse_orders[reverse_position_id] = (
                    taken_level,
                    close_positions_grid_level,
                )
                del self._direct_orders[taken_level]

        levels_to_cancel = set(levels_to_cancel) - filled_levels
        levels_to_cancel = levels_to_cancel - pending_levels

        if directional_check == 2:
            for level_to_cancel in levels_to_cancel:
                try:
                    self._broker_session.cancel_order(
                        category="linear",
                        symbol=self._symbol,
                        orderId=self._direct_orders[level_to_cancel],
                    )
                except:
                    raise Exception("cancel_order")
                del self._direct_orders[level_to_cancel]

        self._trace_revert_orders()

        unclosed_margin = self._calculate_unclosed_margin(last_price)

        stats = {
            "unclosed_pnl": unclosed_margin,
            "closed_pnl": self._grid_pnl,
            "total_pnl": round(unclosed_margin + self._grid_pnl, 3),
        }
        if datetime.datetime.now().minute % 5 == 0:
            self._save_stat(stats)

    def _save_stat(self, stat: dict) -> None:
        stat.update({"updated_at": datetime.datetime.now()})
        update_trade_process(self._session, self._id, **stat)

    def _trace_revert_orders(self) -> None:
        reverse_order_ids = list(self._reverse_orders.keys())
        for reverse_order_id in reverse_order_ids:
            status = self._get_order_status(reverse_order_id)
            if status:
                self._grid_pnl += (
                    abs(
                        self._grid_levels[self._reverse_orders[reverse_order_id][1]]
                        - self._grid_levels[self._reverse_orders[reverse_order_id][0]]
                    )
                    * self._grid_position_size
                ) * 0.999
                del self._reverse_orders[reverse_order_id]

    def _calculate_unclosed_margin(self, last_price) -> float:
        if self._type == TraderType.LONG_ONLY:
            margins = [
                last_price - self._grid_levels[self._reverse_orders[key][0]]
                for key in self._reverse_orders.keys()
            ]
        else:
            margins = [
                self._grid_levels[self._reverse_orders[key][0]] - last_price
                for key in self._reverse_orders.keys()
            ]

        return sum(margins) * self._grid_position_size * 0.999
