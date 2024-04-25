from datamodel import Listing, Observation, Order, OrderDepth, ProsperityEncoder, Symbol, Trade, TradingState
from typing import Any, List
import json
import numpy as np
import math
import collections

INF = int(1e9)

pos_lim = {
    "STRAWBERRIES": 350,
    "CHOCOLATE": 250,
    "ROSES": 60,
    "GIFT_BASKET": 60,
    "STARFRUIT": 20,
    "ORCHIDS": 100,
    "AMETHYSTS": 20
}

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

class Trader:
    ## Initialize all instance variables
    starfruit_cache = []
    starfruit_dim = 4

    ## Calculate the next predicted price of startfruit using LR
    def calc_next_price_starfruit(self):
        # bananas cache stores price from 1 day ago, current day resp
        # by price, here we mean mid price

        coef = [0.19847666, 0.20319141, 0.25784436, 0.34024443]
        intercept = 1.22655515
        nxt_price = intercept
        for i, val in enumerate(self.starfruit_cache):
            nxt_price += val * coef[i]
        return int(round(nxt_price))

    ## Extract the best value
    def values_extract(self, order_dict, buy=0):
        tot_vol = 0
        best_val = -1
        mxvol = -1

        for ask, vol in order_dict.items():
            if (buy == 0):
                vol *= -1
            tot_vol += vol
            if tot_vol > mxvol:
                mxvol = vol
                best_val = ask

        return tot_vol, best_val

    ## Trading strategy for Amethysts
    def compute_order_amethysts(self, state: TradingState):

        ## Market taking
        product = "AMETHYSTS"
        order_depth: OrderDepth = state.order_depths[product]
        orders: List[Order] = []

        current_position = int(state.position.get(product, 0))
        buy_lim = 20 - current_position
        sell_lim = current_position + 20

        if len(order_depth.sell_orders) != 0:
            for ask, vol in list(order_depth.sell_orders.items()):
                if ((ask <= 9999) or ((current_position < 0) and (ask == 10000))) and buy_lim > 0:
                    amt = min(-vol, buy_lim)
                    buy_lim -= amt
                    orders.append(Order(product, ask, amt))

        if len(order_depth.buy_orders) != 0:
            for bid, vol in list(order_depth.buy_orders.items()):
                if ((bid >= 10001) or ((current_position > 0) and (bid == 10000))) and sell_lim > 0:
                    amt = max(-vol, -sell_lim)
                    sell_lim += amt
                    orders.append(Order(product, bid, amt))

        ## Market making
        best_ask, best_ask_vol = list(order_depth.sell_orders.items())[0]
        best_bid, best_bid_vol = list(order_depth.buy_orders.items())[0]

        undercut_sell = best_ask - 1
        undercut_buy = best_bid + 1

        bid_price = min(undercut_buy, 9999)
        ask_price = max(undercut_sell, 10001)

        if buy_lim > 0:
            orders.append(Order(product, bid_price, buy_lim))

        if sell_lim > 0:
            orders.append(Order(product, ask_price, -sell_lim))

        return orders

    ## Trading Strategy for Starfruit
    def compute_order_starfruit(self, state: TradingState):
        product = "STARFRUIT"
        order_depth: OrderDepth = state.order_depths[product]
        orders: List[Order] = []

        current_position = int(state.position.get(product, 0))
        buy_lim = 20 - current_position
        sell_lim = current_position + 20

        ## Calculate the acceptable bid and ask prices
        star_bid = -INF
        star_sell = INF
        if len(self.starfruit_cache) == self.starfruit_dim:
            star_bid = self.calc_next_price_starfruit() - 1
            star_sell = self.calc_next_price_starfruit() + 1

        ## Market Taking
        if len(order_depth.sell_orders) != 0:
            for ask, vol in list(order_depth.sell_orders.items()):
                if ((ask <= star_bid) or ((current_position < 0) and (ask == star_bid + 1))) and buy_lim > 0:
                    amt = min(-vol, buy_lim)
                    buy_lim -= amt
                    orders.append(Order(product, ask, amt))

        if len(order_depth.buy_orders) != 0:
            for bid, vol in list(order_depth.buy_orders.items()):
                if ((bid >= star_sell) or ((current_position > 0) and (bid == star_sell - 1))) and sell_lim > 0:
                    amt = max(-vol, -sell_lim)
                    sell_lim += amt
                    orders.append(Order(product, bid, amt))

        ## Market making
        best_ask, best_ask_vol = list(order_depth.sell_orders.items())[0]
        best_bid, best_bid_vol = list(order_depth.buy_orders.items())[0]

        undercut_sell = best_ask - 1
        undercut_buy = best_bid + 1

        bid_price = min(undercut_buy, star_bid)
        ask_price = max(undercut_sell, star_sell)

        if buy_lim > 0:
            orders.append(Order(product, bid_price, buy_lim))

        if sell_lim > 0:
            orders.append(Order(product, ask_price, -sell_lim))

        return orders

    def compute_order_orchid(self, state: TradingState):
        product = "ORCHIDS"
        order_depth: OrderDepth = state.order_depths[product]
        orders: List[Order] = []
        observation = state.observations.conversionObservations[product]

        south_bid = observation.bidPrice - observation.exportTariff - observation.transportFees - 0.1
        south_ask = observation.askPrice + observation.importTariff + observation.transportFees
        best_bid, best_bid_vol = list(order_depth.buy_orders.items())[0]
        best_ask, best_ask_vol = list(order_depth.sell_orders.items())[0]
        spread = best_ask - best_bid
        fixed = 30
        orders.append(Order(product, math.ceil(south_ask+1), -fixed))
        orders.append(Order(product, math.floor(south_bid-1), fixed))
        return orders

    def run(self, state: TradingState):
        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))

        result = {}
        conversions = 0

        ## Update Starfruit cache
        if len(self.starfruit_cache) == self.starfruit_dim:
            self.starfruit_cache.pop(0)

        _, bs_stars = self.values_extract(
            collections.OrderedDict(sorted(state.order_depths['STARFRUIT'].sell_orders.items())))
        _, bb_stars = self.values_extract(
            collections.OrderedDict(sorted(state.order_depths['STARFRUIT'].buy_orders.items(), reverse=True)), 1)

        self.starfruit_cache.append((bs_stars + bb_stars) / 2)

        # Main trading strategies
        for product in state.order_depths:

            if product == "AMETHYSTS":
                orders = self.compute_order_amethysts(state)
                result[product] = orders

            if product == "STARFRUIT":
                orders = self.compute_order_starfruit(state)
                result[product] = orders

            if product == "ORCHIDS":
                orders = self.compute_order_orchid(state)
                result[product] = orders
                current_position = int(state.position.get(product, 0))
                conversions = -current_position

        traderData = "TryCOCO"
        logger.flush(state, result, conversions, traderData)
        return result, conversions, traderData
