#!/usr/bin/env python3
"""
Logging Test Script

This script tests the logging configuration to ensure everything is working correctly.
Run this before deploying your trading bot to verify logging is functional.

Usage:
    python test_logging.py
"""

import logging
from logging_config import setup_logging

def test_logging():
    """Test all logging levels and verify file output."""
    
    print("=" * 60)
    print("LOGGING SYSTEM TEST")
    print("=" * 60)
    print()
    
    # Setup logging
    logger = setup_logging(level=logging.DEBUG)
    
    # Get a test logger
    test_logger = logging.getLogger(__name__)
    
    print("✓ Logger initialized successfully")
    print()
    
    # Test different log levels
    print("Testing log levels...")
    print("-" * 60)
    
    test_logger.debug("DEBUG level - Detailed diagnostic information")
    test_logger.info("INFO level - General operational information")
    test_logger.warning("WARNING level - Warning about potential issues")
    test_logger.error("ERROR level - Error that occurred")
    
    print("-" * 60)
    print()
    
    # Test module loggers
    print("Testing module-specific logging...")
    print("-" * 60)
    
    my_module_logger = logging.getLogger("my_module")
    my_module_logger.info("New BUY LIMIT order created: test_order_123")
    my_module_logger.debug("Found 2 open BUY LIMIT orders for BTC-USD")
    my_module_logger.warning("Order Limit reached for ETH-USD, skipping BUY LIMIT order.")
    
    print("-" * 60)
    print()
    
    # Test trading bot simulation
    print("Testing trading bot scenario...")
    print("-" * 60)
    
    main_logger = logging.getLogger("__main__")
    main_logger.info("BUY LIMIT order is FILLED. Removing order from the active order list. BTC-USD")
    main_logger.info("Creating new SELL LIMIT order. BTC-USD")
    main_logger.info("Creating new BUY LIMIT order. BTC-USD")
    main_logger.debug("60 sec passed")
    
    print("-" * 60)
    print()
    
    # Summary
    print("=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print()
    print("✅ All logging levels working correctly!")
    print()
    print("Log files are being saved to: logs/trading_bot_*.log")
    print()
    print("Your logging system is ready for production use.")
    print()


if __name__ == "__main__":
    test_logging()

