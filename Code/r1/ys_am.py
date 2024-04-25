from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import string
import numpy as np


class Trader:
    def run(self, state: TradingState):
        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))

        result = {}
        for product in state.order_depths:
            if product == "AMETHYSTS":
                order_depth: OrderDepth = state.order_depths[product]
                orders: List[Order] = []

                current_position = int(state.position.get(product, 0))
                buy_lim = 20 - current_position
                sell_lim = current_position + 20
                mid_price = 10000

                if len(order_depth.sell_orders) > 0:
                    best_ask, best_ask_vol = list(order_depth.sell_orders.items())[0]
                    if int(best_ask) < 10000:
                        print("BUY", str(-best_ask_vol) + "x", best_ask)
                        amt = min(buy_lim , -best_ask_vol)
                        orders.append(Order(product, best_ask, amt))
                        buy_lim = buy_lim - amt

                if len(order_depth.buy_orders) != 0:
                    best_bid, best_bid_vol = list(order_depth.buy_orders.items())[0]
                    if int(best_bid) > 10000:
                        print("SELL", str(best_bid_vol) + "x", best_bid)
                        amt = min(sell_lim, best_bid_vol)
                        orders.append(Order(product, best_bid, -amt))
                        sell_lim = sell_lim - amt

                if buy_lim > 0:
                    orders.append(Order(product, 9999, buy_lim))
                if sell_lim > 0:
                    orders.append(Order(product, 10001, -sell_lim))

                result[product] = orders
            # String value holding Trader state data required.
        # It will be delivered as TradingState.traderData on next execution.
        traderData = "TryCOCO"

        # Sample conversion request. Check more details below.
        conversions = 0
        return result, conversions, traderData