import sqlite3
import hashlib
import streamlit as st
from supabase import create_client, Client

# --- SUPABASE CONNECTION CONFIGURATION ---
@st.cache_resource
def get_supabase() -> Client:
    """Establishes a secure, cached connection to the Supabase cloud instance."""
    url = st.secrets["supabase"]["SUPABASE_URL"]
    key = st.secrets["supabase"]["SUPABASE_KEY"]
    return create_client(url, key)

def make_hashes(password: str) -> str:
    """Secures passwords using standard cryptographic SHA-256 hashing."""
    return hashlib.sha256(str.encode(password)).hexdigest()

# --- SECURE AUTHENTICATION GATEWAY ---
def authenticate_user(email: str, password_plain: str):
    """Verifies credentials against Supabase cloud records. Returns (logged_in, is_admin)."""
    try:
        supabase = get_supabase()
        hashed = make_hashes(password_plain)
        response = supabase.table("users").select("password_hash", "is_admin").eq("email", email).execute()
        if response.data:
            user_record = response.data[0]
            if user_record["password_hash"] == hashed:
                return True, bool(user_record["is_admin"])
        return False, False
    except Exception:
        return False, False

# --- LOCAL-FIRST FLOOR PERSISTENCE ENGINE (ANTI-TIMEOUT GUARD) ---
def init_local_db():
    """Initializes a local database mirror tasked with screen data preservation."""
    conn = sqlite3.connect("local_persistence_cache.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS screen_cache (
            email TEXT,
            field_key TEXT,
            field_value TEXT,
            PRIMARY KEY (email, field_key)
        )
    """)
    conn.commit()
    conn.close()

def force_save_field(email: str, field_key: str, field_value: str):
    """Immediately commits unsubmitted input data directly to local disk space."""
    conn = sqlite3.connect("local_persistence_cache.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO screen_cache (email, field_key, field_value)
        VALUES (?, ?, ?)
    """, (email, field_key, field_value))
    conn.commit()
    conn.close()

def force_load_field(email: str, field_key: str, default_value: str) -> str:
    """Retrieves cached text fields from local storage to survive browser timeouts."""
    conn = sqlite3.connect("local_persistence_cache.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT field_value FROM screen_cache WHERE email=? AND field_key=?", (email, field_key))
    row = c.fetchone()
    conn.close()
    return row[0] if row else default_value

def clear_floor_inputs(email: str):
    """Wipes the local screen cache completely upon a successful transaction entry."""
    conn = sqlite3.connect("local_persistence_cache.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("DELETE FROM screen_cache WHERE email=?", (email,))
    conn.commit()
    conn.close()

# --- CLOUD TRANSACTION LEDGER OPERATIONS (SUPABASE) ---
def cloud_log_transaction(email: str, category: str, notes: str, timestamp: str):
    """Pushes a verified single transaction directly into the Supabase remote ledger."""
    supabase = get_supabase()
    data = {"email": email, "category": category, "notes": notes, "timestamp": timestamp}
    supabase.table("sales_tracker").insert(data).execute()

def cloud_fetch_transactions(email: str):
    """Retrieves all isolated historical transaction data for the logged-in user identity."""
    supabase = get_supabase()
    response = supabase.table("sales_tracker").select("*").eq("email", email).order("timestamp", desc=True).execute()
    return response.data if response.data else []

def cloud_update_transaction(tx_id: int, new_category: str, new_notes: str, new_timestamp: str):
    """Overwrites an existing cloud ledger record with corrected data (e.g. retroactive date fixes)."""
    supabase = get_supabase()
    data = {"category": new_category, "notes": new_notes, "timestamp": new_timestamp}
    supabase.table("sales_tracker").update(data).eq("id", tx_id).execute()

def cloud_delete_transaction(tx_id: int):
    """Permanently clears a specific record from the cloud ledger via its unique identifier."""
    supabase = get_supabase()
    supabase.table("sales_tracker").delete().eq("id", tx_id).execute()

# --- PERFORMANCE TARGETS & RUN-RATES (SUPABASE) ---
def cloud_fetch_targets(email: str):
    """Gathers individualized volume targets and remaining shift tallies from cloud records."""
    supabase = get_supabase()
    t_res = supabase.table("kpi_settings").select("kpi_key", "target_val").eq("email", email).execute()
    s_res = supabase.table("performance_targets").select("shifts_left").eq("email", email).execute()
    targets = {row["kpi_key"]: float(row["target_val"]) for row in t_res.data} if t_res.data else {}
    shifts = s_res.data[0]["shifts_left"] if s_res.data else 1
    return targets, shifts

def cloud_save_targets(email: str, target_dict: dict, shifts_left: int):
    """Saves custom operational configurations securely back to the cloud instance."""
    supabase = get_supabase()
    for kpi, val in target_dict.items():
        supabase.table("kpi_settings").upsert({"email": email, "kpi_key": kpi, "target_val": val}).execute()
    supabase.table("performance_targets").upsert({"email": email, "shifts_left": shifts_left}).execute()

# --- GLOBAL ADMIN CONTROL CENTER FUNCTIONS (SUPABASE) ---
def cloud_fetch_kpi_definitions():
    """Reads active global business performance rules dictated exclusively by administrators."""
    supabase = get_supabase()
    response = supabase.table("kpi_definitions").select("*").order("id", desc=False).execute()
    return response.data if response.data else []

def cloud_save_kpi_definitions(definitions_list: list):
    """Updates overarching metric parameters globally across every client instance."""
    supabase = get_supabase()
    for item in definitions_list:
        supabase.table("kpi_definitions").upsert(item).execute()