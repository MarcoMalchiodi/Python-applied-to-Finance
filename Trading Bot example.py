# Simple Breakout Strategy
# Dynamically changes its lookback length, this way we won't have to aribatrarily impose a time window (ex. 3 motnhs)

import numpy as np

class MultidimensionalTransdimensionalSplitter(QCAlgorithm):
    def Initialize(self):
        self.SetCash(100000) #example of a starting balance
        self.SetStartDate(2023,1,1)
        self.SetEndDate(2024,1,1)

        self.symbol = self.AddEquity("SPY", Resolution.Daily).Symbol

        self.lookback = 20
        self.ceiling = 30 # upper limit
        self.floor = 10   # lower limit
        
        self.InitialStopRisk = 0.98 # how close our first stop will be to the security's price (2% loss before it activates)
        self.trailingStopRisk = 0.9 # how close our trailing stop will follow the trading asset's price

        self.Schedule.On(self.Daterules.EveryDay(self.symbol), \
            self.TimeRules.AfterMarket(self.symbol, 20), \
                Action(self.EveryMarketOpen))

    # The OnData method is called whenever the algorithm gets new data
    def OnData(self, data):
        self.Plot("DataChart", self.symbol, self.Securities[self.symbol].Close)

    
    # The EveryMarketOpen method is called whenever the market opens
    def EveryMarketOpen(self):
        close = self.History(self.symbol, 31, Resolution.Daily)['close']
        todayvol = np.std(close[1:31])
        yesterdayvol = np.std(close[0:30])
        deltavol = (yesterdayvol - todayvol) / todayvol
        self.lookback = self.lookback * (1 + deltavol)

        # Account for upper/lower limit of lockback length
        if self.lookback > self.ceiling:
            self.lookback = self.ceiling
        elif self.lookback < self.floor:
            self.lookback = self.floor
        
        # List of daily highs
        self.high = self.History(self.symbol, self.lookback, Resolution.Daily)["high"]
        
        # Buy in case of breakout
        if not self.Securities[self.symbol].Invested and \
                self.Securities[self.symbol].Close >= max(self.high[:-1]):
            self.SetHoldings(self.symbol, 1)
            self.breakoutlvl = max(self.high[:-1])
            self.highestPrice = self.breakoutlvl
        
        
        # Create trailing stop loss if invested 
        if self.Securities[self.symbol].Invested:
            
            # If no order exists, send stop-loss
            if not self.Transactions.GetOpenOrders(self.symbol):
                self.stopMarketTicket = self.StopMarketOrder(self.symbol, \
                                        -self.Portfolio[self.symbol].Quantity, \
                                        self.initialStopRisk * self.breakoutlvl)
            
            # Check if the asset's price is higher than highestPrice & trailing stop price not below initial stop price
            if self.Securities[self.symbol].Close > self.highestPrice and \
                    self.initialStopRisk * self.breakoutlvl < self.Securities[self.symbol].Close * self.trailingStopRisk:
                # Save the new high to highestPrice
                self.highestPrice = self.Securities[self.symbol].Close
                # Update the stop price
                updateFields = UpdateOrderFields()
                updateFields.StopPrice = self.Securities[self.symbol].Close * self.trailingStopRisk
                self.stopMarketTicket.Update(updateFields)
                
                # Print the new stop price with Debug()
                self.Debug(updateFields.StopPrice)
            
            # Plot trailing stop's price
            self.Plot("Data Chart", "Stop Price", self.stopMarketTicket.Get(OrderField.StopPrice))