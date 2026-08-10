from datetime import datetime, timedelta

def compute_actuals(sales_data: list, kpi_definitions: list, period_start: float = 0.0) -> dict:
    """
    Processes raw transaction entries against active administration definitions.
    Filters out historical data that occurred before the current active tracking period.
    """
    actuals = {defn["display_name"]: 0 for defn in kpi_definitions}
    
    master_display_name = None
    for defn in kpi_definitions:
        if defn["feeds_master_volume"] == 0 and defn["db_code"] == "core_upgrade":
            master_display_name = defn["display_name"]
            break
            
    if not master_display_name and kpi_definitions:
        master_display_name = kpi_definitions[0]["display_name"]

    for row in sales_data:
        # --- NEW: Filter out sales from before the current active tracking month ---
        try:
            dt = datetime.strptime(row.get("timestamp"), "%Y-%m-%d %H:%M")
            if dt.timestamp() < period_start:
                continue
        except ValueError:
            pass

        raw_category = row.get("category", "")
        parent_category = raw_category.split(" - ")[0].strip()
        
        if parent_category in actuals:
            actuals[parent_category] += 1
            
        for defn in kpi_definitions:
            if defn["display_name"] == parent_category and defn["feeds_master_volume"] == 1:
                if master_display_name:
                    actuals[master_display_name] += 1
                break
                
    return actuals

def build_chronological_tree(sales_data: list) -> dict:
    """
    Structures a flat sequence of sales records into a nested timeline structure.
    """
    tree = {}
    
    for row in sales_data:
        ts_str = row.get("timestamp")
        try:
            dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M")
        except ValueError:
            continue
            
        month_key = dt.strftime("%Y-%m")
        month_display = dt.strftime("%B %Y")
        
        start_of_week = dt - timedelta(days=dt.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        week_display = f"{start_of_week.strftime('%d %b')} to {end_of_week.strftime('%d %b')}"
        
        day_display = dt.strftime("%A, %d %B")
        
        if month_key not in tree:
            tree[month_key] = {"display": month_display, "weeks": {}}
            
        if week_display not in tree[month_key]["weeks"]:
            tree[month_key]["weeks"][week_display] = {}
            
        if day_display not in tree[month_key]["weeks"][week_display]:
            tree[month_key]["weeks"][week_display][day_display] = []
            
        tree[month_key]["weeks"][week_display][day_display].append(row)
        
    for m_key, m_data in tree.items():
        for w_title, w_days in m_data["weeks"].items():
            for d_title, txs in w_days.items():
                txs.sort(key=lambda x: datetime.strptime(x['timestamp'], "%Y-%m-%d %H:%M"), reverse=True)
                
    return tree