import numpy as np
import json
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


class Trader:
    def find_max_multiplier(self, state:TradingState):
        position = {} # dict that tracks 
        orderdepth = state.order_depths

        # position: Dict[Product, Position]
        for product in ['STRAWBERRIES', 'CHOCOLATE', 'ROSES', 'GIFT_BASKET']:
            position[product] = state.position[product] if product in state.position else 0
        # retrieves trader's current position at each product recursively. 
        # If a product isn't found in the trader’s inventory, it is set to 0

        # quantity available to sell from the market, min() used to comply with inventory constraints
        straw_ask_volume = min(-list(orderdepth["STRAWBERRIES"].sell_orders.values())[0],
                               350 - position['STRAWBERRIES'], 350)
        chocolate_ask_volume = min(-list(orderdepth["CHOCOLATE"].sell_orders.values())[0], 250 - position['CHOCOLATE'],
                                   250)
        roses_ask_volume = min(-list(orderdepth["ROSES"].sell_orders.values())[0], 60 - position['ROSES'], 60)
        basket_ask_volume = min(-list(orderdepth["GIFT_BASKET"].sell_orders.values())[0], 60 - position['GIFT_BASKET'],
                                60)

        straw_bid_volume = min(list(orderdepth["STRAWBERRIES"].buy_orders.values())[0], 350 + position['STRAWBERRIES'],
                               350)
        chocolate_bid_volume = min(list(orderdepth["CHOCOLATE"].buy_orders.values())[0], 250 + position['CHOCOLATE'],
                                   250)
        roses_bid_volume = min(list(orderdepth["ROSES"].buy_orders.values())[0], 60 + position['ROSES'], 60)
        basket_bid_volume = min(list(orderdepth["GIFT_BASKET"].buy_orders.values())[0], 60 + position['GIFT_BASKET'],
                                60)
        
        # Determines how many basket can we sell 
        sell_basket_multiplier = int(
            np.floor(min(straw_ask_volume / 6, chocolate_ask_volume / 4, roses_ask_volume, basket_bid_volume)))
        # Determines how many basket can we buy 
        buy_basket_multiplier = int(
            np.floor(min(straw_bid_volume / 6, chocolate_bid_volume / 4, roses_bid_volume, basket_ask_volume)))

        return (buy_basket_multiplier, sell_basket_multiplier)

    # averages the best available bid and ask prices
    def calc_midprice(self, order_depth: OrderDepth):
        if len(list(order_depth.sell_orders.values())) > 0 and len(list(order_depth.buy_orders.values())) > 0:
            best_ask, best_ask_vol = list(order_depth.sell_orders.items())[0]
            best_bid, best_bid_vol = list(order_depth.buy_orders.items())[0]
            return (best_ask + best_bid) / 2
        else:
            return 0


    def run(self, state: TradingState):
        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))

        result = {}

        basket_price = 379.5 # fixed basket reference price 
        # get the average of the best available bid and ask prices for each products
        straw = self.calc_midprice(state.order_depths['STRAWBERRIES'])
        choco = self.calc_midprice(state.order_depths['CHOCOLATE'])
        roses = self.calc_midprice(state.order_depths['ROSES'])
        basket = self.calc_midprice(state.order_depths['GIFT_BASKET'])

        # Uses find_max_multiplier to calculate how many units of the gift basket can be bought or sold 
        # under the current market conditions.
        buy_basket_multiplier, sell_basket_multiplier = self.find_max_multiplier(state)
        print(buy_basket_multiplier, sell_basket_multiplier)
        # buy_basket_multiplier, sell_basket_multiplier = min(buy_basket_multiplier, 2), min(sell_basket_multiplier, 2)
        
        # difference between basket price and assembled basket price
        gap = basket - (6 * straw + 4 * choco + roses + basket_price)
        margin = 38.2 # tolearance for the price gap, should be adjusted to achieve higher profit

        # if the basket's market price lower than the cost of its components: undervalued and we buy
        if basket < 6 * straw + 4 * choco + roses + basket_price - margin:
            current_position = int(state.position.get('GIFT_BASKET', 0))
            vol = 60 - current_position
            worst_sell = list(reversed(list(state.order_depths['GIFT_BASKET'].sell_orders.items())))[0][0]
            best_sell = list(state.order_depths['GIFT_BASKET'].sell_orders.items())[0][0]
            if vol > 0:
                logger.print(f"GIFT_BASKET, {worst_sell}x{vol}")
                result['GIFT_BASKET'] = [
                Order('GIFT_BASKET', worst_sell, vol)]
        
        # if the basket's market price higher than the cost of its components: overvalued and we sell
        elif basket > 6 * straw + 4 * choco + roses + basket_price + margin:
            current_position = int(state.position.get('GIFT_BASKET', 0))
            vol = 60 + current_position
            worst_buy = list(reversed(list(state.order_depths['GIFT_BASKET'].buy_orders.items())))[0][0]
            best_buy = list(state.order_depths['GIFT_BASKET'].buy_orders.items())[0][0]
            if vol > 0:
                logger.print(f"GIFT_BASKET, {worst_buy}x-{vol}")
                result['GIFT_BASKET'] = [
                Order('GIFT_BASKET', worst_buy, -vol)]

        traderData = "TryCOCO"

        # Sample conversion request. Check more details below.
        conversions = 0
        logger.flush(state, result, conversions, traderData)
        return result, conversions, traderData
