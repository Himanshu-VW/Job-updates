from google import genai
import hashlib
import os
import requests


# Configuration from Environment Variables
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# List the career pages you want to monitor
CAREER_URLS = [
    "https://apply.careers.microsoft.com/careers"  # Replace with actual target career page URL
]

def send_telegram_message(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials missing.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def check_pages():
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    for url in CAREER_URLS:
        try:
            # 1. Fetch the career page HTML/Text
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            response = requests.get(url, headers=headers, timeout=15)
            page_text = response.text
            
            # 2. Check hash to see if text changed
            page_hash = hashlib.md5(page_text.encode('utf-8')).hexdigest()
            filename = f"cache_{hashlib.md5(url.encode('utf-8')).hexdigest()}.txt"
            
            old_hash = ""
            if os.path.exists(filename):
                with open(filename, "r") as f:
                    old_hash = f.read().strip()
            
            if page_hash == old_hash:
                print(f"No changes detected for: {url}")
                continue
                
            print(f"Change detected on {url}! Analyzing with AI...")
            
            # 3. Use Gemini to parse new roles cleanly
            prompt = f"""
            Analyze the following text extracted from a company career page. 
            Identify if there are any active job openings (especially looking for Software, AI, Data, or tech roles).
            Extract the Job Titles, Locations, and any direct application links found.
            
            Page text snippet:
            {page_text[:15000]}  # Truncate to token safety limits
            
            If there are new listings, format them clearly in markdown. If none, say "No relevant open roles found."
            """
            
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=prompt,
            )
            
            # 4. Notify via Telegram
            alert_text = f"🚨 *Career Page Update!*\nURL: {url}\n\n{response.text}"
            send_telegram_message(alert_text)
            
            # 5. Update cache hash
            with open(filename, "w") as f:
                f.write(page_hash)
                
        except Exception as e:
            print(f"Error checking {url}: {e}")

if __name__ == "__main__":
    check_pages()
