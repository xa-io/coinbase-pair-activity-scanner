# Coinbase Trading Pairs Monitor & Watchlist Generator

This repository contains two Python scripts designed to help you monitor trading pairs on Coinbase and generate watchlists for personal use and Discord notifications.

This script is running 24/7 here: https://discord.gg/FprzuuWZ7t

## Examples:
- `@Pair Scanner [Enabled] BTC-USD has been detected.`
- `@Pair Scanner BTC-USD post only has been disabled.`

## Scripts Overview

### 1. `coinbase_monitor.py`

This script continuously monitors USD trading pairs on Coinbase Advanced and sends real-time notifications to a Discord channel. It tracks changes in trading status (enabled/disabled) and updates in specific fields like `post_only`, `limit_only`, and `trading_disabled`.

**Key Features:**
- **Real-Time Monitoring:** Continuously fetches trading pairs and detects new, traded, and disabled pairs.
- **Discord Notifications:** Sends alerts to a Discord channel, including mentions of specific roles.
- **Logging:** Keeps a record of changes in trading pairs and specific field updates.

### 2. `watchlist_generator.py`

This script generates two watchlist files from a base template and a list of trading pairs. One file is intended for personal use, while the other is formatted for Discord notifications. The script can optionally upload the Discord-formatted watchlist to a Discord channel.

**Key Features:**
- **Customizable Templates:** Includes base templates for watchlists, with specific sections for market leaders, Bitcoin ETFs, and more.
- **Duplicate Filtering:** Automatically removes duplicate trading pairs to keep your watchlists clean.
- **Discord Integration:** Optionally sends the watchlist file to a Discord channel.

## Setup

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/coinbase-monitor-watchlist.git
cd coinbase-monitor-watchlist
```

## Consider Donating:
If you find OmniBot helpful, consider supporting the development with a donation:

- **BTC**: `bc1qwjy0hl4z9c930kgy4nud2fp0nw8m6hzknvumgg`
- **ETH**: `0x0941D41Cd0Ee81bd79Dbe34840bB5999C124D3F0`
- **SOL**: `4cpdbmmp1hyTAstA3iUYdFbqeNBwjFmhQLfL5bMgf77z`
