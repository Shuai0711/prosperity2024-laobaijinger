import numpy as np
import json
from typing import Dict, List
from datamodel import Listing, Observation, Order, OrderDepth, ProsperityEncoder, Symbol, Trade, TradingState
from typing import Any

class Logger:
    def __init__(self) -> None:
        self.logs = ""
        self.max_log_length = 3750

    def print(self, *objects: Any, sep: str = " ", end: str = "\n") -> None:
        self.logs += sep.join(map(str, objects)) + end

    def flush(self, state: TradingState, orders: dict[Symbol, list[Order]], conversions: int, trader_data: str) -> None:
        base_length = len(self.to_json([
            self.compress_state(state, ""),
            self.compress_orders(orders),
            conversions,
            "",
            "",
        ]))

        # We truncate state.traderData, trader_data, and self.logs to the same max. length to fit the log limit
        max_item_length = (self.max_log_length - base_length) // 3

        print(self.to_json([
            self.compress_state(state, self.truncate(state.traderData, max_item_length)),
            self.compress_orders(orders),
            conversions,
            self.truncate(trader_data, max_item_length),
            self.truncate(self.logs, max_item_length),
        ]))

        self.logs = ""

    def compress_state(self, state: TradingState, trader_data: str) -> list[Any]:
        return [
            state.timestamp,
            trader_data,
            self.compress_listings(state.listings),
            self.compress_order_depths(state.order_depths),
            self.compress_trades(state.own_trades),
            self.compress_trades(state.market_trades),
            state.position,
            self.compress_observations(state.observations),
        ]

    def compress_listings(self, listings: dict[Symbol, Listing]) -> list[list[Any]]:
        compressed = []
        for listing in listings.values():
            compressed.append([listing["symbol"], listing["product"], listing["denomination"]])

        return compressed

    def compress_order_depths(self, order_depths: dict[Symbol, OrderDepth]) -> dict[Symbol, list[Any]]:
        compressed = {}
        for symbol, order_depth in order_depths.items():
            compressed[symbol] = [order_depth.buy_orders, order_depth.sell_orders]

        return compressed

    def compress_trades(self, trades: dict[Symbol, list[Trade]]) -> list[list[Any]]:
        compressed = []
        for arr in trades.values():
            for trade in arr:
                compressed.append([
                    trade.symbol,
                    trade.price,
                    trade.quantity,
                    trade.buyer,
                    trade.seller,
                    trade.timestamp,
                ])

        return compressed

    def compress_observations(self, observations: Observation) -> list[Any]:
        conversion_observations = {}
        for product, observation in observations.conversionObservations.items():
            conversion_observations[product] = [
                observation.bidPrice,
                observation.askPrice,
                observation.transportFees,
                observation.exportTariff,
                observation.importTariff,
                observation.sunlight,
                observation.humidity,
            ]

        return [observations.plainValueObservations, conversion_observations]

    def compress_orders(self, orders: dict[Symbol, list[Order]]) -> list[list[Any]]:
        compressed = []
        for arr in orders.values():
            for order in arr:
                compressed.append([order.symbol, order.price, order.quantity])

        return compressed

    def to_json(self, value: Any) -> str:
        return json.dumps(value, cls=ProsperityEncoder, separators=(",", ":"))

    def truncate(self, value: str, max_length: int) -> str:
        if len(value) <= max_length:
            return value

        return value[:max_length - 3] + "..."

logger = Logger()


pos_lim = {
    "STRAWBERRIES": 350,
    "CHOCOLATE": 250,
    "ROSES": 60,
    "GIFT_BASKET": 60,
    "STARFRUIT": 20,
    "ORCHIDS": 100,
    "AMETHYSTS": 20
}

class Trader:
    def find_max_multiplier_ys(self, state: TradingState):
        order_depth = state.order_depths
        position_dict = {}
        ask_volumn_dict = {}
        bid_volumn_dict = {}

        for product in ['STRAWBERRIES', 'CHOCOLATE', 'ROSES', 'GIFT_BASKET']:
            position_dict[product] = state.position.get(product, 0)
            lim = pos_lim[product]
            ask_volumn_dict[product] = min(-list(order_depth[product].sell_orders.values())[0], lim - position_dict[product], lim)
            bid_volumn_dict[product] = min(list(order_depth[product].buy_orders.values())[0], lim + position_dict[product], lim)

        sell_basket_multiplier = int(np.floor(min(ask_volumn_dict["STRAWBERRIES"] / 6, ask_volumn_dict["CHOCOLATE"] / 4, ask_volumn_dict["ROSES"], bid_volumn_dict["GIFT_BASKET"])))
        buy_basket_multiplier = int(np.floor(min(bid_volumn_dict["STRAWBERRIES"] / 6, bid_volumn_dict["CHOCOLATE"] / 4, bid_volumn_dict["ROSES"], ask_volumn_dict["GIFT_BASKET"])))

        return buy_basket_multiplier, sell_basket_multiplier

    def calc_weighted_midprice(self, order_depth: OrderDepth):
        price = 0
        vol = 0
        if len(list(order_depth.sell_orders.items())) > 0 and len(list(order_depth.buy_orders.items())) > 0:
            for p, v in order_depth.sell_orders.items():
                price += abs(p*v)
                vol += abs(v)
            for p, v in order_depth.buy_orders.items():
                price += abs(p*v)
                vol += abs(v)
            return price/vol
        else:
            return 0

    def compute_order_basket(self, state: TradingState):
        res = {}
        basket_mu = 379.5
        mean_strawberry = self.calc_weighted_midprice(state.order_depths['STRAWBERRIES'])
        mean_chocolate = self.calc_weighted_midprice(state.order_depths['CHOCOLATE'])
        mean_roses = self.calc_weighted_midprice(state.order_depths['ROSES'])
        mean_basket = self.calc_weighted_midprice(state.order_depths['GIFT_BASKET'])

        buy_basket_multiplier, sell_basket_multiplier = self.find_max_multiplier_ys(state)
        print(buy_basket_multiplier, sell_basket_multiplier)

        combination_price = 6 * mean_strawberry + 4 * mean_chocolate + mean_roses + basket_mu
        margin = 38

        if mean_basket < combination_price - margin:
            best_ask_basket = list(state.order_depths['GIFT_BASKET'].sell_orders.items())[0][0]
            best_bid_chocolate = list(state.order_depths['CHOCOLATE'].buy_orders.items())[0][0]
            best_bid_roses = list(state.order_depths['ROSES'].buy_orders.items())[0][0]
            best_bid_strawberry = list(state.order_depths['STRAWBERRIES'].buy_orders.items())[0][0]

            res["GIFT_BASKET"] = [Order('GIFT_BASKET', best_ask_basket, buy_basket_multiplier)]
            res["CHOCOLATE"] = [Order('CHOCOLATE', best_bid_chocolate, -4 * buy_basket_multiplier)]
            res["ROSES"] = [Order('ROSES', best_bid_roses, -1 * buy_basket_multiplier)]
            res["STRAWBERRIES"] = [Order('STRAWBERRIES', best_bid_strawberry, -6 * buy_basket_multiplier)]

        elif mean_basket > combination_price + margin:
            best_bid_basket = list(state.order_depths['GIFT_BASKET'].buy_orders.items())[0][0]
            best_ask_chocolate = list(state.order_depths['CHOCOLATE'].sell_orders.items())[0][0]
            best_ask_roses = list(state.order_depths['ROSES'].sell_orders.items())[0][0]
            best_ask_straberry = list(state.order_depths['STRAWBERRIES'].sell_orders.items())[0][0]

            res["GIFT_BASKET"] = [Order('GIFT_BASKET', best_bid_basket, -sell_basket_multiplier)]
            res["STRAWBERRIES"] = [Order('STRAWBERRIES', best_ask_straberry, 6 * sell_basket_multiplier)]
            res["ROSES"] = [Order('ROSES', best_ask_roses, 1 * sell_basket_multiplier)]
            res["CHOCOLATE"] = [Order('CHOCOLATE', best_ask_chocolate, 4 * sell_basket_multiplier)]

        return res


    def run(self, state: TradingState):
        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))
        result = {}
        for product in state.order_depths:
            if product in ["STRAWBERRIES", "CHOCOLATE", "ROSES", "GIFT_BASKET"]:
                orders = self.compute_order_basket(state)
                if len(orders) > 0:
                    for item in list(orders.keys()):
                        result[item] = orders[item]
                break

        traderData = "TryCOCO"

        # Sample conversion request. Check more details below.
        conversions = 0
        logger.flush(state, result, conversions, traderData)
        return result, conversions, traderData
