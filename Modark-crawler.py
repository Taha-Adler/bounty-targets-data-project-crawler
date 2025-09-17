import os
import requests

# ===============================
# Configuration
# ===============================

# URLs of the files in bounty-targets-data repository
FILES = {
    "domains.txt": "https://raw.githubusercontent.com/arkadiyt/bounty-targets-data/main/data/domains.txt",
    "wildcards.txt": "https://raw.githubusercontent.com/arkadiyt/bounty-targets-data/main/data/wildcards.txt",
}

# Telegram bot settings
BOT_TOKEN = "<BOT-TOKEN>"   # Replace with your bot token
CHAT_ID = "CHAT-ID"         # Replace with your Telegram chat ID


# ===============================
# Helper Functions
# ===============================

def fetch_file(url):
    """
    Fetch the contents of a remote file (domains or wildcards) from GitHub.
    Returns a set of cleaned, lowercase items (lines).
    """
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    items = set()
    for line in r.text.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            items.add(line.lower())
    return items


def read_local(path):
    """
    Read items from a local file.
    Returns a set of lowercase strings.
    """
    if not os.path.exists(path):
        return set()
    with open(path, "r", encoding="utf-8") as f:
        return set(line.strip().lower() for line in f if line.strip())


def write_local(path, items):
    """
    Overwrite a local file with a sorted list of items.
    Used on the first fetch.
    """
    with open(path, "w", encoding="utf-8") as f:
        for item in sorted(items):
            f.write(item + "\n")


def append_local(path, new_items):
    """
    Append new items to the local file.
    Used after detecting updates.
    """
    with open(path, "a", encoding="utf-8") as f:
        for item in sorted(new_items):
            f.write(item + "\n")


def send_telegram(text):
    """
    Send a message to Telegram using httpdebugger.com as a proxy.
    This avoids calling Telegram API directly.
    """
    tg_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={text}"
    payload = {
        "UrlBox": tg_url,
        "AgentList": "Google Chrome",
        "VersionsList": "HTTP/1.1",
        "MethodList": "POST"
    }
    r = requests.post("https://www.httpdebugger.com/Tools/ViewHttpHeaders.aspx", data=payload, timeout=30)
    return r.text


# ===============================
# Main Logic
# ===============================

def main():
    """
    Main process:
    - Fetch domains and wildcards from GitHub
    - Compare with local copies
    - Save updates
    - Send new entries to Telegram
    """
    all_messages = []

    for local_file, url in FILES.items():
        remote_items = fetch_file(url)
        local_items = read_local(local_file)

        if not local_items:
            # First run: store all items locally and notify
            write_local(local_file, remote_items)
            msg = f"Initial fetch for {local_file} ({len(remote_items)} items):\n" + "\n".join(sorted(remote_items))
            all_messages.append(msg)
        else:
            # Subsequent runs: detect and store only new items
            new_items = remote_items - local_items
            if new_items:
                append_local(local_file, new_items)
                msg = f"{len(new_items)} new entries in {local_file}:\n" + "\n".join(sorted(new_items))
                all_messages.append(msg)

    # Send updates to Telegram (if any)
    if all_messages:
        send_telegram("\n\n".join(all_messages))


if __name__ == "__main__":
    main()

