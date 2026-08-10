import streamlit as st
from datetime import datetime
import time
import database as db
import styles as s
import logic_engine as le

# 1. Page Configuration
st.set_page_config(page_title="Lazarus Tools", page_icon="🎯", layout="wide")
db.init_local_db()
s.inject_global_css()

# 2. Session State Setup
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "email" not in st.session_state:
    st.session_state.email = ""
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "active_log_tile" not in st.session_state:
    st.session_state.active_log_tile = None
# --- NEW: Edit Mode Safeguard State ---
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False

# 3. Authentication Routing View
if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    s.render_logo("login")
    st.markdown("<h2 style='text-align: center; margin-bottom: 24px; color: #ffffff;'>Lazarus Tools Command Center</h2>", unsafe_allow_html=True)
    
    _, login_col, _ = st.columns([1, 1.5, 1])
    with login_col:
        with st.form("auth_form", clear_on_submit=False):
            email = st.text_input("Username / Email Address").strip()
            password = st.text_input("Security Password", type="password")
            login_clicked = st.form_submit_button("Authenticate into Command Center")
            
            if login_clicked:
                success, admin_status = db.authenticate_user(email, password)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.email = email
                    st.session_state.is_admin = admin_status
                    st.rerun()
                else:
                    st.error("Authentication Failed. Invalid credentials or network error.")
                    
else:
    # --- APPS/WORKSPACES INNER SCREEN ---
    s.render_logo("sidebar")
    st.sidebar.markdown(f"**User Profile:** \n`👤 {st.session_state.email}`")
    st.sidebar.markdown("---")
    
    kpi_defs = db.cloud_fetch_kpi_definitions()
    
    menu_options = ["🎯 KPI Tracker", "⚙️ My Profile & Shifts"]
    if st.session_state.is_admin:
        menu_options.append("🛠️ Admin Control Center")
        
    choice = st.sidebar.radio("Navigate Platform:", menu_options)
    
    st.sidebar.markdown("---")
    if st.sidebar.button("Secure Logout"):
        st.session_state.logged_in = False
        st.session_state.email = ""
        st.session_state.is_admin = False
        st.session_state.active_log_tile = None
        st.session_state.edit_mode = False
        st.rerun()
        
    user_email = st.session_state.email
    user_targets, shifts_left, period_start = db.cloud_fetch_targets(user_email)
    
    for k in kpi_defs:
        if k["db_code"] not in user_targets:
            user_targets[k["db_code"]] = 0.0

    if choice == "🎯 KPI Tracker":
        st.markdown(f"# 🎯 KPI Pace & Command Center")
        
        raw_sales = db.cloud_fetch_transactions(user_email)
        computed_actuals = le.compute_actuals(raw_sales, kpi_defs, period_start)
        
        head_col1, head_col2 = st.columns([2, 1])
        with head_col1:
            st.markdown(f"### 🗓️ Shifts Remaining: **{shifts_left}**")
        with head_col2:
            if st.button("🏁 Finish Active Shift", use_container_width=True):
                new_shifts = max(0, shifts_left - 1)
                db.cloud_save_targets(user_email, user_targets, new_shifts)
                st.success("Shift ended. Required pace values recalculated dynamically.")
                st.rerun()
                
        st.markdown("---")
        
        active_defs = [d for d in kpi_defs if d["is_active"] == 1]
        card_cols = st.columns(len(active_defs) if len(active_defs) > 0 else 1)
        for idx, defn in enumerate(active_defs):
            with card_cols[idx]:
                act = computed_actuals.get(defn["display_name"], 0)
                targ = user_targets.get(defn["db_code"], 0.0)
                s.render_kpi_block(defn["display_name"], act, targ, shifts_left)
                
        st.markdown("---")
        
        st.markdown("### 🎲 Quick-Log Bingo Grid")
        
        tile_cols = st.columns(5)
        with tile_cols[0]:
            if st.button("🎮 Gaming", use_container_width=True): st.session_state.active_log_tile = "Gaming"
        with tile_cols[1]:
            if st.button("📡 HBB", use_container_width=True): st.session_state.active_log_tile = "HBB"
        with tile_cols[2]:
            if st.button("📺 TV", use_container_width=True): st.session_state.active_log_tile = "TV"
        with tile_cols[3]:
            if st.button("⬆️ Upgrades", use_container_width=True): st.session_state.active_log_tile = "Upgrades"
        with tile_cols[4]:
            if st.button("✨ New Connections", use_container_width=True): st.session_state.active_log_tile = "New Connections"
            
        if st.session_state.active_log_tile:
            active_tile = st.session_state.active_log_tile
            st.markdown(f"#### 📝 Logging Details: {active_tile}")
            
            with st.form("bingo_drilldown_form"):
                subtype = None
                
                if active_tile == "Gaming":
                    st.info("Gaming units log directly as Non-Core items.")
                elif active_tile in ["HBB", "TV"]:
                    subtype = st.radio(f"Is this {active_tile} New or Regrade?", ["New", "Regrade"], horizontal=True)
                elif active_tile in ["Upgrades", "New Connections"]:
                    subtype = st.radio("Select Device Type:", ["Handset", "Tablet", "Watch", "MBB", "SIM"], horizontal=True)
                    
                notes_text = st.text_input("Transaction / Deal Notes (Optional)", placeholder="Customer initials or specific plan...")
                log_date = st.date_input("Transaction Date", value=datetime.today().date())
                
                form_col1, form_col2 = st.columns([1, 1])
                with form_col1:
                    submit_txn = st.form_submit_button("✅ Post to Ledger")
                with form_col2:
                    cancel_btn = st.form_submit_button("❌ Cancel")
                
                if submit_txn:
                    final_category = active_tile if not subtype else f"{active_tile} - {subtype}"
                    hidden_time_str = datetime.now().strftime("%H:%M")
                    now_str = f"{log_date.strftime('%Y-%m-%d')} {hidden_time_str}"
                    
                    db.cloud_log_transaction(user_email, final_category, notes_text.strip(), now_str)
                    
                    st.session_state.active_log_tile = None
                    st.success(f"Successfully tracked: {final_category} on {log_date.strftime('%d %b %Y')}")
                    st.rerun()
                    
                if cancel_btn:
                    st.session_state.active_log_tile = None
                    st.rerun()
                    
        st.markdown("---")
        
        # --- NEW: Safegaurded Calendar Header ---
        cal_col1, cal_col2 = st.columns([3, 1])
        with cal_col1:
            st.markdown("### 🗄️ Deep-Dive Calendar & History")
        with cal_col2:
            if st.session_state.edit_mode:
                if st.button("🔒 Lock Settings", use_container_width=True):
                    st.session_state.edit_mode = False
                    st.rerun()
            else:
                if st.button("⚙️ Unlock Edit/Void Mode", use_container_width=True):
                    st.session_state.edit_mode = True
                    st.rerun()

        if st.session_state.edit_mode:
            st.warning("⚠️ **Void Mode Active:** You can now delete incorrect entries. Remember to lock settings when finished.")

        tree = le.build_chronological_tree(raw_sales)
        
        if not tree:
            st.info("No verified cloud sales logged under this user profile for the active lifecycle.")
        else:
            for m_key, m_data in tree.items():
                
                monthly_tally = {}
                for w_title, w_days in m_data["weeks"].items():
                    for d_title, txs in w_days.items():
                        for tx in txs:
                            parent_cat = tx['category'].split(" - ")[0].strip()
                            monthly_tally[parent_cat] = monthly_tally.get(parent_cat, 0) + 1
                
                m_tally_str = " • ".join([f"{count} {cat}" for cat, count in monthly_tally.items()])
                
                with st.expander(f"📁 {m_data['display']}  [ {m_tally_str} ]", expanded=True):
                    for w_title, w_days in m_data["weeks"].items():
                        
                        weekly_tally = {}
                        for d_title, txs in w_days.items():
                            for tx in txs:
                                parent_cat = tx['category'].split(" - ")[0].strip()
                                weekly_tally[parent_cat] = weekly_tally.get(parent_cat, 0) + 1
                                
                        w_tally_str = " • ".join([f"{count} {cat}" for cat, count in weekly_tally.items()])
                        
                        st.markdown(f"#### 📅 {w_title}  *( {w_tally_str} )*")
                        
                        for d_title, txs in w_days.items():
                            daily_tally = {}
                            for tx in txs:
                                daily_tally[tx['category']] = daily_tally.get(tx['category'], 0) + 1
                            
                            tally_string = " | ".join([f"**{count}** {cat}" for cat, count in daily_tally.items()])
                            st.markdown(f"**{d_title}** 📊 *({tally_string})*")
                            
                            for tx in txs:
                                t_col1, t_col2 = st.columns([5, 1])
                                with t_col1:
                                    st.markdown(f"**{tx['category']}** — *{tx['notes']}*")
                                with t_col2:
                                    # --- NEW: Only show the Void button if Edit Mode is Unlocked ---
                                    if st.session_state.edit_mode:
                                        if st.button("🗑️ Void", key=f"del_btn_{tx['id']}"):
                                            db.cloud_delete_transaction(tx["id"])
                                            st.warning("Ledger line record deleted.")
                                            st.rerun()

    elif choice == "⚙️ My Profile & Shifts":
        st.markdown("# ⚙️ Target Settings & Profile Configurations")
        st.markdown("Customize your personal run-rates and target configurations below.")
        
        with st.form("personal_targets_form"):
            new_shifts_count = st.number_input("Total Monthly Shifts Remaining", min_value=0, max_value=31, value=shifts_left, step=1)
            updated_targets = {}
            
            for defn in kpi_defs:
                cur_t = user_targets.get(defn["db_code"], 0.0)
                updated_targets[defn["db_code"]] = st.number_input(f"Target Volume for {defn['display_name']}", min_value=0, value=int(cur_t), step=1)
                
            save_profile_settings = st.form_submit_button("Update Profile Configurations")
            if save_profile_settings:
                db.cloud_save_targets(user_email, updated_targets, new_shifts_count)
                st.success("Personal profile configurations synchronized to Supabase server.")
                st.rerun()

        st.markdown("---")
        
        st.markdown("### 🔄 Start a New Month")
        st.info("Finishing the month will reset your Dashboard actuals to zero so you can start fresh. All of your past sales will still remain perfectly visible in the Deep-Dive Calendar.")
        if st.button("🚨 Finish Month & Reset Actuals"):
            new_period_start = time.time()
            db.cloud_save_period_start(user_email, new_period_start)
            st.success("New month started! Dashboard actuals have been cleared.")
            st.rerun()

    elif choice == "🛠️ Admin Control Center" and st.session_state.is_admin:
        st.markdown("# 🛠️ Master Administrative Control Deck")
        st.markdown("Global corporate rules configurations. Updates deployed here apply instantly across all field clients.")
        
        updated_defs = []
        for item in kpi_defs:
            st.markdown(f"### Metric: **{item['display_name']}**")
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                d_name = st.text_input(f"Rename Display Label", value=item["display_name"], key=f"nm_{item['id']}")
            with col_b:
                feeds_vol = st.checkbox("Absorbs into Master Volume Count", value=bool(item["feeds_master_volume"]), key=f"f_vol_{item['id']}")
            with col_c:
                active_stat = st.checkbox("Metric Active on Sales Floor", value=bool(item["is_active"]), key=f"act_{item['id']}")
            
            updated_defs.append({
                "id": item["id"],
                "display_name": d_name,
                "db_code": item["db_code"],
                "feeds_master_volume": int(feeds_vol),
                "is_active": int(active_stat)
            })
            st.markdown("---")
            
        if st.button("⚡ Push Corporate Configuration Update Globally", use_container_width=True):
            db.cloud_save_kpi_definitions(updated_defs)
            st.success("Global corporate KPI mappings updated successfully.")
            st.rerun()