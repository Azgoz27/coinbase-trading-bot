from datetime import datetime, timedelta, timezone
import uuid
import logging

# Configure logger for this module
logger = logging.getLogger(__name__)


class TradingOrder:
    def __init__(self, client, pairs, active_order_list, config, live_trading=False):
        """
        Args:
            client: Coinbase REST client
            pairs: List of trading pairs
            active_order_list: Active orders list
            config: TradingConfig object with all parameters
            live_trading: Live trading flag
        """
        self.client = client
        self.pairs = pairs
        self.active_order_list = active_order_list
        self.config = config
        self.live_trading = live_trading

        # Map config parameters to instance attributes
        self.number_of_trading_pairs = config.number_of_trading_pairs
        self.max_quote = config.max_quote
        self.trading_limit = config.trading_limit
        self.time_modifier = config.time_modifier
        self.buy_limit_price_percent = config.buy_limit_price_percent
        self.buy_stop_price_percent = config.buy_stop_price_percent
        self.buy_stop_limit_price_percent = config.buy_stop_limit_price_percent
        self.sell_limit_price_percent = config.sell_limit_price_percent
        self.sell_stop_price_percent = config.sell_stop_price_percent
        self.sell_stop_limit_price_percent = config.sell_stop_limit_price_percent
        self.sell_bracket_limit_percent = config.sell_bracket_limit_percent
        self.sell_bracket_stop_percent = config.sell_bracket_stop_percent

        mode_status = "LIVE TRADING ENABLED" if live_trading else "PAPER TRADING MODE"
        logger.info(f"TradingOrder initialized in {mode_status} - {config}")

    def get_sorted_pair_list(self):
        """
        Get Current price for selected pairs, then Get sorted list of pairs.
        """
        # Get Current price for selected pairs
        product_type = "SPOT"
        limit = self.number_of_trading_pairs
        try:
            data = self.client.get_products(product_type=product_type, product_ids=self.pairs, limit=limit)
        except Exception as e:
            logger.error(f'Failed to fetch pair prices: {e}')
        products_data = data['products']

        # Get sorted list of pairs
        sorted_products_data = sorted(products_data, key=lambda x: x['price_percentage_change_24h'], reverse=True)

        return sorted_products_data

    def set_order_time_duration(self):
        """
        Get current time and set the time modifier.
        """
        local_time = datetime.now(timezone.utc)
        modified_time = local_time + timedelta(minutes=self.time_modifier)
        return modified_time.isoformat()

    def set_orders(self, pair, size, price, buy_stop_limit_price=None, buy_limit=False, buy_stop_limit=False,
                   sell_limit=False, stop_direction=None, order_duration=None):
        """
        Check if Order Limit is reached
        Open Buy Limit order.
        Open Buy Stop Limit order.
        Open Sell Limit order.
        """
        # Check if trading mode allows actual orders
        if not self.live_trading:
            order_type = "BUY LIMIT" if buy_limit else ("BUY STOP LIMIT" if buy_stop_limit else "SELL LIMIT")
            logger.info(f"[PAPER TRADING] Would create {order_type} order for {pair['product_id']} at price {price} with size {size}")
            return
        
        # For GTD orders
        # end_time = str(order_duration)
        limit_check_result = self.trading_limit_check(pair['product_id'], status='OPEN', order_side='SELL',
                                                      order_type='LIMIT')

        if buy_limit and limit_check_result:
            client_order_id = str(uuid.uuid4().hex)
            product_id = str(pair['product_id'])
            buy_limit_price = str(price)
            base_size_buy_limit = str(size)
            post_only = True

            try:
                order_data = self.client.limit_order_gtc_buy(client_order_id=client_order_id,
                                                             product_id=product_id,
                                                             base_size=base_size_buy_limit,
                                                             limit_price=buy_limit_price,
                                                             post_only=post_only
                                                             )
                # Add order to list of created orders
                if order_data['success']:
                    logger.info(f"New BUY LIMIT order created: {order_data['success_response']['order_id']}")
                    new_order_id = self.client.list_orders(order_ids=order_data['success_response']['order_id'])
                    self.active_order_list.append(new_order_id['orders'][0])
                else:
                    logger.error(f"BUY LIMIT order failed with error: {order_data['error_response']['error']}")

            except Exception as e:
                logger.error(f'Failed to create BUY LIMIT order: {e}')

        elif buy_limit and not limit_check_result:
            logger.warning(f'Order Limit reached for {pair['product_id']}, skipping BUY LIMIT order.')

        elif buy_stop_limit:
            client_order_id = str(uuid.uuid4().hex)
            product_id = str(pair['product_id'])
            buy_stop_price = str(price)
            buy_stop_limit_price = str(buy_stop_limit_price)
            base_size_buy_stop = str(size)
            stop_direction = stop_direction

            try:
                order_data = self.client.stop_limit_order_gtc_buy(client_order_id=client_order_id,
                                                                  product_id=product_id,
                                                                  base_size=base_size_buy_stop,
                                                                  limit_price=buy_stop_limit_price,
                                                                  stop_price=buy_stop_price,
                                                                  stop_direction=stop_direction
                                                                  )
                # Add order to list of created orders
                if order_data['success']:
                    logger.info(f"New BUY STOP LIMIT order created: {order_data['success_response']['order_id']}")
                    new_order_id = self.client.list_orders(order_ids=order_data['success_response']['order_id'])
                    self.active_order_list.append(new_order_id['orders'][0])
                else:
                    logger.error(f"BUY STOP LIMIT order failed with error: {order_data['error_response']['error']}")

            except Exception as e:
                logger.error(f'Failed to create BUY STOP LIMIT order: {e}')

        elif sell_limit:
            client_order_id = str(uuid.uuid4().hex)
            product_id = str(pair['product_id'])
            sell_limit_price = str(price)
            base_size_sell_limit = str(size)
            post_only = True

            try:
                order_data = self.client.limit_order_gtc_sell(client_order_id=client_order_id,
                                                              product_id=product_id,
                                                              base_size=base_size_sell_limit,
                                                              limit_price=sell_limit_price,
                                                              post_only=post_only
                                                              )
                # Add order to list of created orders
                if order_data['success']:
                    logger.info(f"New SELL LIMIT order created: {order_data['success_response']['order_id']}")
                    new_order_id = self.client.list_orders(order_ids=order_data['success_response']['order_id'])
                    self.active_order_list.append(new_order_id['orders'][0])
                else:
                    logger.error(f"SELL LIMIT order failed with error: {order_data['error_response']['error']}")

            except Exception as e:
                logger.error(f'Failed to create SELL LIMIT order: {e}')

    def calc_new_price(self, pair, price, buy=False, sell=False, limit=False, stop=False):
        base_price = price
        qoute_increment = pair['quote_increment']
        base_price_decimal_length = qoute_increment[::-1].find('.')
        if base_price_decimal_length <= 0:
            base_price_decimal_length = 2
        if buy and limit:
            buy_limit_price = round(float(price) * self.buy_limit_price_percent,
                                    base_price_decimal_length)
            return buy_limit_price
        elif buy and stop:
            buy_stop_price = round(float(price) * self.buy_stop_price_percent,
                                   base_price_decimal_length)
            buy_stop_limit_price = round(float(base_price) * self.buy_stop_limit_price_percent,
                                         base_price_decimal_length)
            return buy_stop_price, buy_stop_limit_price
        elif sell and limit:
            sell_limit_price = round(float(price) * self.sell_limit_price_percent,
                                     base_price_decimal_length)
            return sell_limit_price
        elif sell and stop:
            sell_stop_price = round(float(price) * self.sell_stop_price_percent,
                                    base_price_decimal_length)
            sell_stop_limit_price = round(float(price) * self.sell_stop_limit_price_percent,
                                          base_price_decimal_length)
            return sell_stop_price, sell_stop_limit_price

    def calc_new_size(self, pair, price, buy=False, limit=False, stop=False):
        base_min_size = pair['base_min_size']
        if buy and limit:
            if base_min_size == '1':
                base_size_buy_limit = int(self.max_quote / float(price))
                return base_size_buy_limit
            else:
                base_size_decimal_length = base_min_size[::-1].find('.')
                base_size_buy_limit = round(self.max_quote / float(price),
                                            base_size_decimal_length)
                return base_size_buy_limit
        elif buy and stop:
            if base_min_size == '1':
                base_size_buy_stop = int(self.max_quote / float(price))
                return base_size_buy_stop
            else:
                base_size_decimal_length = base_min_size[::-1].find('.')
                base_size_buy_stop = round(self.max_quote / float(price),
                                           base_size_decimal_length)
                return base_size_buy_stop

    def get_active_order_list(self, pair=None, status=None, order_side=None, order_type=None):
        try:
            return self.client.list_orders(product_ids=pair, order_status=status, order_side=order_side,
                                           order_types=order_type)['orders']
        except Exception as e:
            logger.error(f'Failed to fetch active orders: {e}')

    def get_order_status(self, order_id):
        try:
            return self.client.get_order(order_id)['order']
        except Exception as e:
            logger.error(f'Failed to fetch order per order_id: {e}')

    def cancel_order(self, old_order):
        try:
            self.client.cancel_orders(order_ids=[old_order])
        except Exception as e:
            logger.error(f'Failed to cancel order: {e}')

    def trading_limit_check(self, pair=None, status=None, order_side=None, order_type=None):
        try:
            limit_list = self.get_active_order_list(pair=pair, status=status, order_side=order_side,
                                                    order_type=order_type)
            logger.debug(f'Found {len(limit_list)} open SELL LIMIT orders for {pair}')
            if len(limit_list) < self.trading_limit:
                return True
            else:
                return False
        except Exception as e:
            logger.error(f'Failed to check order limit: {e}')

    def set_initial_orders(self, pair_list):
        for pair in pair_list:
            limit_status = self.trading_limit_check(pair=pair['product_id'], status='OPEN', order_side='SELL',
                                                    order_type='LIMIT')
            if limit_status:
                try:
                    # Open Buy Limit orders
                    open_buy_limit_orders = self.get_active_order_list(pair=pair['product_id'], status='OPEN',
                                                                       order_side='BUY', order_type='LIMIT')
                    logger.debug(f'Found {len(open_buy_limit_orders)} open BUY LIMIT orders for {pair['product_id']}')
                    if len(open_buy_limit_orders) == 0:
                        buy_limit_price = self.calc_new_price(pair, pair['price'], buy=True, limit=True)
                        buy_limit_size = self.calc_new_size(pair, buy_limit_price, buy=True, limit=True)
                        self.set_orders(pair, buy_limit_size, buy_limit_price, buy_limit=True)
                    # Open Buy Stop Limit orders
                    open_buy_stop_limit_orders = self.get_active_order_list(pair=pair['product_id'], status='OPEN',
                                                                            order_side='BUY', order_type='STOP_LIMIT')
                    logger.debug(f'Found {len(open_buy_stop_limit_orders)} open BUY STOP LIMIT orders for {pair['product_id']}')
                    if len(open_buy_stop_limit_orders) == 0:
                        buy_stop_price, buy_stop_limit_price = self.calc_new_price(pair, pair['price'], buy=True,
                                                                                   stop=True)
                        buy_stop_size = self.calc_new_size(pair, buy_stop_price, buy=True, stop=True)
                        self.set_orders(pair, buy_stop_size, buy_stop_price, buy_stop_limit_price, buy_stop_limit=True,
                                        stop_direction='STOP_DIRECTION_STOP_UP')
                except Exception as e:
                    logger.error(f'Failed to fetch active Buy orders: {e}')
            else:
                logger.warning(f'Order Limit reached for {pair['product_id']}')

