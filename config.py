class TradingConfig:
    """Configuration class for trading parameters."""

    def __init__(self,
                 number_of_trading_pairs=20,
                 max_quote=2.0,
                 trading_limit=5,
                 time_modifier=10,
                 buy_limit_price_percent=0.9,
                 buy_stop_price_percent=1.1,
                 buy_stop_limit_price_percent=1.11,
                 sell_limit_price_percent=1.1,
                 sell_stop_price_percent=0.9,
                 sell_stop_limit_price_percent=0.89,
                 sell_bracket_limit_percent=1.042,
                 sell_bracket_stop_percent=0.958):
        self.number_of_trading_pairs = number_of_trading_pairs
        self.max_quote = max_quote
        self.trading_limit = trading_limit
        self.time_modifier = time_modifier
        self.buy_limit_price_percent = buy_limit_price_percent
        self.buy_stop_price_percent = buy_stop_price_percent
        self.buy_stop_limit_price_percent = buy_stop_limit_price_percent
        self.sell_limit_price_percent = sell_limit_price_percent
        self.sell_stop_price_percent = sell_stop_price_percent
        self.sell_stop_limit_price_percent = sell_stop_limit_price_percent
        self.sell_bracket_limit_percent = sell_bracket_limit_percent
        self.sell_bracket_stop_percent = sell_bracket_stop_percent


# Default configuration
DEFAULT_CONFIG = TradingConfig()

# Predefined strategies
CONSERVATIVE_CONFIG = TradingConfig(number_of_trading_pairs=10, max_quote=0.5, trading_limit=3)
AGGRESSIVE_CONFIG = TradingConfig(number_of_trading_pairs=30, max_quote=5.0, trading_limit=8)