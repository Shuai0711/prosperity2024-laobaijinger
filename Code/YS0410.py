from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import string
import numpy as np


class Trader:
    def run(self, state: TradingState):
        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))

        def mean_price(prod):
            if prod == 'AMETHYSTS':
                return 10000
            if prod == 'STARFRUIT':
                return 5000

        result = {}
        for product in state.order_depths:
            if product == "AMETHYSTS":
                current_position = state.position.get(product,0)
                order_depth: OrderDepth = state.order_depths[product]
                orders: List[Order] = []

                if len(order_depth.sell_orders) > 0:
                    best_ask, best_ask_vol = list(order_depth.sell_orders.items())[0]
                    if int(best_ask) < mean_price(product):
                        print("BUY", str(-best_ask_vol) + "x", best_ask)
                        orders.append(Order(product, best_ask, min(20, -best_ask_vol)))

                if len(order_depth.buy_orders) != 0:
                    best_bid, best_bid_vol = list(order_depth.buy_orders.items())[0]
                    if int(best_bid) > mean_price(product):
                        print("SELL", str(best_bid_vol) + "x", best_bid)
                        orders.append(Order(product, best_bid, min(20, -best_bid_vol)))

                result[product] = orders

            # String value holding Trader state data required.
        # It will be delivered as TradingState.traderData on next execution.
        traderData = "TryCOCO"

        # Sample conversion request. Check more details below.
        conversions = 0
        return result, conversions, traderData
