from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import string
import numpy as np
import collections

INF = int(1e9)

class Trader:
    starfruit_cache = []
    starfruit_dim = 4

    def calc_next_price_star(self):
        # bananas cache stores price from 1 day ago, current day resp
        # by price, here we mean mid price

        coef = [0.19847666, 0.20319141, 0.25784436, 0.34024443]
        intercept = 1.22655515
        nxt_price = intercept
        for i, val in enumerate(self.starfruit_cache):
            nxt_price += val * coef[i]
        return int(round(nxt_price))

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

    def run(self, state: TradingState):
        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))

        result = {}

        if len(self.starfruit_cache) == self.starfruit_dim:
            self.starfruit_cache.pop(0)
        _, bs_stars = self.values_extract(
            collections.OrderedDict(sorted(state.order_depths['STARFRUIT'].sell_orders.items())))
        _, bb_stars = self.values_extract(
            collections.OrderedDict(sorted(state.order_depths['STARFRUIT'].buy_orders.items(), reverse=True)), 1)

        self.starfruit_cache.append((bs_stars + bb_stars) / 2)
        star_lb = -INF
        star_ub = INF

        if len(self.starfruit_cache) == self.starfruit_dim:
            star_lb = self.calc_next_price_star() - 1
            star_ub = self.calc_next_price_star() + 1

        for product in state.order_depths:
            if product == "STARFRUIT":
                order_depth: OrderDepth = state.order_depths[product]
                orders: List[Order] = []

                if len(order_depth.sell_orders) > 0 and len(order_depth.buy_orders) > 0:
                    w, v = 0, 0
                    for price, vol in list(order_depth.buy_orders.items()):
                        if price is None or vol is None:
                            continue
                        w += int(price) * int(vol)
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
                    fair_price = (weight_ask + weight_bid)/2 - 0.07 * current_position - 0.01 * vol_diff

                    if int(best_ask) < max(fair_price, star_lb):
                        print("BUY", str(-best_ask_vol) + "x", best_ask)
                        orders.append(Order(product, best_ask, -best_ask_vol))

                    if int(best_bid) > min(fair_price,star_ub):
                        print("SELL", str(best_bid_vol) + "x", best_bid)
                        orders.append(Order(product, best_bid, -best_bid_vol))

                    result[product] = orders
        traderData = "TryCOCO"

        # Sample conversion request. Check more details below.
        conversions = 0
        return result, conversions, traderData
