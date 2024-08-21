import os
from datetime import datetime
from discord_webhook import DiscordWebhook

# Configuration
send_to_discord = True  # Set to True if you want the watchlist file to be sent to Discord automatically
webhook_url = 'https://discord.com/api/webhooks/your_webhook_id/your_webhook_token'  # Replace with your Discord webhook URL

# Get the directory where the script is located
# This ensures that file paths are correctly referenced relative to the script's location
script_dir = os.path.dirname(os.path.abspath(__file__))

# Get the current date and format it as M-D-YY
# This date stamp will be used in the filenames for easy identification
date_stamp = datetime.now().strftime("%m-%d-%y")

# Define the full path to the input file
# 'TV-Coinbase-Watchlist.txt' should contain the list of trading pairs to be added to the watchlist
input_file_path = os.path.join(script_dir, 'TV-Coinbase-Watchlist.txt')

# Define the full paths to the output files
# Two separate watchlist files will be created: one for personal use and one formatted for Discord
output_file_path_personal = os.path.join(script_dir, f'Watchlist - {date_stamp}.txt')
output_file_path_discord = os.path.join(script_dir, f'Watchlist - {date_stamp} - Discord.txt')

# Define common pairs to be included in the watchlists
# These include market leaders, Bitcoin ETFs, staking assets, and stablecoins
market_leaders_pairs = """COINBASE:BTCUSD,
COINBASE:ETHUSD,
COINBASE:SOLUSD,
COINBASE:DOGEUSD,
BINANCE:BNBUSDT,
COINBASE:XRPUSD,
COINBASE:CROUSD,
COINBASE:ADAUSD,
BINANCE:AVAXUSDT,
COINBASE:LTCUSD,"""

bitcoin_etfs_pairs = """AMEX:EZBC,
AMEX:ARKB,
NASDAQ:IBIT,
AMEX:BITB,
AMEX:FBTC,
AMEX:HODL,
AMEX:BTCO,
NASDAQ:BRRR,
AMEX:GBTC,
AMEX:BTCW,
AMEX:DEFI,"""

stakes_pairs = """COINBASE:WBTCUSD,
COINBASE:CBETHUSD,
COINBASE:LSETHUSD,
COINBASE:MSOLUSD,"""

stablecoins_pairs = """1/COINBASE:USDTUSD,
COINBASE:DAIUSD,
COINBASE:PAXUSD,
COINBASE:PYUSDUSD,
COINBASE:GUSDUSD,
COINBASE:GYENUSD,"""

# Base template with sections for personal use (includes SECTION 1)
# SECTION 1 is meant for pairs that are relevant to the user but not included in the Discord version
base_template_personal = f"""###MARKET LEADERS,
{market_leaders_pairs}

###BITCOIN ETF'S,
{bitcoin_etfs_pairs}

###SECTION 1,
NYSE:GME,
NYSE:AMC,

###CRYPTO FLOOD,
{{crypto_flood_pairs}},

###STAKES,
{stakes_pairs}

###STABLECOINS,
{stablecoins_pairs}
"""

# Base template for Discord (excludes SECTION 1)
# This version is formatted specifically for sending to Discord and excludes personal sections
base_template_discord = f"""###MARKET LEADERS,
{market_leaders_pairs}

###BITCOIN ETF'S,
{bitcoin_etfs_pairs}

###CRYPTO FLOOD,
{{crypto_flood_pairs}},

###STAKES,
{stakes_pairs}

###STABLECOINS,
{stablecoins_pairs}
"""

# Create a set of pairs that are already included in the base templates to prevent duplicates
# This ensures that the same trading pairs aren't added multiple times
existing_pairs_personal = set(pair.strip() for pair in base_template_personal.split(',') if pair.strip())
existing_pairs_discord = set(pair.strip() for pair in base_template_discord.split(',') if pair.strip())

# Read pairs from TV-Coinbase-Watchlist.txt
# These are the new pairs that will be added under the 'CRYPTO FLOOD' section
with open(input_file_path, 'r') as file:
    new_pairs = {line.strip().rstrip(',') for line in file if line.strip()}

# Filter out any pairs that are already in the base templates or duplicates
# This step ensures that only unique pairs are added to the final watchlists
unique_pairs_personal = sorted(pair for pair in new_pairs if pair not in existing_pairs_personal)
unique_pairs_discord = sorted(pair for pair in new_pairs if pair not in existing_pairs_discord)

# Convert the list of unique pairs back to a string with commas and newlines for insertion into the templates
crypto_flood_content_personal = ',\n'.join(unique_pairs_personal)
crypto_flood_content_discord = ',\n'.join(unique_pairs_discord)

# Insert the new pairs into the base templates
# The templates are populated with the filtered pairs under the 'CRYPTO FLOOD' section
output_content_personal = base_template_personal.format(crypto_flood_pairs=crypto_flood_content_personal)
output_content_discord = base_template_discord.format(crypto_flood_pairs=crypto_flood_content_discord)

# Write the personal file (with SECTION 1)
# This file is tailored for the user's personal use, including the custom SECTION 1
with open(output_file_path_personal, 'w') as output_file:
    output_file.write(output_content_personal)

print(f"Personal watchlist file '{output_file_path_personal}' has been created.")

# Write the Discord file (without SECTION 1)
# This version is prepared specifically for sharing on Discord
with open(output_file_path_discord, 'w') as output_file:
    output_file.write(output_content_discord)

print(f"Discord watchlist file '{output_file_path_discord}' has been created.")

# Conditionally send the file to Discord
# If send_to_discord is set to True, the file will be uploaded to the specified Discord channel
if send_to_discord:
    webhook = DiscordWebhook(url=webhook_url, content="Here is the latest watchlist file for Coinbase:")
    with open(output_file_path_discord, "rb") as f:
        webhook.add_file(file=f.read(), filename=f'Watchlist - {date_stamp} - Discord.txt')
    response = webhook.execute()

    print(f"File '{output_file_path_discord}' uploaded to Discord.")
else:
    print("File was not uploaded to Discord as per the configuration.")
