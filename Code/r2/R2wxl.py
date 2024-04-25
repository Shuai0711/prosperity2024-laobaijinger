from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import string
import numpy as np
import collections

INF = int(1e9)

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

        if buy_lim>0:
            orders.append(Order(product, bid_price, buy_lim))

        if sell_lim>0:
            orders.append(Order(product, ask_price, -sell_lim))


        # if len(order_depth.sell_orders) > 0:
        #     best_ask, best_ask_vol = list(order_depth.sell_orders.items())[0]
        #     if int(best_ask) < 10000:
        #         #print("BUY", str(-best_ask_vol) + "x", best_ask)
        #         amt = min(buy_lim, -best_ask_vol)
        #         orders.append(Order(product, best_ask, amt))
        #         buy_lim = buy_lim - amt

        # if len(order_depth.buy_orders) != 0:
        #     best_bid, best_bid_vol = list(order_depth.buy_orders.items())[0]
        #     if int(best_bid) > 10000:
        #         #print("SELL", str(best_bid_vol) + "x", best_bid)
        #         amt = min(sell_lim, best_bid_vol)
        #         orders.append(Order(product, best_bid, -amt))
        #         sell_lim = sell_lim - amt
        
        # ## Market making
        # if buy_lim > 0:
        #     orders.append(Order(product, 9999, buy_lim))
        # if sell_lim > 0:
        #     orders.append(Order(product, 10001, -sell_lim))

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
                if ((ask <= star_bid) or ((current_position < 0) and (ask == star_bid+1))) and buy_lim > 0:
                    amt = min(-vol, buy_lim)
                    buy_lim -= amt
                    orders.append(Order(product, ask, amt))

        if len(order_depth.buy_orders) != 0:
            for bid, vol in list(order_depth.buy_orders.items()):
                if ((bid >= star_sell) or ((current_position > 0) and (bid == star_sell-1))) and sell_lim > 0:
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

        if buy_lim>0:
            orders.append(Order(product, bid_price, buy_lim))

        if sell_lim>0:
            orders.append(Order(product, ask_price, -sell_lim))



        # if len(order_depth.sell_orders) > 0 and len(order_depth.buy_orders) > 0:
        #     w, v = 0, 0
        #     for price, vol in list(order_depth.buy_orders.items()):
        #         if price is None or vol is None:
        #             continue
        #         w += int(price) * int(vol)
        #         v += int(vol)
        #     weight_bid = w/v

        #     w, v = 0, 0
        #     for price, vol in list(order_depth.sell_orders.items()):
        #         if price is None or vol is None:
        #             continue
        #         w += int(price) * int(vol)
        #         v += int(vol)
        #     weight_ask = w/v

        #     best_bid, best_bid_vol = list(order_depth.buy_orders.items())[0]
        #     best_ask, best_ask_vol = list(order_depth.sell_orders.items())[0]
        #     vol_diff = best_ask_vol - best_bid_vol
        #     fair_price = (weight_ask + weight_bid)/2 - 0.07 * current_position

        #     if int(best_ask) < fair_price:
        #         print("BUY", str(best_ask < fair_price), str(best_ask < star_bid))
        #         amt = min(buy_lim, -best_ask_vol)
        #         orders.append(Order(product, best_ask, amt))
        #         buy_lim = buy_lim - amt

        #     if int(best_bid) > fair_price:
        #         print("SELL", str(best_bid > fair_price), str(best_bid > star_bid))
        #         amt = min(sell_lim, best_bid_vol)
        #         orders.append(Order(product, best_bid, -amt))
        #         sell_lim = sell_lim - amt
        
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

        ## Main trading strategies
        for product in state.order_depths:
            if product == "AMETHYSTS":
                orders = self.compute_order_amethysts(state)
                result[product] = orders

            if product == "STARFRUIT":
                orders = self.compute_order_starfruit(state)
                result[product] = orders

            if product == "ORCHIDS":
                order_depth: OrderDepth = state.order_depths[product]
                orders: List[Order] = []
                observation = state.observations.conversionObservations[product]

                current_position = int(state.position.get(product, 0))
                buy_lim = 100 - current_position
                sell_lim = current_position + 100

                conversions = -current_position

                if len(order_depth.buy_orders) > 0:
                    best_bid, best_bid_vol = list(order_depth.buy_orders.items())[0]
                    if best_bid > observation.askPrice + observation.transportFees + observation.importTariff :
                        #print("SELL", str(-best_bid_vol) + "x", best_bid)
                        # if (current_position < 0):
                        #     conversions = min(-current_position, best_bid_vol)
                        orders.append(Order(product, best_bid, -min(sell_lim, best_bid_vol)))

                if len(order_depth.sell_orders) > 0:
                    best_ask, best_ask_vol = list(order_depth.sell_orders.items())[0]
                    if best_ask < observation.bidPrice  - observation.transportFees - observation.exportTariff:
                        #print("BUY", str(best_ask_vol)  "x", best_ask)
                        # if (current_position > 0):
                        #     conversions = -min(current_position, -best_ask_vol)
                        orders.append(Order(product, best_ask, min(buy_lim, -best_ask_vol)))

                result[product] = orders
        
        traderData = "TryCOCO"

        return result, conversions, traderData
