# prosperity2024-laobaijinger

This group LAOBAIJINGER in 2024 IMC Prosperity2 challange!

Group members: Shuai Yuan & Jiayue Joyce Chen @ UC Santa Barbara, Xilin Rice Wang @ Brown University, Yutong Elena Li @ U of Chicago, Shuiqing Sophie Han @ U of Michigan Ann Arbor.

We are all undergrads and NEW to algo trading. This is our first ever hands-on experience, and we are doing a decent job (in my opinion) as a first timer haha.

Here is a short description of final strategies used for different sets of products.

R1: `AMETHYSTS` and `STARFRUIT`, Both market making strategies. 

`AMETHYSTS` we always consider fair price at 10000, take all buy/sell order lower/higher than fair price, and the use left positions market make orders 1 better than best ask/bid.

`STARFRUIT` we used similar market making and taking techniques as `AMETHYSTS`, instead using a fixed fair price, we fitted linear regression that use last 4 steps' weighted mid price to calculate next step's fair price.

Both strategies remain stable from round 2-4, around 15k profit per day.

R2: `ORCHIDS`

We failed to do the correct one side market making arbitrage strategy at round2 which gave most teams tons of profit. We discovered that afterwards, which huge backtester profit, but in the end profit very little from round3 and round4 results.

We did not get any progress from trend trading, and failed to construct a signal using humidity and sunlight information.

We basically gave up on `ORCHIDS`

R3: `GIFT_BASKET` and related

We constructed a pair trading strategy with edge = `GIFT_BASKET` - 6 * `CHOCOLATES` - 4 * `STRAWBERRIES` - `ROSES` - 380. Trade when edge exceed margin value = 38 (0.5 * std). 

In general gives a stable 70k profit per day.

R4: `COCONUT` and `COCONUT_COUPON`

Used basic Black-Scholes model, with fixed volatility = 0.0101193. `COCONUT_COUPON` is like a put option of `COCONUT`, since we don't have the buy option, we use `COCONUT` to hedge.

We calculate fair price of `COCONUT_COUPON`. When it moved more than margin = 2 from fair price, we take the negative position to trade `COCONUT_COUPON` and trade -delta * position of `COCONUT`.

In round4 this pair gives an amazing 160k profit!

R5: Traders information

After few hours on analysis, we reached an agreement that these information are noises LOL. Decided to keep our original strategies. We looked at each individual traders trading a specific product on a given day, and none of them have a good strategy and a straight, positive PnL. Raj's trades do somehow reflect the long term trend of `COCONUT` but we are not sure that this will be beneficial to our algo so we gave up on all the trader information.

