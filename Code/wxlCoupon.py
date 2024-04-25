import numpy as np
import json
from datamodel import Listing, Observation, Order, OrderDepth, ProsperityEncoder, Symbol, Trade, TradingState
from typing import Any
import numpy as np
from math import sqrt, erf
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
    "AMETHYSTS": 20,
    "COCONUT": 300,
    "COCONUT_COUPON": 600
}

class Trader:
    def __init__(self):
        self.sigma = 0.0101192
        self.K = 10000 
        self.Time = 250
        self.r = 0 
        self.sigma_est=0.2

    def black_scholes_call(self, S, K=10000, T=250, r=0, sigma=0.0101193, ReturnDelta=False):
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        normcdf = lambda x: (1.0 + erf(x / np.sqrt(2))) / 2.0
        N1 = normcdf(d1)  # Delta as the sensitivity of option value to underlying asset price
        N2 = normcdf(d2)
        call_price = S * N1 - K * np.exp(-r * T) * N2
        if ReturnDelta:
            return call_price, N1
        else:
            return call_price

    def fit_volatility(self, vol_fit=0.01, S=10000, px=637.63, T=250, step=0.00001):
        for i in range(30):
            px_new = self.black_scholes_call(S=S, sigma=vol_fit, T=T)
            if abs(px_new - px) < 0.01:
                break
            vol_fit = vol_fit + (px - px_new) * step
        return vol_fit

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
    def calc_midprice(self, order_depth: OrderDepth):
        if len(list(order_depth.sell_orders.values())) > 0 and len(list(order_depth.buy_orders.values())) > 0:
            best_ask, best_ask_vol = list(order_depth.sell_orders.items())[0]
            best_bid, best_bid_vol = list(order_depth.buy_orders.items())[0]
            return (best_ask + best_bid) / 2
        else:
            return 0

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

    def run(self, state: TradingState):
        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))
        result = {}
        threshold = 2  # Define how much deviation is tolerated


        for product in state.order_depths:

            if product == "COCONUT_COUPON":

                COCONUT_current_price = self.calc_weighted_midprice(state.order_depths['COCONUT'])
                COUPON_current_price = self.calc_weighted_midprice(state.order_depths['COCONUT_COUPON'])
                #self.sigma = self.fit_volatility()
                COUPON_fair_price, delta = self.black_scholes_call(COCONUT_current_price, self.K, self.Time, self.r, self.sigma, ReturnDelta=True)
                deviation = COUPON_current_price - COUPON_fair_price
            
                if deviation > threshold: # coupon is overvalued, we should sell
                    if len(list(state.order_depths['COCONUT'].sell_orders.items())) > 0 and len(list(state.order_depths['COCONUT_COUPON'].buy_orders.items())) >0:
                        c_ask, c_ask_vol = list(state.order_depths['COCONUT'].sell_orders.items())[0]
                        cp_bid, cp_bid_vol = list(state.order_depths['COCONUT_COUPON'].buy_orders.items())[0]
                        c_pos = state.position.get("COCONUT", 0)
                        cp_pos = state.position.get("COCONUT_COUPON", 0)

                        c_vol = min(-c_ask_vol, pos_lim["COCONUT"] - c_pos)
                        cp_vol = min(cp_bid_vol, pos_lim["COCONUT_COUPON"] + cp_pos)

                        result["COCONUT"] = [Order('COCONUT', c_ask, c_vol)]
                        result["COCONUT_COUPON"] = [Order('COCONUT_COUPON', cp_bid, -cp_vol)]

                elif deviation < -threshold: # coupon is undervalued, we should buy
                    if len(list(state.order_depths['COCONUT'].buy_orders.items())) > 0 and len(list(state.order_depths['COCONUT_COUPON'].sell_orders.items())) >0:
                        c_bid, c_bid_vol = list(state.order_depths['COCONUT'].buy_orders.items())[0]
                        cp_ask, cp_ask_vol = list(state.order_depths['COCONUT_COUPON'].sell_orders.items())[0]
                        c_pos = state.position.get("COCONUT", 0)
                        cp_pos = state.position.get("COCONUT_COUPON", 0)

                        c_vol = min(c_bid_vol, pos_lim["COCONUT"] + c_pos)
                        cp_vol = min(-cp_ask_vol, pos_lim["COCONUT_COUPON"] - cp_pos)

                        result["COCONUT"] = [Order('COCONUT', c_bid, -c_vol)]
                        result["COCONUT_COUPON"] = [Order('COCONUT_COUPON', cp_ask, cp_vol)]

        traderData = "TryCOCO"

        # Sample conversion request. Check more details below.
        conversions = 0
        logger.flush(state, result, conversions, traderData)
        return result, conversions, traderData
