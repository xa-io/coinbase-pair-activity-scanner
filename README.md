# Coinbase Trading Pairs Monitor & Watchlist Generator

This repository contains two Python scripts designed to help you monitor trading pairs on Coinbase and generate watchlists for personal use and Discord notifications.

This script is running 24/7 here: https://discord.gg/FprzuuWZ7t

## Examples:
- `@Pair Scanner BTC-USD cancel only has been disabled.`
- `https://www.coinbase.com/advanced-trade/spot/BTC-USD`
- `@Pair Scanner BTC-USD auction mode has started.`
- `https://www.coinbase.com/advanced-trade/spot/BTC-USD`

## Scripts Overview

### 1. `fetch_usd_pairs.py`

This script continuously monitors USD trading pairs on Coinbase Advanced and sends real-time notifications to a Discord channel. It tracks changes in trading status (enabled/disabled) and updates in specific fields like `post_only`, `limit_only`, and `trading_disabled`.

**Key Features:**
- **Real-Time Monitoring:** Continuously fetches trading pairs and detects new, traded, and disabled pairs.
- **Discord Notifications:** Sends alerts to a Discord channel, including mentions of specific roles.
- **Logging:** Keeps a record of changes in trading pairs and specific field updates.

### 2. `tradingview_watchlist_builder.py`

This script generates two watchlist files from a base template and a list of trading pairs. One file is intended for personal use, while the other is formatted for Discord notifications. The script can optionally upload the Discord-formatted watchlist to a Discord channel.

**Key Features:**
- **Customizable Templates:** Includes base templates for watchlists, with specific sections for market leaders, Bitcoin ETFs, and more.
- **Duplicate Filtering:** Automatically removes duplicate trading pairs to keep your watchlists clean.
- **Discord Integration:** Optionally sends the watchlist file to a Discord channel.

### Revision 2: Update (2024-12-13):
- Updated for new Coinbase API endpoints:
  - Transitioned from the deprecated pro.coinbase.com endpoint to the new Coinbase Advanced Trade endpoint. 
  - Replaced the old products URL (https://api.pro.coinbase.com/products) with the new URL (https://api.exchange.coinbase.com/products).
  - Ensured compatibility with the updated format and fields returned by the new Coinbase Advanced Trade API.
- Improved Field Normalization**  
  - The updated script now normalizes field values, ensuring consistency by handling special characters and formatting discrepancies. This enhancement reduces redundant notifications caused by inconsistent field values.

- **Optimized Baseline Creation**  
  - On the first run, the script automatically creates a baseline for tracking changes in fields like `post_only`, `limit_only`, `cancel_only`, and more. This ensures efficient and accurate detection of future updates.

- **Reduced Notification Spam**  
  - Updates to fields such as `status_message` and other frequently changing values are now filtered to avoid unnecessary notifications. This ensures you only get the most relevant alerts.

- **Faster Update Intervals**  
  - The monitoring interval has been fine-tuned to provide updates every 10 seconds, offering near real-time tracking without overwhelming system resources.

- **Discord Notifications Enhancements**  
  - Notifications now include improved formatting and links to the corresponding trading pairs on Coinbase Advanced, making it easier to take action on updates.

- **Streamlined Logging**  
  - All changes, including new pairs, activations, and field updates, are logged systematically, providing a comprehensive record for review.

## Consider Donating:
If you find OmniBot helpful, consider supporting the development with a donation:

- **BTC**: `bc1qwjy0hl4z9c930kgy4nud2fp0nw8m6hzknvumgg`
- **ETH**: `0x0941D41Cd0Ee81bd79Dbe34840bB5999C124D3F0`
- **SOL**: `4cpdbmmp1hyTAstA3iUYdFbqeNBwjFmhQLfL5bMgf77z`
