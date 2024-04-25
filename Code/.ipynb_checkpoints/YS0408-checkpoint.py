from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List, Dict
import string
import numpy as np



POSITION_LIMIT = {
    "AMETHYSTS" = 20,
    "STARFRUIT" = 20
}

trade_dict = {
    AM = 0,
    SF = 0
}


class Trader:
        
    
    def run(self, state: TradingState):
        result = {}
        
        def mean_price(product):
            if product == 'AMETHYSTS':
                return 10000
            if product == 'STARFRUIT':
                return 5000
        
        for product in state.order_depths.keys():
            o_depth: OrderDepth = state.order_depths[product]
            orders: list[Order] = []
            
            if len(o_depth.sell_orders) != 0:
                best_ask = min(o_depth.sell_orders.keys())
                best_ask_vol = o_depth.sell_orders[best_ask]
                
                if best_ask < mean_price(product):
                    order.append(Order(product, best_ask, -best_ask_vol)
                
            if len(o_depth.buy_orders) != 0:
                best_bid = min(o_depth.buy_orders.keys())
                best_bid_vol = o_depth.buy_orders[best_bid]
                
                if best_bid > mean_price(product):
                    orders.append(Order(product, best_bid, -best_bid_vol)
            
                                  
            result[product] = orders
                                  
        return results