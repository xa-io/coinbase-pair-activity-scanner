import os
from datetime import datetime
import time
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
# Ensure you have a .env file in the same directory as this script with the following variables:
# DISCORD_WEBHOOK_URL: The webhook URL to send notifications to Discord
# MENTION_ROLE: The role to mention in Discord when sending notifications (e.g., @everyone or a specific role ID)
load_dotenv()

# Your Discord webhook URL and role mention
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
mentionrole = os.getenv('MENTION_ROLE')

# Directory where the script and files are located
# This will automatically point to the directory where the script is being executed
script_dir = os.path.dirname(os.path.realpath(__file__))

# Function to send a notification to Discord
# This function takes the content (text) to be sent to Discord and posts it to the webhook URL
def send_discord_notification(content):
    if content.strip():
        data = {"content": content}
        response = requests.post(DISCORD_WEBHOOK_URL, json=data)
        if response.status_code == 204:
            print("Discord notification sent successfully.")
        else:
            print(f"Failed to send Discord notification. Status code: {response.status_code}")

# Function to fetch all trading pairs from Coinbase Pro API
# It filters the pairs to only include those quoted in USD, and then separates them into traded and disabled pairs
def fetch_usd_pairs():
    start_time = time.time()  # Start measuring time
    url = "https://api.pro.coinbase.com/products"  # Coinbase Pro API endpoint to fetch product data
    
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Coinbase Pro API: {e}")
        return
    
    products = response.json()
    
    # Filter out only USD pairs
    usd_pairs = [product for product in products if product['quote_currency'] == 'USD']
    
    # Separate traded and disabled pairs
    traded_pairs = sorted([pair['id'] for pair in usd_pairs if not pair['trading_disabled']])
    disabled_pairs = sorted([pair['id'] for pair in usd_pairs if pair['trading_disabled']])
    
    # Load previously saved pairs if the file exists
    previous_traded_pairs = set()
    previous_disabled_pairs = set()
    fields_status = {}
    pairs_file_path = os.path.join(script_dir, "pairs.txt")
    fields_status_file_path = os.path.join(script_dir, "fields_status.txt")

    try:
        with open(pairs_file_path, "r") as file:
            lines = file.readlines()
            traded_section = False
            disabled_section = False
            for line in lines:
                if line.strip() == "Traded Pairs:":
                    traded_section = True
                    disabled_section = False
                    continue
                elif line.strip() == "Disabled Pairs:":
                    traded_section = False
                    disabled_section = True
                    continue
                
                if traded_section and line.strip():
                    previous_traded_pairs.add(line.strip())
                if disabled_section and line.strip():
                    previous_disabled_pairs.add(line.strip())
    except FileNotFoundError:
        print("pairs.txt not found, creating a new one.")
    
    try:
        with open(fields_status_file_path, "r") as file:
            for line in file:
                pair_id, statuses_str = line.strip().split(":", 1)
                fields_status[pair_id] = dict(field.split("=") for field in statuses_str.split(",") if "=" in field)
    except FileNotFoundError:
        print("fields_status.txt not found, creating a new one.")
    
    # Get the current pairs and field statuses
    current_traded_pairs = set(traded_pairs)
    current_disabled_pairs = set(disabled_pairs)
    current_fields_status = {pair['id']: {
        'post_only': str(pair['post_only']),
        'limit_only': str(pair['limit_only']),
        'cancel_only': str(pair['cancel_only']),
        'status': str(pair['status']),
        'status_message': str(pair['status_message']),
        'trading_disabled': str(pair['trading_disabled']),
        'auction_mode': str(pair['auction_mode'])
    } for pair in usd_pairs}
    
    # Find new pairs
    previous_pairs = previous_traded_pairs | previous_disabled_pairs
    current_pairs = current_traded_pairs | current_disabled_pairs
    new_pairs = current_pairs - previous_pairs

    # Detect changes between traded and disabled pairs
    moved_to_traded = previous_disabled_pairs & current_traded_pairs
    moved_to_disabled = previous_traded_pairs & current_disabled_pairs

    # Detect changes in specified fields (e.g., post_only, limit_only, etc.)
    field_changes = {}
    for pair_id, statuses in current_fields_status.items():
        previous_statuses = fields_status.get(pair_id, {})
        changes = {field: statuses[field] for field in statuses if statuses[field] != previous_statuses.get(field, None)}
        if changes:
            field_changes[pair_id] = changes

    # Ensure pairs.txt and TV-Coinbase-Watchlist.txt are created and updated on the first run or when new pairs are found
    # These files store the traded pairs and the corresponding TradingView watchlist format
    tv_watchlist_file_path = os.path.join(script_dir, "TV-Coinbase-Watchlist.txt")
    if not os.path.exists(pairs_file_path) or not os.path.exists(tv_watchlist_file_path) or new_pairs or moved_to_traded or moved_to_disabled or field_changes:
        with open(pairs_file_path, "w") as file:
            file.write("Traded Pairs:\n")
            for pair in traded_pairs:
                file.write(pair + "\n")
            file.write("\nDisabled Pairs:\n")
            for pair in disabled_pairs:
                file.write(pair + "\n")
        print("pairs.txt has been updated.")
        
        with open(tv_watchlist_file_path, "w") as file:
            for pair in traded_pairs:
                file.write(f"COINBASE:{pair.replace('-', '')},\n")
        print("TV-Coinbase-Watchlist.txt has been updated.")
        
    # Only update active_pairs.txt if changes occurred
    # This file stores all traded pairs with the '-USD' suffix
    active_pairs_file_path = os.path.join(script_dir, "active_pairs.txt")
    previous_active_pairs = set()
    try:
        with open(active_pairs_file_path, "r") as file:
            previous_active_pairs = set(file.read().splitlines())
    except FileNotFoundError:
        print("active_pairs.txt not found, creating a new one.")

    # Keep the '-USD' suffix and sort pairs alphabetically
    current_active_pairs = sorted(traded_pairs)
    if set(current_active_pairs) != previous_active_pairs:
        with open(active_pairs_file_path, "w") as file:
            for pair in current_active_pairs:
                file.write(pair + "\n")
        print("active_pairs.txt has been updated with traded pairs sorted alphabetically.")

    # Update active_pairs_no_usd.txt similarly to active_pairs.txt but without the '-USD' suffix
    # This file stores the traded pairs without the '-USD' suffix, useful for certain applications
    active_pairs_no_usd_file_path = os.path.join(script_dir, "active_pairs_no_usd.txt")
    previous_active_pairs_no_usd = set()
    try:
        with open(active_pairs_no_usd_file_path, "r") as file:
            previous_active_pairs_no_usd = set(file.read().splitlines())
    except FileNotFoundError:
        print("active_pairs_no_usd.txt not found, creating a new one.")

    # Remove '-USD' from each traded pair and sort them alphabetically
    current_active_pairs_no_usd = sorted(pair.replace('-USD', '') for pair in traded_pairs)
    if set(current_active_pairs_no_usd) != previous_active_pairs_no_usd:
        with open(active_pairs_no_usd_file_path, "w") as file:
            for pair in current_active_pairs_no_usd:
                file.write(pair + "\n")
        print("active_pairs_no_usd.txt has been updated with traded pairs without the '-USD' suffix.")

    # Save new pairs with the date they were found to new_pairs.txt
    # This helps in keeping track of when new pairs are introduced
    new_pairs_file_path = os.path.join(script_dir, "new_pairs.txt")
    if new_pairs:
        with open(new_pairs_file_path, "a") as file:
            for pair in new_pairs:
                file.write(f"{datetime.now().strftime('%m-%d-%y %H:%M:%S')} - {pair}\n")
        content = ""
        for pair in new_pairs:
            if pair in traded_pairs:
                content += f"{mentionrole} [Enabled] {pair} has been detected.\n<https://www.coinbase.com/advanced-trade/spot/{pair}>\n"
            else:
                content += f"{mentionrole} [Disabled] {pair} has been detected.\n"
        send_discord_notification(content)
        print("new_pairs.txt has been updated with new pairs.")
    
    # Log and notify about pairs moving between traded and disabled
    # This logs the pairs that have been enabled or disabled and notifies via Discord
    activations_file_path = os.path.join(script_dir, "activations.txt")
    if moved_to_traded or moved_to_disabled:
        content = ""
        with open(activations_file_path, "a") as file:
            if moved_to_traded:
                for pair in moved_to_traded:
                    log = f"{datetime.now().strftime('%m-%d-%y %H:%M:%S')} - {pair} has been enabled\n"
                    file.write(log)
                    content += f"{mentionrole} {pair} trading has been enabled.\n<https://www.coinbase.com/advanced-trade/spot/{pair}>\n"
            if moved_to_disabled:
                for pair in moved_to_disabled:
                    log = f"{datetime.now().strftime('%m-%d-%y %H:%M:%S')} - {pair} has been disabled\n"
                    file.write(log)
                    content += f"{mentionrole} {pair} trading has been disabled.\n"
        if content:
            send_discord_notification(content)
        print("activations.txt has been updated with changes in pair status.")
    
    # Log and notify about changes in specified fields
    # This section detects changes in fields like 'post_only', 'limit_only', etc., and notifies via Discord
    field_changes_file_path = os.path.join(script_dir, "field_changes.txt")
    fields_status_file_path = os.path.join(script_dir, "fields_status.txt")
    if field_changes:
        content = ""
        with open(field_changes_file_path, "a") as file:
            for pair_id, changes in field_changes.items():
                for field, value in changes.items():
                    if field == 'status_message' and value == "":
                        continue  # Skip notification for blank status_message
                    log = f"{datetime.now().strftime('%m-%d-%y %H:%M:%S')} - {pair_id} {field} changed to {value}\n"
                    file.write(log)
                    if field in ['post_only', 'limit_only', 'cancel_only']:
                        content += f"{mentionrole} {pair_id} {field.replace('_', ' ')} has been {'enabled' if value == 'true' else 'disabled'}.\n<https://www.coinbase.com/advanced-trade/spot/{pair_id}>\n"
                    elif field == 'status':
                        if value == 'online':
                            content += f"{mentionrole} {pair_id} is now online\n<https://www.coinbase.com/advanced-trade/spot/{pair_id}>\n"
                        else:
                            content += f"{mentionrole} {pair_id} is now {value}.\n"
                    elif field == 'status_message':
                        content += f"{mentionrole} {pair_id} status updated: {value}.\n<https://www.coinbase.com/advanced-trade/spot/{pair_id}>\n"
                    elif field == 'trading_disabled':
                        if value.lower() == 'true':
                            content += f"{mentionrole} {pair_id} trading has been disabled.\n"
                        else:
                            content += f"{mentionrole} {pair_id} trading has been enabled.\n<https://www.coinbase.com/advanced-trade/spot/{pair_id}>\n"
                    elif field == 'auction_mode':
                        content += f"{mentionrole} {pair_id} auction mode has {'started' if value == 'true' else 'ended'}.\n<https://www.coinbase.com/advanced-trade/spot/{pair_id}>\n"

        if content:  # Only send notification if there's content
            send_discord_notification(content)
            print("field_changes.txt has been updated with changes in specified fields.")
            print("Discord notification sent successfully.")

        # Update the fields_status file with the current statuses to prevent repeated notifications
        # Alphabetize by pair_id for consistency
        sorted_pairs = sorted(current_fields_status.items())
        with open(fields_status_file_path, "w") as file:
            for pair_id, statuses in sorted_pairs:
                file.write(f"{pair_id}:{','.join(f'{k}={v}' for k, v in statuses.items())}\n")
        print("fields_status.txt has been updated.")

    # Print results only if there are new pairs or changes in pair status or fields
    elapsed_time = (time.time() - start_time) * 1000  # Calculate elapsed time in milliseconds
    if new_pairs or moved_to_traded or moved_to_disabled or field_changes:
        if new_pairs:
            print("New pairs found:")
            for pair in new_pairs:
                print(f"{datetime.now().strftime('%m-%d-%y %H:%M:%S')} - {pair}")
        if moved_to_traded:
            print("Pairs Enabled:")
            for pair in moved_to_traded:
                print(f"{datetime.now().strftime('%m-%d-%y %H:%M:%S')} - {pair}")
        if moved_to_disabled:
            print("Pairs Disabled:")
            for pair in moved_to_disabled:
                print(f"{datetime.now().strftime('%m-%d-%y %H:%M:%S')} - {pair}")
        if field_changes:
            print("Field changes:")
            for pair_id, changes in field_changes.items():
                for field, value in changes.items():
                    print(f"{datetime.now().strftime('%m-%d-%y %H:%M:%S')} - {pair_id} {field} changed to {value}")
    else:
        print(f"{datetime.now().strftime('%m-%d-%y %H:%M:%S')} - {elapsed_time:.2f} ms - No new pairs found this scan.")

# Main loop: The script continuously runs and fetches USD pairs from Coinbase Pro API every 2 seconds
if __name__ == "__main__":
    fetch_usd_pairs()  # Ensure the files are created/updated on the first run
    while True:
        fetch_usd_pairs()
        time.sleep(2)  # Wait for 2 seconds before running again
