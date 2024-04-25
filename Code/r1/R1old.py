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

                if len(order_depth.sell_orders) > 0:
                    best_ask, best_ask_vol = list(order_depth.sell_orders.items())[0]
                    if int(best_ask) < 10000:
                        print("BUY", str(-best_ask_vol) + "x", best_ask)
                        orders.append(Order(product, best_ask, min(20, -best_ask_vol)))

                if len(order_depth.buy_orders) != 0:
                    best_bid, best_bid_vol = list(order_depth.buy_orders.items())[0]
                    if int(best_bid) > 10000:
                        print("SELL", str(best_bid_vol) + "x", best_bid)
                        orders.append(Order(product, best_bid, min(20, -best_bid_vol)))

                result[product] = orders

            if product == "STARFRUIT":
                current_position = state.position.get(product, 0)
                order_depth: OrderDepth = state.order_depths[product]
                orders: List[Order] = []

            if len(order_depth.sell_orders) > 0 and len(order_depth.buy_orders) > 0:
                w, v = 0, 0
                for price, vol in list(order_depth.buy_orders.items()):
                    if price is None or vol is None:
                        continue
                    w += int(price)* int(vol)
                    v += int(vol)
                weight_bid = w/v

                w, v = 0, 0
                for price, vol in list(order_depth.sell_orders.items()):
                    if price is None or vol is None:
                        continue
                    w += int(price) * int(vol)
                    v += int(vol)
                weight_ask = w/v

                best_bid, best_bid_vol = list(order_depth.buy_orders.items())[0]
                best_ask, best_ask_vol = list(order_depth.sell_orders.items())[0]
                vol_diff = best_ask_vol - best_bid_vol
                current_position = int(state.position.get(product, 0))
                fair_price = (weight_ask + weight_bid) / 2 - 0.1 * current_position - 0.01 * vol_diff

                if int(best_ask) < fair_price:
                    print("BUY", str(-best_ask_vol) + "x", best_ask)
                    orders.append(Order(product, best_ask, min(20, -best_ask_vol)))

                if int(best_bid) > fair_price:
                    print("SELL", str(best_bid_vol) + "x", best_bid)
                    orders.append(Order(product, best_bid, min(20, -best_bid_vol)))

                result[product] = orders
            # String value holding Trader state data required.
        # It will be delivered as TradingState.traderData on next execution.
        traderData = "TryCOCO"

        # Sample conversion request. Check more details below.
        conversions = 0
        return result, conversions, traderData
