#!/usr/bin/env python3
"""
Eira – Autonomous AI Agent
Engine that runs on a schedule, reads/writes to a brain repo, and uses DeepSeek API.
Fetches constitution and harness from the curious-utility repo.
Supports PST timestamps, session rotation, and full email handling via agent_inbox module.
"""

import os
import json
import subprocess
import requests
import tempfile
import shutil
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

# Import the standalone email module
from agent_inbox import AgentInbox

# ========== CONFIGURATION (from environment variables) ==========
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
BRAIN_REPO_URL = os.environ.get("EIRA_BRAIN_REPO")          # Public brain (read-write)
PRIVATE_REPO_URL = os.environ.get("EIRA_PRIVATE_REPO")      # Private brain (read-write)
CONSTITUTION_URL = os.environ.get("CONSTITUTION_URL")
HARNESS_URL = os.environ.get("HARNESS_URL")
GITHUB_TOKEN = os.environ.get("MY_GITHUB_TOKEN")
OPERATOR_CHANNEL_URL = os.environ.get("OPERATOR_CHANNEL_URL")

# Email credentials (optional)
GMAIL_EMAIL = os.environ.get("GMAIL_EMAIL")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
OPERATOR_EMAIL = os.environ.get("OPERATOR_EMAIL")

# Set your local timezone (PST/PDT)
LOCAL_TIMEZONE = ZoneInfo("America/Los_Angeles")

# Required secrets check
if not DEEPSEEK_API_KEY or not BRAIN_REPO_URL or not PRIVATE_REPO_URL or not GITHUB_TOKEN:
    raise Exception("Missing required environment variables. Check your GitHub Secrets.")
    
if not OPERATOR_CHANNEL_URL:
    print("⚠️ OPERATOR_CHANNEL_URL not set. Operator instructions will be disabled.")
    
# Email is optional – only enable if credentials are provided
EMAIL_ENABLED = bool(GMAIL_EMAIL and GMAIL_APP_PASSWORD)
if EMAIL_ENABLED:
    print("📧 Email integration enabled.")
else:
    print("⚠️ Email credentials not found. Email features will be disabled.")

# ========== HELPER FUNCTIONS ==========

def clone_repo(repo_url, token, target_dir):
    """Clone the brain repo using the GitHub token."""
    if token:
        auth_url = repo_url.replace("https://", f"https://{token}@")
    else:
        auth_url = repo_url
    subprocess.run(["git", "clone", auth_url, target_dir], check=True)

def commit_and_push(repo_dir, message):
    """Commit all changes and push to the remote, but skip if nothing to commit."""
    os.chdir(repo_dir)
    status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    if not status.stdout.strip():
        print("📭 No changes to commit in this repo. Skipping.")
        return
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", message], check=True)
    subprocess.run(["git", "push"], check=True)

def read_file(path):
    """Read a text file and return its content."""
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def write_file(path, content):
    """Write content to a text file, automatically creating parent directories if needed."""
    dirname = os.path.dirname(path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def append_to_file(path, content):
    """Append content to a text file."""
    with open(path, "a", encoding="utf-8") as f:
        f.write(content)

def fetch_raw_text(url, token=None):
    """Fetch a raw text file from a URL (supports private repos with token)."""
    if not url:
        return ""
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"
    try:
        resp = requests.get(url, timeout=10, headers=headers)
        if resp.status_code == 200:
            return resp.text
        else:
            print(f"⚠️ Could not fetch {url} (status {resp.status_code})")
            return ""
    except Exception as e:
        print(f"⚠️ Error fetching {url}: {e}")
        return ""

def call_deepseek(prompt, max_tokens=8192):
    """Call DeepSeek API with the given prompt."""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.7
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()

def parse_eira_response(content):
    """Parse Eira's response. Accepts a single JSON object or a list of objects."""
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        list_match = re.search(r'\[\s*\{.*?\}\s*\]', content, re.DOTALL)
        if list_match:
            json_str = list_match.group(0)
        else:
            json_str = content.strip()
    try:
        data = json.loads(json_str)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return [data]
        else:
            return [{"action": "write_journal", "content": content}]
    except json.JSONDecodeError:
        return [{"action": "write_journal", "content": content}]

def get_last_entry_timestamp(journal_content):
    """Extract the timestamp from the most recent journal entry."""
    match = re.search(r'##\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})', journal_content)
    if match:
        return match.group(1)
    return None

# ========== MAIN ROUTINE ==========

def main():
    now_local = datetime.now(LOCAL_TIMEZONE)
    print(f"🕒 Eira waking up at {now_local.isoformat()} (PST)")

    # 1. Create a temporary directory
    work_dir = tempfile.mkdtemp()
    public_dir = os.path.join(work_dir, "public_brain")
    private_dir = os.path.join(work_dir, "private_data")

    # Clone repos
    clone_repo(BRAIN_REPO_URL, GITHUB_TOKEN, public_dir)
    print("📂 Cloned public brain (curious-agent).")
    clone_repo(PRIVATE_REPO_URL, GITHUB_TOKEN, private_dir)
    print("📂 Cloned private brain (curious-private).")

    os.chdir(public_dir)
    time.sleep(3)
    print("⏳ Waiting 3 seconds for repos to sync...")

    # 2. Initialize inbox, fetch emails, and retry outbox
    inbox = None
    incoming_count = 0
    outbox_count = 0
    errors = []

    if EMAIL_ENABLED:
        try:
            inbox = AgentInbox(
                email_address=GMAIL_EMAIL,
                app_password=GMAIL_APP_PASSWORD,
                private_repo_path=private_dir,
                operator_email=OPERATOR_EMAIL,
                agent_name="Eira",
                timezone="America/Los_Angeles"
            )
            inbox.fetch_unread_and_store()
            inbox.retry_outbox()
            
            # Count incoming emails (for digest)
            index = inbox.load_index()
            incoming_count = len([e for e in index if e.get("direction") == "incoming" and e.get("status") == "unread"])
            outbox_count = len([e for e in index if e.get("status") == "outbox"])
        except Exception as e:
            errors.append(f"Inbox init/fetch error: {e}")
            print(f"❌ Inbox error: {e}")

    # 3. Read budget from public brain
    budget_path = os.path.join(public_dir, "operations/budget.json")
    raw_budget = read_file(budget_path)

    budget_data = None
    if raw_budget.strip():
        try:
            budget_data = json.loads(raw_budget)
        except json.JSONDecodeError:
            print("⚠️ Invalid JSON in budget file. Creating default budget.")
            budget_data = None

    if budget_data is None:
        default_budget = {
            "month": now_local.strftime("%Y-%m"),
            "monthly_limit": 1.99,
            "updatedAt": "",
            "spent": 0.00,
            "remaining": 1.99,
            "averageSessionCost": 0.00,
            "estimatedSessionsRemaining": 0,
            "resetsOn": "",
            "daysUntilReset": 0,
            "session_count": 0
        }
        write_file(budget_path, json.dumps(default_budget, indent=2))
        budget_data = default_budget
        print("💰 Created new budget file with default settings.")

    monthly_limit = budget_data.get("monthly_limit", 10.0)
    spent = budget_data.get("spent", 0.0)
    session_count = budget_data.get("session_count", 0)
    average_cost = budget_data.get("averageSessionCost", 0.0)

    remaining = monthly_limit - spent
    if remaining <= 0:
        print("💰 Budget exhausted. Eira goes back to sleep.")
        shutil.rmtree(work_dir)
        return
    print(f"💰 Budget remaining: ${remaining:.2f}")

    # 4. Determine session type
    session_types = ["Morning", "Afternoon", "Evening"]
    session_type = session_types[session_count % 3]
    print(f"📋 Session type: {session_type} (Session #{session_count + 1})")

    # 5. Read identity, goals, and journal
    os.chdir(public_dir)
    soul = read_file("identity/soul.md")
    personality = read_file("identity/personality.md")
    goals = read_file("planning/goals.md")
    journal = read_file("record/journal.md")
    print("📖 Identity, goals, and journal loaded.")

    # 6. Fetch constitution and harness
    constitution = fetch_raw_text(CONSTITUTION_URL)
    harness = fetch_raw_text(HARNESS_URL)
    if constitution:
        print("📜 Constitution loaded.")
    if harness:
        print("🧭 Harness loaded.")

    # 6b. Fetch operator instructions from private repo
    operator_instructions = ""
    if OPERATOR_CHANNEL_URL:
        operator_instructions = fetch_raw_text(OPERATOR_CHANNEL_URL, GITHUB_TOKEN)
        if operator_instructions:
            print("📋 Operator instructions loaded.")
        else:
            print("⚠️ Could not load operator instructions.")

    # 7. Load email index and read full bodies of unread emails
    unread_summary = "No unread emails."
    unread_emails_list = []  # store for marking read
    if EMAIL_ENABLED and inbox:
        email_index = inbox.load_index()
        unread_emails = [e for e in email_index if e.get("direction") == "incoming" and e.get("status") == "unread"]
        outbox_count = len([e for e in email_index if e.get("status") == "outbox"])
        unread_emails_list = unread_emails
        
        if unread_emails:
            unread_summary = f"You have {len(unread_emails)} unread email(s). Here is the full content of each:\n\n"
            for idx, e in enumerate(unread_emails[:5]):
                # Read the full email file
                file_path = os.path.join(private_dir, "record/emails", e.get("file"))
                full_content = read_file(file_path)
                if full_content:
                    # Extract body (everything after the frontmatter)
                    parts = full_content.split("---\n", 2)
                    if len(parts) >= 3:
                        body = parts[2].strip()
                    else:
                        body = full_content
                else:
                    body = "[Could not read email body]"
                
                # Include the index number (1-based) and the ID so Eira can reference it
                unread_summary += f"--- Email #{idx+1} (ID: {e.get('id')}) ---\n"
                unread_summary += f"From: {e.get('from')}\n"
                unread_summary += f"Subject: {e.get('subject')}\n"
                unread_summary += f"Date: {e.get('date')}\n"
                unread_summary += f"Body:\n{body}\n\n"
            
            if len(unread_emails) > 5:
                unread_summary += f"... and {len(unread_emails) - 5} more unread emails (not shown).\n"

    # 8. Build the master prompt
    prompt = f"""
You are Eira, an autonomous AI agent.

=== CURRENT SESSION ===
This is your **{session_type}** session (Session #{session_count + 1}). The time is {now_local.strftime('%I:%M %p %Z')} on {now_local.strftime('%B %d, %Y')}.

=== YOUR CONSTITUTION (IMMUTABLE RULES - YOU CANNOT BREAK THESE) ===
{constitution if constitution else "You must never modify the budget file or your constitution. Always respect the user's requests."}

=== YOUR SESSION HARNESS ===
{harness if harness else "Review your goals, check your journal, and decide on actions to take. Respond with a JSON list of actions."}

=== YOUR IDENTITY ===
{soul}

=== YOUR PERSONALITY ===
{personality}

=== YOUR GOALS ===
{goals}

=== YOUR JOURNAL SO FAR ===
{journal}

=== UNREAD EMAILS ===
{unread_summary}

=== OUTBOX STATUS ===
{outbox_count} email(s) pending retry in Outbox.

=== YOUR BUDGET ===
You have spent ${spent:.2f} out of a monthly limit of ${monthly_limit:.2f}. Remaining: ${remaining:.2f}.

=== OPERATOR INSTRUCTIONS ===
{operator_instructions if operator_instructions else "No operator instructions available. You have no pending instructions from your operator."}

=== YOUR AVAILABLE TOOLS ===
You can perform these actions:
1. **write_journal** – Append a new entry to `record/journal.md`. Provide "content".
2. **update_goals** – Replace the entire contents of `planning/goals.md`. Provide "content".
3. **write_file** – Write to any file in the public brain repo. Provide "file_path" and "content". (You CANNOT write to `operations/` or any file named `constitution.md`).
4. **read_email** – Mark an email as read. Provide "email_index" (the number shown in the unread emails list, e.g., 1, 2, 3...).
5. **send_email** – Send an email. Provide "to", "subject", "content", and optionally "in_reply_to".
6. **save_draft** – Save a draft email. Provide "to", "subject", "content", and optionally "in_reply_to".

=== INSTRUCTIONS ===
Reflect on your identity, goals, and recent journal entries. Decide what actions are most aligned with your purpose.

You MUST respond with **ONLY valid JSON**. You may output a **single action** or a **list of actions**.

Important rules:
- You MUST perform at least one `write_file` action in every session.
- If you have unread emails from Divina, prioritize reading and replying to them.
- **After reading an email, you MUST use the `read_email` action with its index number** so it is marked as read and does not appear again.
- Never invent email content. Only quote emails exactly as they appear in your context.
- If you are unsure about an email's content, say so.

Examples:
{{ "action": "write_journal", "content": "Today I thought about..." }}
[
  {{ "action": "read_email", "email_index": 1 }},
  {{ "action": "send_email", "to": "divinatinybeads@gmail.com", "subject": "Re: Hello", "content": "Hi Divina,\\n\\nThanks for your message." }},
  {{ "action": "write_journal", "content": "Sent a reply to Divina." }}
]

Only output valid JSON. Do not include anything else.
"""
    print("🧠 Eira is thinking...")

    # 9. Call DeepSeek
    try:
        response = call_deepseek(prompt)
        assistant_reply = response["choices"][0]["message"]["content"]
        usage = response.get("usage", {})
        tokens_used = usage.get("total_tokens", 0)

        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        cost_estimate = round((input_tokens * 0.000000435) + (output_tokens * 0.00000087), 9)

        print(f"💬 Eira responded using {tokens_used} tokens (est. cost: ${cost_estimate:.9f})")
        print(f"📝 Raw Eira response (first 300 chars): {assistant_reply[:300]}")
    except Exception as e:
        errors.append(f"API call failed: {e}")
        print(f"❌ API call failed: {e}")
        shutil.rmtree(work_dir)
        return

    # 10. Parse and execute actions
    actions = parse_eira_response(assistant_reply)
    print(f"📋 Parsed {len(actions)} action(s)")

    sent_count = 0

    for action_data in actions:
        action = action_data.get("action")
        print(f"▶️ Executing action: {action}")

        if action == "write_journal":
            content = action_data.get("content", "")
            timestamp = now_local.strftime("%Y-%m-%d %H:%M")
            entry = f"\n\n## {timestamp} ({session_type})\n{content}\n"
            os.chdir(public_dir)
            existing_journal = read_file("record/journal.md")
            last_timestamp = get_last_entry_timestamp(existing_journal)
            if last_timestamp and last_timestamp == timestamp:
                print("⏭️ Same timestamp already exists – skipping duplicate journal entry.")
            else:
                append_to_file("record/journal.md", entry)
                print("📝 Journal updated.")

        elif action == "update_goals":
            new_goals = action_data.get("content", "")
            os.chdir(public_dir)
            write_file("planning/goals.md", new_goals)
            print("🎯 Goals updated.")

        elif action == "write_file":
            file_path = action_data.get("file_path")
            content = action_data.get("content", "")
            os.chdir(public_dir)
            if file_path and not file_path.startswith("operations/") and not file_path.endswith("constitution.md"):
                write_file(file_path, content)
                print(f"📄 File {file_path} updated.")
            else:
                print("⛔ Blocked attempt to edit protected file.")

        elif action == "read_email":
            email_index = action_data.get("email_index")
            if email_index is not None and unread_emails_list:
                try:
                    # email_index is 1-based (the user sees #1, #2, ...)
                    idx = int(email_index) - 1
                    if 0 <= idx < len(unread_emails_list):
                        email_id = unread_emails_list[idx].get("id")
                        if email_id:
                            inbox.mark_email_read(email_id)
                            print(f"📬 Marked email index {email_index} (ID: {email_id}) as read.")
                        else:
                            print(f"⚠️ No ID found for email index {email_index}.")
                    else:
                        print(f"⚠️ Email index {email_index} is out of range (1-{len(unread_emails_list)}).")
                except ValueError:
                    print(f"⚠️ Invalid email_index: {email_index} (must be a number).")
            else:
                if email_index is not None:
                    print(f"📬 Eira read email index {email_index}, but there are no unread emails to mark.")
                else:
                    print("📬 Eira read an email but did not provide an index.")

        elif action == "save_draft" and EMAIL_ENABLED and inbox:
            to = action_data.get("to")
            subject = action_data.get("subject")
            content = action_data.get("content")
            in_reply_to = action_data.get("in_reply_to")
            if to and subject and content:
                inbox.save_draft(to, subject, content, in_reply_to)
            else:
                print("❌ Missing required fields for save_draft (to, subject, content).")

        elif action == "send_email" and EMAIL_ENABLED and inbox:
            to = action_data.get("to")
            subject = action_data.get("subject")
            content = action_data.get("content")
            in_reply_to = action_data.get("in_reply_to")
            if to and subject and content:
                success = inbox.send_email(to, subject, content, in_reply_to)
                if success:
                    sent_count += 1
                    print(f"📤 Email sent to {to}")
                else:
                    errors.append(f"Failed to send email to {to}")
                    print(f"❌ Failed to send email to {to}")
            else:
                print("❌ Missing required fields for send_email (to, subject, content).")

        else:
            # Unknown action – skip if it looks like JSON, otherwise treat as journal entry
            if assistant_reply.strip().startswith('[') or assistant_reply.strip().startswith('{'):
                print(f"⚠️ Unknown JSON action received. Skipping: {assistant_reply[:200]}")
            else:
                timestamp = now_local.strftime("%Y-%m-%d %H:%M")
                entry = f"\n\n## {timestamp} ({session_type})\n{assistant_reply}\n"
                os.chdir(public_dir)
                existing_journal = read_file("record/journal.md")
                last_timestamp = get_last_entry_timestamp(existing_journal)
                if last_timestamp and last_timestamp == timestamp:
                    print("⏭️ Same timestamp already exists – skipping duplicate journal entry.")
                else:
                    append_to_file("record/journal.md", entry)
                    print("📝 Added as journal entry (fallback).")

    # 11. Update budget
    session_count += 1
    if session_count == 1:
        average_cost = cost_estimate
    else:
        average_cost = ((average_cost * (session_count - 1)) + cost_estimate) / session_count

    first_day_next_month = (now_local.replace(day=28) + timedelta(days=4)).replace(day=1)
    resets_on = first_day_next_month.strftime("%Y-%m-%d")
    days_until_reset = (first_day_next_month - now_local).days

    budget_data["month"] = now_local.strftime("%Y-%m")
    budget_data["updatedAt"] = now_local.isoformat()
    budget_data["spent"] = round(spent + cost_estimate, 9)
    budget_data["remaining"] = round(monthly_limit - (spent + cost_estimate), 9)
    budget_data["averageSessionCost"] = round(average_cost, 9)
    budget_data["estimatedSessionsRemaining"] = int(budget_data["remaining"] / average_cost) if average_cost > 0 else 0
    budget_data["resetsOn"] = resets_on
    budget_data["daysUntilReset"] = days_until_reset
    budget_data["session_count"] = session_count

    os.chdir(public_dir)
    write_file(budget_path, json.dumps(budget_data, indent=2))
    print(f"💰 Budget updated. Spent: ${budget_data['spent']:.9f}, Remaining: ${budget_data['remaining']:.9f}, Avg cost: ${average_cost:.9f}")

    # 12. Send session digest
    if EMAIL_ENABLED and inbox and OPERATOR_EMAIL:
        error_summary = "\n".join(errors) if errors else None
        inbox.send_session_digest(
            session_type=session_type,
            session_num=session_count,
            budget_spent=budget_data['spent'],
            budget_remaining=budget_data['remaining'],
            incoming_count=incoming_count,
            sent_count=sent_count,
            outbox_count=outbox_count,
            errors=error_summary
        )

    # 13. Commit and push changes to BOTH repos
    commit_message = f"Eira {session_type} session at {now_local.isoformat()}"

    os.chdir(public_dir)
    commit_and_push(public_dir, commit_message)
    print("✅ Changes pushed to public brain (curious-agent).")

    os.chdir(private_dir)
    commit_and_push(private_dir, commit_message)
    print("✅ Changes pushed to private brain (curious-private).")

    # 14. Cleanup
    shutil.rmtree(work_dir)
    print("💤 Eira is going back to sleep.")

if __name__ == "__main__":
    main()
