import os
import re
import time
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------
DEBUG_MODE = False  # Set to True to enable extra [DEBUG] prints
ALERTED_FIELDS_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), "alerted_fields.json")
# ---------------------------------------------------------------------

# Load environment variables from .env file
load_dotenv()

# Your Discord webhook URL and role mention
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
MENTION_ROLE = os.getenv('MENTION_ROLE')

# Files used by the script
script_dir = os.path.dirname(os.path.realpath(__file__))
pairs_file_path = os.path.join(script_dir, "pairs.txt")
fields_status_file_path = os.path.join(script_dir, "fields_status.txt")

def send_discord_notification(content):
    """Sends a notification to Discord using the provided webhook URL."""
    if content.strip():
        data = {"content": content}
        try:
            response = requests.post(DISCORD_WEBHOOK_URL, json=data)
            if response.status_code == 204:
                print("Discord notification sent successfully.")
            else:
                print(f"Failed to send Discord notification. Status code: {response.status_code}")
        except Exception as e:
            print(f"Error sending Discord notification: {e}")

def robust_normalize_value(value):
    """
    Normalizes a value by stripping whitespace, replacing fancy quotes/zero-width characters,
    and collapsing multiple spaces into one.
    """
    value = value.strip()
    value = value.replace('’', "'").replace('\u200b', '')
    value = value.replace('“', '"').replace('”', '"')
    value = re.sub(r'\s+', ' ', value)
    return value

def normalize_status_message(value):
    """
    Further normalizes a status message by applying robust normalization and then
    replacing commas with periods so that messages with a comma or period are treated equally.
    """
    norm_val = robust_normalize_value(value)
    norm_val = norm_val.replace(",", ".")
    return norm_val

def load_baseline(filename):
    """Loads the baseline from a file into a dictionary."""
    baseline = {}
    try:
        with open(filename, "r") as file:
            for line in file:
                if ':' not in line:
                    continue
                pair_id, statuses_str = line.strip().split(":", 1)
                baseline[pair_id] = {}
                for entry in statuses_str.split(","):
                    if "=" in entry:
                        k, v = entry.split("=", 1)
                        baseline[pair_id][k.strip()] = robust_normalize_value(v.strip())
    except FileNotFoundError:
        if DEBUG_MODE:
            print("[DEBUG] Baseline file not found, will create a new one.")
    return baseline

def save_baseline(baseline, filename):
    """Saves the baseline dictionary to a file."""
    with open(filename, "w") as file:
        for pair_id, statuses in sorted(baseline.items()):
            line = f"{pair_id}:{','.join(f'{k}={v}' for k, v in statuses.items())}\n"
            file.write(line)

def load_alerted_fields(filename):
    """Loads the persistent alerted fields (for status_message only) from a JSON file."""
    if os.path.exists(filename):
        try:
            with open(filename, "r") as f:
                return json.load(f)
        except Exception as e:
            if DEBUG_MODE:
                print(f"[DEBUG] Error loading alerted fields: {e}")
    return {}

def save_alerted_fields(alerted, filename):
    """Saves the persistent alerted fields (for status_message only) to a JSON file."""
    try:
        with open(filename, "w") as f:
            json.dump(alerted, f)
    except Exception as e:
        if DEBUG_MODE:
            print(f"[DEBUG] Error saving alerted fields: {e}")

def fetch_usd_pairs():
    """Fetches USD pairs, detects changes, updates local files, and sends Discord notifications if needed."""
    start_time = time.time()
    url = "https://api.exchange.coinbase.com/products"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Coinbase Pro API: {e}")
        return

    products = response.json()
    if DEBUG_MODE:
        print(f"[DEBUG] Fetched {len(products)} total products.")

    usd_pairs = [p for p in products if p.get('quote_currency') == 'USD']
    if DEBUG_MODE:
        print(f"[DEBUG] Filtered down to {len(usd_pairs)} USD pairs.")

    traded_pairs = sorted([p['id'] for p in usd_pairs if not p.get('trading_disabled', False)])
    disabled_pairs = sorted([p['id'] for p in usd_pairs if p.get('trading_disabled', False)])
    current_traded_pairs = set(traded_pairs)
    current_disabled_pairs = set(disabled_pairs)

    # Load previously saved pairs from pairs.txt.
    previous_traded_pairs = set()
    previous_disabled_pairs = set()
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
        if DEBUG_MODE:
            print("[DEBUG] pairs.txt not found, will create a new one.")

    baseline = load_baseline(fields_status_file_path)
    alerted_fields = load_alerted_fields(ALERTED_FIELDS_FILE)

    # Build current fields status from API data.
    current_fields_status = {}
    for p in usd_pairs:
        pair_id = p.get('id', '')
        current_fields_status[pair_id] = {
            'post_only': 'true' if p.get('post_only', False) else 'false',
            'limit_only': 'true' if p.get('limit_only', False) else 'false',
            'cancel_only': 'true' if p.get('cancel_only', False) else 'false',
            'trading_disabled': 'true' if p.get('trading_disabled', False) else 'false',
            'auction_mode': 'true' if p.get('auction_mode', False) else 'false',
            'status': robust_normalize_value(str(p.get('status', ''))),
            'status_message': robust_normalize_value(str(p.get('status_message', '')))
        }

    # If no baseline exists, save current as baseline and exit.
    if not baseline:
        save_baseline(current_fields_status, fields_status_file_path)
        save_alerted_fields(alerted_fields, ALERTED_FIELDS_FILE)
        print("Baseline created in fields_status.txt; no alerts on first run.")
        return

    # Determine field changes.
    field_changes = {}
    for pair_id, current_vals in current_fields_status.items():
        if pair_id not in baseline:
            field_changes[pair_id] = current_vals.copy()
        else:
            changes = {}
            for field in ['post_only','limit_only','cancel_only','status','status_message','trading_disabled','auction_mode']:
                if field == 'status_message':
                    current_val = normalize_status_message(current_vals.get(field, ''))
                    baseline_val = normalize_status_message(baseline.get(pair_id, {}).get(field, ''))
                else:
                    current_val = robust_normalize_value(current_vals.get(field, ''))
                    baseline_val = robust_normalize_value(baseline.get(pair_id, {}).get(field, ''))
                if current_val != baseline_val:
                    changes[field] = current_val
            if changes:
                field_changes[pair_id] = changes

    # Determine if pairs have changed from disabled <--> traded.
    new_pairs = (current_traded_pairs | current_disabled_pairs) - (previous_traded_pairs | previous_disabled_pairs)
    moved_to_traded = previous_disabled_pairs & current_traded_pairs
    moved_to_disabled = previous_traded_pairs & current_disabled_pairs

    # We'll track if we actually wrote pairs.txt or watchlist so we don't spam the console.
    wrote_pairs_txt = False
    wrote_watchlist_txt = False

    # Update pairs.txt and TV-Coinbase-Watchlist.txt only if something actually changed.
    need_update_pairs_files = (
        new_pairs or moved_to_traded or moved_to_disabled or field_changes
        or not os.path.exists(pairs_file_path)
    )
    tv_watchlist_file_path = os.path.join(script_dir, "TV-Coinbase-Watchlist.txt")
    if need_update_pairs_files:
        with open(pairs_file_path, "w") as file:
            file.write("Traded Pairs:\n")
            for pair in traded_pairs:
                file.write(pair + "\n")
            file.write("\nDisabled Pairs:\n")
            for pair in disabled_pairs:
                file.write(pair + "\n")
        wrote_pairs_txt = True

        # Update watchlist if needed.
        with open(tv_watchlist_file_path, "w") as file:
            for pair in traded_pairs:
                file.write(f"COINBASE:{pair.replace('-', '')},\n")
        wrote_watchlist_txt = True

    # Update baseline if changed or new pairs or anything relevant.
    # Actually, we do this after we decide if we have changes or not.

    # (Optional) If you have an active_pairs.txt or active_pairs_no_usd.txt, handle them similarly.

    # Handle notifications for new pairs.
    content_for_new_pairs = ""
    if new_pairs:
        new_pairs_file_path = os.path.join(script_dir, "new_pairs.txt")
        with open(new_pairs_file_path, "a") as file:
            for pair in new_pairs:
                file.write(f"{datetime.now().strftime('%m-%d-%y %H:%M:%S')} - {pair}\n")

        for pair in new_pairs:
            if pair in traded_pairs:
                content_for_new_pairs += f"{MENTION_ROLE} [Enabled] {pair} has been detected.\n<https://www.coinbase.com/advanced-trade/spot/{pair}>\n"
            else:
                content_for_new_pairs += f"{MENTION_ROLE} [Disabled] {pair} has been detected.\n"

        send_discord_notification(content_for_new_pairs)

    # Handle activations (moved_to_traded or moved_to_disabled).
    content_for_activations = ""
    if moved_to_traded or moved_to_disabled:
        activations_file_path = os.path.join(script_dir, "activations.txt")
        with open(activations_file_path, "a") as file:
            if moved_to_traded:
                for pair in moved_to_traded:
                    log = f"{datetime.now().strftime('%m-%d-%y %H:%M:%S')} - {pair} has been enabled\n"
                    file.write(log)
                    content_for_activations += f"{MENTION_ROLE} {pair} trading has been enabled.\n<https://www.coinbase.com/advanced-trade/spot/{pair}>\n"
            if moved_to_disabled:
                for pair in moved_to_disabled:
                    log = f"{datetime.now().strftime('%m-%d-%y %H:%M:%S')} - {pair} has been disabled\n"
                    file.write(log)
                    content_for_activations += f"{MENTION_ROLE} {pair} trading has been disabled.\n"

        send_discord_notification(content_for_activations)

    # --- Handle field_changes notifications ---
    notification_content = ""
    field_changes_file_path = os.path.join(script_dir, "field_changes.txt")
    changes_occurred = False  # track if *any* real changes occurred

    if field_changes:
        with open(field_changes_file_path, "a") as file:
            for pair_id, changes_dict in field_changes.items():
                for field, new_value in changes_dict.items():
                    # Skip empty status_message.
                    if field == 'status_message' and not new_value:
                        continue

                    changes_occurred = True
                    if field == 'status_message':
                        norm_new_value = normalize_status_message(new_value)
                        alerted_val = alerted_fields.get(pair_id, {}).get('status_message', '')
                        if norm_new_value == alerted_val:
                            # Already alerted this exact status_message
                            continue
                    else:
                        norm_new_value = robust_normalize_value(new_value)

                    log_line = f"{datetime.now().strftime('%m-%d-%y %H:%M:%S')} - {pair_id} {field} changed to {norm_new_value}\n"
                    file.write(log_line)

                    # Build Discord message using Markdown link formatting.
                    link = f"[{pair_id}](<https://www.coinbase.com/advanced-trade/spot/{pair_id}-USD>)"
                    if field in ['post_only','limit_only','cancel_only']:
                        status = 'enabled' if norm_new_value == 'true' else 'disabled'
                        description = f"{field.replace('_', ' ')} has been {status}"
                    elif field == 'status':
                        if norm_new_value.lower() == 'online':
                            description = "is now online"
                        else:
                            description = f"status changed to {norm_new_value}"
                    elif field == 'status_message':
                        description = f"status updated: {norm_new_value}"
                    elif field == 'trading_disabled':
                        if norm_new_value.lower() == 'true':
                            description = "trading has been disabled"
                        else:
                            description = "trading has been enabled"
                    elif field == 'auction_mode':
                        auction_status = 'started' if norm_new_value.lower() == 'true' else 'ended'
                        description = f"auction mode has {auction_status}"
                    # Append the formatted message.
                    notification_content += f"{MENTION_ROLE} {link} - {description}\n"

                    if field == 'status_message':
                        if pair_id not in alerted_fields:
                            alerted_fields[pair_id] = {}
                        alerted_fields[pair_id]['status_message'] = norm_new_value

    # Send Discord notification if there's content
    if notification_content.strip():
        send_discord_notification(notification_content)
        changes_occurred = True

    # Save updated baseline and persistent alerted fields.
    save_baseline(current_fields_status, fields_status_file_path)
    save_alerted_fields(alerted_fields, ALERTED_FIELDS_FILE)

    # Minimal console output:
    # Only print if we actually changed pairs.txt/watchlist, or if we had changes, otherwise 1 line.
    if wrote_pairs_txt:
        print("pairs.txt has been updated.")
    if wrote_watchlist_txt:
        print("TV-Coinbase-Watchlist.txt has been updated.")

    elapsed_time = (time.time() - start_time) * 1000
    if changes_occurred or new_pairs or moved_to_traded or moved_to_disabled or wrote_pairs_txt or wrote_watchlist_txt:
        # If something actually changed or was updated:
        if field_changes:
            # Print "Field changes:" only if there's actual changes we wrote
            # The loop above might skip status_message if repeated. So let's see if any fields remain.
            real_changes = {}
            for pid, chdict in field_changes.items():
                # Filter out "status_message" if we didn't actually alert it
                filtered = {}
                for f, val in chdict.items():
                    if f == 'status_message':
                        # Did we skip it? check if we alerted
                        norm_new_value = normalize_status_message(val)
                        old_alerted = alerted_fields.get(pid, {}).get('status_message', None)
                        if norm_new_value != old_alerted:
                            filtered[f] = val
                    else:
                        # Always include other fields
                        filtered[f] = val
                if filtered:
                    real_changes[pid] = filtered

            if real_changes:
                print("Field changes:")
                for pid, cdict in real_changes.items():
                    for fld, val in cdict.items():
                        if fld == 'status_message':
                            continue  # skip flooding console for status_message
                        print(f"{datetime.now().strftime('%m-%d-%y %H:%M:%S')} - {pid} {fld} changed to {val}")

    else:
        # If truly no new changes
        print(f"{datetime.now().strftime('%m-%d-%y %H:%M:%S')} - No new pairs or changes detected this scan.")

if __name__ == "__main__":
    # First run establishes baseline.
    fetch_usd_pairs()
    while True:
        fetch_usd_pairs()
        time.sleep(10)  # Adjust as needed.
