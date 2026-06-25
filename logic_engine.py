from datetime import datetime, timedelta

def compute_actuals(sales_data: list, kpi_definitions: list) -> dict:
    """
    Processes raw transaction entries against active administration definitions.
    Applies the master volume absorption rule dynamically without duplicating data.
    """
    # Initialize all known categories to 0 actuals
    actuals = {defn["display_name"]: 0 for defn in kpi_definitions}
    
    # Identify which master definition handles overarching volume
    master_display_name = None
    for defn in kpi_definitions:
        if defn["feeds_master_volume"] == 0 and defn["db_code"] == "core_upgrade":
            master_display_name = defn["display_name"]
            break
            
    # Default fallback if renamed or missing
    if not master_display_name and kpi_definitions:
        master_display_name = kpi_definitions[0]["display_name"]

    # Calculate volumes based on administrative mapping logic
    for row in sales_data:
        category = row.get("category")
        if category in actuals:
            actuals[category] += 1
            
        # Find if this category feeds into the master volume bucket
        for defn in kpi_definitions:
            if defn["display_name"] == category and defn["feeds_master_volume"] == 1:
                if master_display_name:
                    actuals[master_display_name] += 1
                break
                
    return actuals

def build_chronological_tree(sales_data: list) -> dict:
    """
    Structures a flat sequence of sales records into a clean, nested dictionary structure.
    Hierarchy: Year-Month -> Week (Strict Monday to Sunday Boundary) -> Specific Day.
    """
    tree = {}
    
    for row in sales_data:
        ts_str = row.get("timestamp")
        try:
            dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M")
        except ValueError:
            continue # Protects dashboard views from structurally corrupt historical timestamps
            
        # Level 1: Month Grouping
        month_key = dt.strftime("%Y-%m")
        month_display = dt.strftime("%B %Y")
        
        # Level 2: Week Grouping (Calculate the starting Monday of that specific transaction week)
        start_of_week = dt - timedelta(days=dt.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        week_display = f"📅 Week: {start_of_week.strftime('%d %b')} to {end_of_week.strftime('%d %b')}"
        
        # Level 3: Day Grouping
        day_display = dt.strftime("%A, %d %B")
        
        # Initialize dictionary nodes if they do not yet exist
        if month_key not in tree:
            tree[month_key] = {"display": month_display, "weeks": {}}
            
        if week_display not in tree[month_key]["weeks"]:
            tree[month_key]["weeks"][week_display] = {}
            
        if day_display not in tree[month_key]["weeks"][week_display]:
            tree[month_key]["weeks"][week_display][day_display] = []
            
        tree[month_key]["weeks"][week_display][day_display].append(row)
        
    return tree