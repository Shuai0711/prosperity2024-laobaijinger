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
        buy_lim = pos_lim["AMETHYSTS"] - current_position
        sell_lim = current_position + pos_lim["AMETHYSTS"]

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
        buy_lim = pos_lim["STARFRUIT"] - current_position
        sell_lim = current_position + pos_lim["STARFRUIT"]

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
        dynamic = 60+(8-spread)*5
        fix = 70
        orders.append(Order(product, math.ceil(south_ask+1), -fix))
        orders.append(Order(product, math.floor(south_bid-1), fix))
        return orders

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

    # weighted midprice calculator
    def calc_midprice(self, order_depth: OrderDepth):
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

    def run(self, state: TradingState):
        logger.print("traderData: " + state.traderData)
        logger.print("Observations: " + str(state.observations))

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

            if product == "GIFT_BASKET":
                basket_mu = 379.5
                mean_strawberry = self.calc_midprice(state.order_depths['STRAWBERRIES'])
                mean_chocolate = self.calc_midprice(state.order_depths['CHOCOLATE'])
                mean_roses = self.calc_midprice(state.order_depths['ROSES'])
                mean_basket = self.calc_midprice(state.order_depths['GIFT_BASKET'])

                combination_price = 6 * mean_strawberry + 4 * mean_chocolate + mean_roses + basket_mu
                margin = 38.2
                edge_max = 650
                edge = mean_basket - combination_price

                if mean_basket < combination_price - margin:
                    current_position = int(state.position.get('GIFT_BASKET', 0))
                    vol = 60 - current_position
                    worst_sell = list(reversed(list(state.order_depths['GIFT_BASKET'].sell_orders.items())))[0][0]
                    best_sell = list(state.order_depths['GIFT_BASKET'].sell_orders.items())[0][0]
                    if vol > 0:
                        result['GIFT_BASKET'] = [
                            Order('GIFT_BASKET', worst_sell, vol)]

                # if the basket's market price higher than the cost of its components: overvalued and we sell
                elif mean_basket > combination_price + margin:
                    current_position = int(state.position.get('GIFT_BASKET', 0))
                    vol = 60 + current_position
                    worst_buy = list(reversed(list(state.order_depths['GIFT_BASKET'].buy_orders.items())))[0][0]
                    best_buy = list(state.order_depths['GIFT_BASKET'].buy_orders.items())[0][0]
                    if vol > 0:
                        result['GIFT_BASKET'] = [
                            Order('GIFT_BASKET', worst_buy, -vol)]

                # combination_price = 6 * mean_strawberry + 4 * mean_chocolate + mean_roses + basket_mu
                # margin = 30
                # edge_max = 650
                # edge = mean_basket - combination_price
                #
                # if mean_basket < combination_price - margin:
                #     best_ask_basket = list(state.order_depths['GIFT_BASKET'].sell_orders.items())[0][0]
                #     result['GIFT_BASKET'] = [Order('GIFT_BASKET', best_ask_basket, buy_basket_multiplier)]
                #
                # elif mean_basket > combination_price + margin:
                #     best_bid_basket = list(state.order_depths['GIFT_BASKET'].buy_orders.items())[0][0]
                #     result['GIFT_BASKET'] = [Order('GIFT_BASKET', best_bid_basket, -sell_basket_multiplier)]

        traderData = "COCO_WITHOUT_NUTS"
        logger.flush(state, result, conversions, traderData)

        return result, conversions, traderData
