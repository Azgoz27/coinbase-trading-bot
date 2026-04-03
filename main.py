from trading_order import TradingOrder
import keys
import pairs_list
import config
from coinbase.rest import RESTClient
import time
from logging_config import logger
import argparse
import sys

# Parse command-line arguments
def parse_arguments():
    """Parse command-line arguments for trading mode selection."""
    parser = argparse.ArgumentParser(
        description='CoinbaseUpTrender Trading Bot',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Run in paper trading mode (default)
  python main.py --live_trading     # Run in live trading mode
        """
    )
    
    parser.add_argument(
        '--live_trading',
        action='store_true',
        default=False,
        help='Enable live trading mode (default: False - paper trading)'
    )
    
    return parser.parse_args()

# Create instance with login keys provided in the keys file
client = RESTClient(api_key=keys.api_key, api_secret=keys.api_secret)

# Select the Pairs List
pair_list = pairs_list.TWENTY

def main(live_trading=False):
    """
    Main trading bot function.
    
    Args:
        live_trading (bool): If True, execute live trades. If False, run in paper trading mode.
    """
    # Log trading mode
    trading_mode = "LIVE TRADING" if live_trading else "PAPER TRADING"
    logger.info(f"Starting trading bot in {trading_mode} mode")
    logger.warning(f"Trading Mode: {trading_mode} - {'REAL MONEY AT RISK!' if live_trading else 'Simulated trading'}")

    # Initialize the class with config object
    tco = TradingOrder(
        client=client,
        pairs=pair_list,
        active_order_list=[],
        config=config.DEFAULT_CONFIG,  # Or CONSERVATIVE_CONFIG, AGGRESSIVE_CONFIG
        live_trading=live_trading
    )

    # Sort all pairs per last 24 hour price change
    sorted_pair_list = tco.get_sorted_pair_list()

    # Set initial orders
    tco.set_initial_orders(sorted_pair_list)

    # Get the list of active orders
    tco.active_order_list = tco.get_active_order_list(pair=tco.pairs, status='OPEN')

    while True:
        # Calculate order duration
        order_duration = tco.set_order_time_duration()

        # Scan through all OPEN - BUY, SELL and FILLED orders
        for active_order in tco.active_order_list:
            order_status = tco.get_order_status(active_order['order_id'])
            if not order_status:
                time.sleep(300)
                continue
            for pair in sorted_pair_list:

                # Check if BUY LIMIT order is OPEN
                if (order_status['side'] == 'BUY' and
                        order_status['status'] == 'OPEN' and
                        order_status['order_type'] == 'LIMIT' and
                        order_status['product_id'] == pair['product_id']):
                    buy_limit_price_order = order_status['order_configuration']['limit_limit_gtc']['limit_price']
                    perc_change = round((((float(pair['price']) - float(buy_limit_price_order)) / float(
                        buy_limit_price_order)) * 100), 2)
                    logger.info(f'BUY LIMIT order is OPEN. {pair['product_id']} CP: {pair['price']} BLP: '
                          f'{buy_limit_price_order} = {perc_change}% change')

                # Check if BUY STOP LIMIT order is OPEN
                elif (order_status['side'] == 'BUY' and
                      order_status['status'] == 'OPEN' and
                      order_status['order_type'] == 'STOP_LIMIT' and
                      order_status['product_id'] == pair['product_id']):
                    buy_stop_limit_price_order = order_status['order_configuration']['stop_limit_stop_limit_gtc'][
                        'stop_price']
                    perc_change = round((((float(buy_stop_limit_price_order) - float(pair['price'])) / float(
                        pair['price'])) * 100), 2)
                    logger.info(f'BUY STOP LIMIT order is OPEN. {pair['product_id']} CP: {pair['price']} BSLP: '
                        f'{buy_stop_limit_price_order} = {perc_change}% change')

                # Check if SELL LIMIT order is OPEN
                elif (order_status['side'] == 'SELL' and
                      order_status['status'] == 'OPEN' and
                      order_status['order_type'] == 'LIMIT' and
                      order_status['product_id'] == pair['product_id']):
                    sell_limit_price_order = order_status['order_configuration']['limit_limit_gtc']['limit_price']
                    perc_change = round((((float(sell_limit_price_order) - float(pair['price'])) / float(
                        pair['price'])) * 100), 2)
                    logger.info(f'SELL LIMIT order is OPEN. {pair['product_id']} CP: {pair['price']} SLP: '
                          f'{sell_limit_price_order} = {perc_change}% change')

                # Check if BUY LIMIT order is FILLED
                elif (order_status['side'] == 'BUY' and
                      order_status['status'] == 'FILLED' and
                      order_status['order_type'] == 'LIMIT' and
                      order_status['product_id'] == pair['product_id']):
                    # Calculate new prices and sizes
                    filled_price = order_status['average_filled_price']
                    filled_size = order_status['filled_size']
                    # filled value = ???
                    sell_limit_price = tco.calc_new_price(pair, filled_price, sell=True, limit=True)
                    buy_limit_price = tco.calc_new_price(pair, filled_price, buy=True, limit=True)
                    buy_limit_size = tco.calc_new_size(pair, buy_limit_price, buy=True, limit=True)
                    buy_stop_price, buy_stop_limit_price = tco.calc_new_price(pair, filled_price, buy=True, stop=True)
                    buy_stop_size = tco.calc_new_size(pair, buy_stop_price, buy=True, stop=True)
                    # Execute orders
                    logger.info(f'BUY LIMIT order is FILLED. Removing order from the active order list. {pair['product_id']}')
                    tco.active_order_list.remove(active_order)
                    logger.info(f'Creating new SELL LIMIT order. {pair['product_id']}')
                    tco.set_orders(pair, filled_size, sell_limit_price, sell_limit=True)
                    logger.info(f'Creating new BUY LIMIT order. {pair['product_id']}')
                    tco.set_orders(pair, buy_limit_size, buy_limit_price, buy_limit=True)
                    logger.info(f'Cancelling old BUY STOP LIMIT order. {pair['product_id']}')
                    old_order = tco.get_active_order_list(pair=pair['product_id'], status='OPEN', order_side='BUY',
                                                          order_type='STOP_LIMIT')
                    if old_order:
                        tco.cancel_order(old_order[0]['order_id'])
                        logger.info(f'Buy order cancelled for {pair['product_id']} with order ID: {old_order[0]['order_id']}')
                    else:
                        logger.warning(f'Order NOT found: {pair['product_id']} '
                              f'status=OPEN, order_side=BUY, order_type=STOP_LIMIT')
                    logger.info(f'Creating new BUY STOP LIMIT order. {pair['product_id']}')
                    tco.set_orders(pair, buy_stop_size, buy_stop_price, buy_stop_limit_price, buy_stop_limit=True,
                                   stop_direction='STOP_DIRECTION_STOP_UP')

                # Check if BUY STOP LIMIT order is FILLED
                elif (order_status['side'] == 'BUY' and
                      order_status['status'] == 'FILLED' and
                      order_status['order_type'] == 'STOP_LIMIT' and
                      order_status['product_id'] == pair['product_id']):
                    # Calculate new prices and sizes
                    filled_price = order_status['average_filled_price']
                    filled_size = order_status['filled_size']
                    # filled value = ???
                    sell_limit_price = tco.calc_new_price(pair, filled_price, sell=True, limit=True)
                    buy_limit_price = tco.calc_new_price(pair, filled_price, buy=True, limit=True)
                    buy_limit_size = tco.calc_new_size(pair, buy_limit_price, buy=True, limit=True)
                    buy_stop_price, buy_stop_limit_price = tco.calc_new_price(pair, filled_price, buy=True, stop=True)
                    buy_stop_size = tco.calc_new_size(pair, buy_stop_price, buy=True, stop=True)
                    # Execute orders
                    logger.info(f'BUY STOP LIMIT order is FILLED. Removing order from the active order list. '
                          f'{pair['product_id']}')
                    tco.active_order_list.remove(active_order)
                    logger.info(f'Creating new SELL LIMIT order. {pair['product_id']}')
                    tco.set_orders(pair, filled_size, sell_limit_price, sell_limit=True)
                    logger.info(f'Creating new BUY STOP LIMIT order. {pair['product_id']}')
                    tco.set_orders(pair, buy_stop_size, buy_stop_price, buy_stop_limit_price, buy_stop_limit=True,
                                   stop_direction='STOP_DIRECTION_STOP_UP')
                    logger.info(f'Canceling old BUY LIMIT order. {pair['product_id']}')
                    old_order = tco.get_active_order_list(pair=pair['product_id'], status='OPEN', order_side='BUY',
                                                          order_type='LIMIT')
                    if old_order:
                        tco.cancel_order(old_order[0]['order_id'])
                        logger.info(f'Buy order cancelled for {pair['product_id']} with order ID: {old_order[0]['order_id']}')
                    else:
                        logger.warning(f'Order NOT found: {pair['product_id']} status=OPEN, order_side=BUY, order_type=LIMIT')
                    logger.info(f'Creating new BUY LIMIT order. {pair['product_id']}')
                    tco.set_orders(pair, buy_limit_size, buy_limit_price, buy_limit=True)

                # Check if SELL LIMIT order is FILLED
                elif (order_status['side'] == 'SELL' and
                      order_status['status'] == 'FILLED' and
                      order_status['order_type'] == 'LIMIT' and
                      order_status['product_id'] == pair['product_id']):
                    logger.info(f'SELL LIMIT order is FILLED. Removing order from the active order list. {pair['product_id']}')
                    tco.active_order_list.remove(active_order)

                # Check if BUY LIMIT order is CANCELLED
                elif (order_status['side'] == 'BUY' and
                      order_status['status'] == 'CANCELLED' and
                      order_status['order_type'] == 'LIMIT' and
                      order_status['product_id'] == pair['product_id']):
                    logger.info(f'BUY LIMIT order is CANCELLED. Removing order from the active order list. {pair['product_id']}')
                    tco.active_order_list.remove(active_order)

                # Check if BUY STOP LIMIT order is CANCELLED
                elif (order_status['side'] == 'BUY' and
                      order_status['status'] == 'CANCELLED' and
                      order_status['order_type'] == 'STOP_LIMIT' and
                      order_status['product_id'] == pair['product_id']):
                    logger.info(f'BUY STOP LIMIT order is CANCELLED. Removing order from the active order list. {pair['product_id']}')
                    tco.active_order_list.remove(active_order)

                # Check if SELL LIMIT order is CANCELLED
                elif (order_status['side'] == 'BUY' and
                      order_status['status'] == 'CANCELLED' and
                      order_status['order_type'] == 'LIMIT' and
                      order_status['product_id'] == pair['product_id']):
                    logger.info(f'BUY LIMIT order is CANCELLED. Removing order from the active order list. {pair['product_id']}')
                    tco.active_order_list.remove(active_order)

        # Wait 60 seconds before new orders are checked
        time.sleep(60)
        logger.debug('60 sec passed')


if __name__ == "__main__":
    # Parse command-line arguments
    args = parse_arguments()
    
    # Run main with live_trading flag
    try:
        main(live_trading=args.live_trading)
    except KeyboardInterrupt:
        logger.info("Trading bot stopped by user (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error in trading bot: {e}", exc_info=True)
        sys.exit(1)
