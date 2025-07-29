import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from pathlib import Path
import json

def load_excel_data(uploaded_file):
    """Load Excel file and return all sheets as a dictionary"""
    if uploaded_file is not None:
        try:
            excel_data = pd.ExcelFile(uploaded_file)
            sheets = {}
            for sheet_name in excel_data.sheet_names:
                # Debug for specific sheets
                if "5" in sheet_name or "6" in sheet_name:
                    st.write(f"🔍 **Loading {sheet_name}...**")
                
                # First, read the sheet without setting header to see the structure
                df_raw = pd.read_excel(uploaded_file, sheet_name=sheet_name, header=None)
                
                if "5" in sheet_name or "6" in sheet_name:
                    st.write(f"Raw data for {sheet_name}:")
                    st.write("First 3 rows:")
                    for i in range(min(3, len(df_raw))):
                        row_data = [str(val) if pd.notna(val) else 'NaN' for val in df_raw.iloc[i]]
                        st.write(f"  Row {i}: {row_data}")
                
                # Check if we have multi-row headers by looking at the first few rows
                if len(df_raw) >= 2:
                    # Look at first two rows to see if they contain year information
                    row0 = df_raw.iloc[0].fillna('').astype(str)
                    row1 = df_raw.iloc[1].fillna('').astype(str)
                    
                    # Check if row 0 contains year information directly (like "Porcentaje 2024")
                    has_years_in_row0 = any('202' in str(val) or '201' in str(val) for val in row0)
                    
                    # Check if row 1 contains year-category combinations like "2022-Total"
                    has_year_categories_in_row1 = any(
                        '-' in str(val) and 
                        any(char.isdigit() for char in str(val)) and
                        len(str(val).split('-')) == 2 and
                        any(part.strip().isdigit() and len(part.strip()) == 4 and 1900 <= int(part.strip()) <= 2100 
                            for part in str(val).split('-') if part.strip().isdigit())
                        for val in row1 if pd.notna(val) and str(val).strip()
                    )
                    
                    if "5" in sheet_name or "6" in sheet_name:
                        st.write(f"has_years_in_row0: {has_years_in_row0}")
                        st.write(f"has_year_categories_in_row1: {has_year_categories_in_row1}")
                    
                    if has_years_in_row0 and not has_year_categories_in_row1:
                        # Standard header processing - row 0 has the headers with years
                        df = pd.read_excel(uploaded_file, sheet_name=sheet_name, header=0)
                        if "5" in sheet_name or "6" in sheet_name:
                            st.write(f"Using standard header processing for {sheet_name}")
                            st.write(f"Resulting columns: {list(df.columns)}")
                    elif has_year_categories_in_row1:
                        # Use row 1 as headers directly, but clean them up
                        headers = []
                        for i, val in enumerate(row1):
                            if pd.notna(val) and str(val).strip():
                                headers.append(str(val).strip())
                            else:
                                # For empty cells, try to use row 0 value or create unnamed column
                                row0_val = row0.iloc[i] if i < len(row0) and pd.notna(row0.iloc[i]) else ''
                                if row0_val:
                                    headers.append(str(row0_val).strip())
                                else:
                                    headers.append(f"Unnamed_{i}")
                        
                        # Read the data starting from row 2 with the headers from row 1
                        df = pd.read_excel(uploaded_file, sheet_name=sheet_name, header=None, skiprows=2)
                        if len(headers) <= len(df.columns):
                            df.columns = headers[:len(df.columns)]
                        else:
                            # If we have more headers than columns, truncate headers
                            df.columns = headers[:len(df.columns)]
                        
                        if "5" in sheet_name or "6" in sheet_name:
                            st.write(f"Using row 1 as headers for {sheet_name}")
                            st.write(f"Headers: {headers}")
                    else:
                        # Standard header processing
                        df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
                        if "5" in sheet_name or "6" in sheet_name:
                            st.write(f"Using fallback standard processing for {sheet_name}")
                            st.write(f"Resulting columns: {list(df.columns)}")
                else:
                    # Standard header processing for sheets with fewer rows
                    df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
                
                # Drop rows with all NaN values
                df = df.dropna(how='all')
                # Drop columns with all NaN values
                df = df.dropna(axis=1, how='all')
                # Clean empty strings and convert to proper types
                for col in df.columns:
                    df[col] = df[col].replace(['', ' ', '  ', '   '], np.nan)
                sheets[sheet_name] = df
            return sheets
        except Exception as e:
            st.error(f"Error loading Excel file: {e}")
            return None
    return None

def clean_value(value):
    """Clean and convert value to float, handling NaN and string values"""
    if pd.isna(value):
        return 0.0
    
    if isinstance(value, str):
        # Remove % and commas, then convert to float
        clean_value = value.replace('%', '').replace(',', '').strip()
        try:
            num_value = float(clean_value)
            # If it's a decimal percentage (0.188), convert to whole percentage (18.8)
            if num_value < 1 and num_value > 0:
                num_value = num_value * 100
            return num_value
        except:
            return 0.0
    
    try:
        num_value = float(value)
        # If it's a decimal percentage (0.188), convert to whole percentage (18.8)
        if num_value < 1 and num_value > 0:
            num_value = num_value * 100
        return num_value
    except:
        return 0.0

def clean_change_value(value):
    """Clean change values (percentage points) without converting decimals to percentages"""
    if pd.isna(value):
        return 0.0
    
    if isinstance(value, str):
        # Remove % and commas, then convert to float
        clean_val = value.replace('%', '').replace(',', '').strip()
        try:
            return float(clean_val) * 100  # Convert decimal to percentage points
        except:
            return 0.0
    
    try:
        return float(value) * 100  # Convert decimal to percentage points
    except:
        return 0.0

def process_graph1_data(df, selected_years):
    """Process data for Graph 1 (Line chart with poverty data)"""
    processed_data = []
    
    # Use the original data structure directly
    for index, row in df.iterrows():
        variable = str(row.iloc[0]) if len(row) > 0 else ""
        
        # Look for poverty-related variables in the first column
        if "Pobreza" in variable:
            poverty_data = {
                "Variable": variable
            }
            
            # Process each column to find year data
            for col in df.columns:
                col_str = str(col)
                
                # Check if this column contains year data
                for year in selected_years:
                    if f"{year}" in col_str:
                        value = clean_value(row[col])
                        if value > 0:  # Only add if we have valid data
                            poverty_data[str(year)] = value
                            
                            # Look for corresponding miles data
                            for miles_col in df.columns:
                                miles_col_str = str(miles_col)
                                if f"{year}" in miles_col_str and ("miles" in miles_col_str.lower() or "personas" in miles_col_str.lower()):
                                    miles_value = clean_value(row[miles_col])
                                    if miles_value > 0:
                                        poverty_data[f"{year} (miles de personas)"] = miles_value
                                    break
            
            # Only add if we have data for at least one year
            if any(str(year) in poverty_data for year in selected_years):
                processed_data.append(poverty_data)
    
    return processed_data

def process_graph2_data(df, selected_years):
    """Process data for Graph 2 (Horizontal bar chart with deficiencies)"""
    processed_data = []
    
    # Use the original data structure directly
    for index, row in df.iterrows():
        variable = str(row.iloc[0]) if len(row) > 0 else ""
        
        # Look for deficiency-related variables in the first column
        if ("Carencia" in variable or "carencia" in variable or 
            "Rezago educativo" in variable or "Rezago" in variable):
            deficiency_data = {
                "Carencia": variable
            }
            
            # Process each column to find year data
            for col in df.columns:
                col_str = str(col)
                
                # Check if this column contains year data
                for year in selected_years:
                    if f"{year}" in col_str:
                        value = clean_value(row[col])
                        if value > 0:  # Only add if we have valid data
                            deficiency_data[str(year)] = value
                            
                            # Look for corresponding miles data
                            for miles_col in df.columns:
                                miles_col_str = str(miles_col)
                                if f"{year}" in miles_col_str and ("miles" in miles_col_str.lower() or "personas" in miles_col_str.lower()):
                                    miles_value = clean_value(row[miles_col])
                                    if miles_value > 0:
                                        deficiency_data[f"{year} (miles de personas)"] = miles_value
                                    break
            
            # Only add if we have data for at least one year
            if any(str(year) in deficiency_data for year in selected_years):
                processed_data.append(deficiency_data)
    
    return processed_data

def process_graph3_data(df, selected_years):
    """Process data for Graph 3 (Bar chart comparing years)"""
    processed_data = []
    
    # Use the original data structure directly
    for index, row in df.iterrows():
        variable = str(row.iloc[0]) if len(row) > 0 else ""
        
        # Look for category variables (exclude empty and generic terms)
        if variable and variable not in ["Variable", "Categoría", ""] and not pd.isna(variable):
            category_data = {
                "Categoría": variable
            }
            
            # Process each column to find year data
            for col in df.columns:
                col_str = str(col)
                
                # Check if this column contains year data
                for year in selected_years:
                    if f"{year}" in col_str:
                        value = clean_value(row[col])
                        if value > 0:  # Only add if we have valid data
                            category_data[str(year)] = value
                            
                            # Look for corresponding miles data
                            for miles_col in df.columns:
                                miles_col_str = str(miles_col)
                                if f"{year}" in miles_col_str and ("miles" in miles_col_str.lower() or "personas" in miles_col_str.lower()):
                                    miles_value = clean_value(row[miles_col])
                                    if miles_value > 0:
                                        category_data[f"{year} (miles de personas)"] = miles_value
                                    break
            
            # Only add if we have data for at least one year
            if any(str(year) in category_data for year in selected_years):
                processed_data.append(category_data)
    
    return processed_data

def render_graph1(df, selected_years):
    """Render Graph 1: Line chart with poverty data and absolute values as labels"""
    if df is None or df.empty:
        st.warning("No data available for Graph 1")
        return
    
    df = df.reset_index(drop=True)  # Ensure positional indices match iloc
    # Get all rows from the original data (don't filter by keywords)
    poverty_rows = []
    for index, row in df.iterrows():
        variable = str(row.iloc[0]) if len(row) > 0 else ""
        # Include all rows that have data in the first column
        if variable and variable not in ["Variable", "Categoría", ""] and not pd.isna(variable):
            poverty_rows.append((index, variable))
    
    if not poverty_rows:
        st.warning("No data found in the original data")
        return
    
    # Prepare data for plotting from original DataFrame
    plot_data = []
    for row_idx, variable in poverty_rows:
        # Only process row 0 and 1
        if row_idx not in [0, 1]:
            continue
        row = df.iloc[row_idx]
        for year in selected_years:
            for col in df.columns:
                col_str = str(col)
                if f"{year}" in col_str:
                    value = clean_value(row[col])
                    if value > 0:
                        # Get miles from row 2 for Pobreza, row 3 for Pobreza extrema
                        miles_row_idx = row_idx + 2
                        miles_value = 0
                        if miles_row_idx < len(df):
                            try:
                                miles_value = clean_value(df.iloc[miles_row_idx][col])
                            except (KeyError, IndexError):
                                miles_value = 0
                        plot_point = {
                            'Year': year,
                            'Variable': variable,
                            'Value': value,  # value is already in correct format
                            'Miles': miles_value
                        }
                        plot_data.append(plot_point)
                    break
    
    if not plot_data:
        st.warning("No valid data found for plotting")
        return
    
    df_plot = pd.DataFrame(plot_data)
    
    # Create line chart with custom labels
    fig = go.Figure()
    
    colors = {'Pobreza': '#FFD700', 'Pobreza extrema': '#FF4444'}
    
    for variable in df_plot['Variable'].unique():
        var_data = df_plot[df_plot['Variable'] == variable]
        color = colors.get(variable, '#8884d8')
        
        # Create custom text labels with percentage and miles
        text_labels = []
        for _, row in var_data.iterrows():
            percentage = f"{row['Value']:.1f}%"
            miles = f"[{row['Miles']:.0f}]" if row['Miles'] > 0 else ""
            text_labels.append(f"{percentage}<br>{miles}")
        
        fig.add_trace(go.Scatter(
             x=var_data['Year'],
             y=var_data['Value'],
             mode='lines+markers+text',
             name=variable,
             text=text_labels,
             textposition="top center",
             line=dict(color=color, width=3),
             marker=dict(size=8, color=color),
             hovertemplate=f"{variable}: %{{y:.1f}}%<br>Year: %{{x}}<br>Miles: %{{customdata}}<extra></extra>",
             customdata=var_data['Miles'].tolist()
         ))
    
    fig.update_layout(
        title="Evolución de la Pobreza",
        xaxis_title="Año",
        yaxis_title="Porcentaje (%)",
        height=700,  # Increased from 500
        showlegend=True,
        legend=dict(
            yanchor="bottom",
            y=0.01,
            xanchor="right",
            x=0.99
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_graph2(df, selected_years):
    """Render Graph 2: Horizontal bar chart with deficiencies"""
    if df is None or df.empty:
        st.warning("No data available for Graph 2")
        return
    
    # Get all rows from the original data (don't filter by keywords)
    deficiency_rows = []
    for index, row in df.iterrows():
        variable = str(row.iloc[0]) if len(row) > 0 else ""
        # Include all rows that have data in the first column
        if variable and variable not in ["Variable", "Categoría", ""] and not pd.isna(variable):
            deficiency_rows.append((index, variable))
    
    if not deficiency_rows:
        st.warning("No data found in the original data")
        return
    
    # Prepare data for plotting from original DataFrame
    plot_data = []
    for row_idx, carencia in deficiency_rows:
        row = df.iloc[row_idx]
        
        for year in selected_years:
            # Look for columns containing the year
            for col in df.columns:
                col_str = str(col)
                if f"{year}" in col_str:
                    value = clean_value(row[col])
                    if value > 0:
                        # Look for corresponding miles data in row 2 (index 1)
                        miles_value = 0
                        if len(df) > 1:  # If there's more than one row
                            # Find the column index for the current column
                            col_index = None
                            for i, col_name in enumerate(df.columns):
                                if col_name == col:
                                    col_index = i
                                    break
                            
                            if col_index is not None and len(df) > 1:
                                # Get miles value from the same column in row 2 (index 1)
                                miles_value = clean_value(df.iloc[1][col_index])
                        
                        # If no miles found in row 2, try to find it in the same row
                        if miles_value == 0:
                            for miles_col in df.columns:
                                miles_col_str = str(miles_col)
                                if f"{year}" in miles_col_str and ("miles" in miles_col_str.lower() or "personas" in miles_col_str.lower()):
                                    miles_value = clean_value(row[miles_col])
                                    break
                        
                        plot_data.append({
                            'Carencia': carencia,
                            'Year': year,
                            'Value': value,
                            'Miles': miles_value
                        })
                    break
    
    if not plot_data:
        st.warning("No valid data found for plotting")
        return
    
    df_plot = pd.DataFrame(plot_data)
    
    # Create horizontal bar chart with custom styling
    fig = go.Figure()
    
    # Colors for different years
    colors = {'2022': '#1f77b4', '2024': '#ff7f0e'}
    
    # Sort categories by 2024 values for better visualization
    if len(selected_years) >= 2:
        year1, year2 = selected_years[0], selected_years[1]
        categories_2024 = df_plot[df_plot['Year'] == year2].sort_values('Value', ascending=True)['Carencia'].unique()
    else:
        categories_2024 = df_plot['Carencia'].unique()
    
    for year in selected_years:
        year_data = df_plot[df_plot['Year'] == year]
        
        # Create custom text labels with percentage and miles
        text_labels = []
        for _, row in year_data.iterrows():
            percentage = f"{row['Value']:.1f}%"
            miles = f"[{row['Miles']:.0f}]" if row['Miles'] > 0 else ""
            text_labels.append(f"{percentage} {miles}")
        
        fig.add_trace(go.Bar(
            x=year_data['Value'],
            y=year_data['Carencia'],
            name=f'{year}',
            orientation='h',
            marker_color=colors.get(str(year), '#8884d8'),
            text=text_labels,
            textposition='auto',
            hovertemplate=f"{year}: %{{x:.1f}}%<br>Miles: %{{customdata}}<extra></extra>",
            customdata=year_data['Miles'].tolist()
        ))
    
    # Add change indicators if we have two years
    if len(selected_years) >= 2:
        year1, year2 = selected_years[0], selected_years[1]
        year1_data = df_plot[df_plot['Year'] == year1].set_index('Carencia')['Value']
        year2_data = df_plot[df_plot['Year'] == year2].set_index('Carencia')['Value']
        
        # Calculate changes
        changes = []
        for carencia in categories_2024:
            if carencia in year1_data.index and carencia in year2_data.index:
                change = year2_data[carencia] - year1_data[carencia]
                # Convert to scalar if it's a Series
                if hasattr(change, 'item'):
                    try:
                        change = change.item()
                    except ValueError:
                        # If it's a Series with multiple values, take the first one
                        change = change.iloc[0] if len(change) > 0 else 0
                elif hasattr(change, 'iloc'):
                    change = change.iloc[0] if len(change) > 0 else 0
                elif isinstance(change, (list, tuple)):
                    change = change[0] if len(change) > 0 else 0
                
                changes.append({
                    'Carencia': carencia,
                    'Change': change,
                    'Arrow': '▼' if change < 0 else '▲' if change > 0 else '→'
                })
        
        # Add change annotations with prettier styling
        for change_info in changes:
            carencia = change_info['Carencia']
            change = change_info['Change']
            
            # Use prettier arrows and colors
            if change < 0:
                arrow = "↘️"  # Down arrow with emoji
                color = "#27ae60"  # Green
                change_text = f"↘️ {abs(change):.1f} pp"  # Changed from "p.p." to "pp"
            elif change > 0:
                arrow = "↗️"  # Up arrow with emoji
                color = "#e74c3c"  # Red
                change_text = f"↗️ +{change:.1f} pp"  # Changed from "p.p." to "pp"
            else:
                arrow = "→"  # Neutral arrow
                color = "#95a5a6"  # Gray
                change_text = f"→ {change:.1f} pp"  # Changed from "p.p." to "pp"
            
            # Find the position for the annotation (outside the graph)
            year2_value = year2_data.get(carencia, 0)
            max_value = max(df_plot['Value'])
            
            fig.add_annotation(
                x=max_value * 1.15,  # Position outside the graph area
                y=carencia,
                text=change_text,
                showarrow=False,
                font=dict(
                    color=color,
                    size=12,
                    family="Arial, sans-serif"
                ),
                xanchor='left',
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor=color,
                borderwidth=1
            )
    
    fig.update_layout(
        title="Carencias Nuevo León",
        xaxis_title="Porcentaje (%)",
        yaxis_title="",
        height=700,  # Increased from 500
        barmode='group',
        showlegend=True,
        legend=dict(
            yanchor="bottom",
            y=0.01,
            xanchor="right",
            x=0.99
        ),
        xaxis=dict(range=[0, max(df_plot['Value']) * 1.3])
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_graph3(df, selected_years):
    """Render Graph 3: Bar chart comparing years with percentage labels and miles values"""
    if df is None or df.empty:
        st.warning("No data available for Graph 3")
        return
    
    df = df.reset_index(drop=True)  # Ensure positional indices match iloc
    
    # Get all columns except the first one (which is the row identifier)
    data_columns = df.columns[1:]
    
    # Extract demographic groups and years from column names
    demographic_groups = []
    years_found = []
    
    for col in data_columns:
        col_str = str(col)
        
        # Try different patterns for column names
        if '-' in col_str:
            parts = col_str.split('-')
            if len(parts) >= 2:
                year = parts[0].strip()
                group = parts[1].strip()
                
                # Check if the first part is a year
                try:
                    year_int = int(year)
                    if 1900 <= year_int <= 2100:
                        if year_int not in years_found:
                            years_found.append(year_int)
                        
                        if group not in demographic_groups:
                            demographic_groups.append(group)
                except:
                    # If first part is not a year, try the reverse
                    try:
                        year_int = int(parts[1].strip())
                        if 1900 <= year_int <= 2100:
                            if year_int not in years_found:
                                years_found.append(year_int)
                            
                            group = parts[0].strip()
                            if group not in demographic_groups:
                                demographic_groups.append(group)
                    except:
                        pass
        else:
            # Try to extract year from column name using regex
            import re
            year_match = re.search(r'\b(19|20)\d{2}\b', col_str)
            if year_match:
                year_int = int(year_match.group())
                if year_int not in years_found:
                    years_found.append(year_int)
                
                # Extract group name (everything before the year)
                group = col_str.replace(str(year_int), '').strip()
                if group and group not in demographic_groups:
                    demographic_groups.append(group)
    
    # Filter to only include selected years
    years_to_plot = [year for year in years_found if year in selected_years]
    
    if not years_to_plot or not demographic_groups:
        st.warning("No valid data found for plotting")
        return
    
    # Prepare data for plotting - only use rows 0 and 1 for percentages
    plot_data = []
    for group in demographic_groups:
        for year in years_to_plot:
            # Find the column that matches this group and year
            target_col = None
            for col in data_columns:
                col_str = str(col)
                # Try multiple patterns - the format is "2022-Total", "2024-Total", etc.
                if (f"{year}-{group}" in col_str or 
                    f"{year} - {group}" in col_str or
                    f"{year}{group}" in col_str):
                    target_col = col
                    break
            
            if target_col is not None:
                # Get percentage from row 0 (first data row)
                value = clean_value(df.iloc[0][target_col])
                if value > 0:
                    # Get miles from row 2 (third row)
                    miles_value = 0
                    if len(df) > 2:
                        try:
                            miles_value = clean_value(df.iloc[2][target_col])
                        except (KeyError, IndexError):
                            miles_value = 0
                    
                    plot_point = {
                        'Categoría': group,
                        'Year': year,
                        'Value': value,
                        'Miles': miles_value
                    }
                    plot_data.append(plot_point)
    
    if not plot_data:
        st.warning("No valid data found for plotting")
        return
    
    df_plot = pd.DataFrame(plot_data)
    
    # Create bar chart with custom styling
    fig = go.Figure()
    
    # Colors for different years
    colors = {'2022': '#1f77b4', '2024': '#ff7f0e'}
    
    # Sort categories for better visualization
    categories = df_plot['Categoría'].unique()
    
    for year in selected_years:
        year_data = df_plot[df_plot['Year'] == year]
        
        # Create custom text labels with percentage and miles
        text_labels = []
        for _, row in year_data.iterrows():
            percentage = f"{row['Value']:.1f}%"
            miles = f"[{row['Miles']:.0f}]" if row['Miles'] > 0 else ""
            text_labels.append(f"{percentage} {miles}")
        
        # Use category names for X-axis, but position bars side by side
        fig.add_trace(go.Bar(
            x=year_data['Categoría'],
            y=year_data['Value'],
            name=f'{year}',
            marker_color=colors.get(str(year), '#8884d8'),
            text=text_labels,
            textposition='outside',
            hovertemplate=f"{year}: %{{y:.1f}}%<br>Miles: %{{customdata}}<extra></extra>",
            customdata=year_data['Miles'].tolist()
        ))
    
    # Add change indicators if we have two years
    if len(selected_years) >= 2:
        year1, year2 = selected_years[0], selected_years[1]
        year1_data = df_plot[df_plot['Year'] == year1].set_index('Categoría')['Value']
        year2_data = df_plot[df_plot['Year'] == year2].set_index('Categoría')['Value']
        
        # Calculate changes
        changes = []
        for categoria in categories:
            if categoria in year1_data.index and categoria in year2_data.index:
                change = year2_data[categoria] - year1_data[categoria]
                # Convert to scalar if it's a Series
                if hasattr(change, 'item'):
                    try:
                        change = change.item()
                    except ValueError:
                        # If it's a Series with multiple values, take the first one
                        change = change.iloc[0] if len(change) > 0 else 0
                elif hasattr(change, 'iloc'):
                    change = change.iloc[0] if len(change) > 0 else 0
                elif isinstance(change, (list, tuple)):
                    change = change[0] if len(change) > 0 else 0
                
                changes.append({
                    'Categoría': categoria,
                    'Change': change,
                    'Arrow': '▼' if change < 0 else '▲' if change > 0 else '→'
                })
        
        # Add change annotations with prettier styling
        for change_info in changes:
            categoria = change_info['Categoría']
            change = change_info['Change']
            
            # Use prettier arrows and colors
            if change < 0:
                arrow = "▼"  # Down arrow
                color = "#27ae60"  # Green
                change_text = f"▼ {abs(change):.1f} pp"
            elif change > 0:
                arrow = "▲"  # Up arrow
                color = "#e74c3c"  # Red
                change_text = f"▲ +{change:.1f} pp"
            else:
                arrow = "→"  # Neutral arrow
                color = "#95a5a6"  # Gray
                change_text = f"→ {change:.1f} pp"
            
            # Find the position for the annotation (above the chart)
            year2_value = year2_data.get(categoria, 0)
            max_value = max(df_plot['Value'])
            
            # Find the position for the annotation (above the chart)
            fig.add_annotation(
                x=categoria,
                y=max_value * 1.05,  # Position above the chart area
                text=change_text,
                showarrow=False,
                font=dict(
                    color=color,
                    size=12,
                    family="Arial, sans-serif"
                ),
                yanchor='bottom',
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor=color,
                borderwidth=1
            )
    
    fig.update_layout(
        title="Población en pobreza",
        xaxis_title="",
        yaxis_title="Porcentaje (%)",
        height=700,  # Increased from 500
        barmode='group',
        showlegend=True,
        legend=dict(
            yanchor="bottom",
            y=0.01,
            xanchor="right",
            x=0.99
        ),
        yaxis=dict(range=[0, max(df_plot['Value']) * 1.15])
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_graph4(df, selected_years):
    """Render Graph 4: Combined summary table and vertical bar chart"""
    if df is None or df.empty:
        st.warning("No data available for Graph 4")
        return
    
    df = df.reset_index(drop=True)  # Ensure positional indices match iloc
    
    # Get all columns except the first one (which is the row identifier)
    data_columns = df.columns[1:]
    
    # Extract categories and years from column names
    categories = []
    years_found = []
    
    for col in data_columns:
        col_str = str(col)
        
        # Try different patterns for column names
        if '-' in col_str:
            parts = col_str.split('-')
            if len(parts) >= 2:
                year = parts[0].strip()
                category = parts[1].strip()
                
                # Check if the first part is a year
                try:
                    year_int = int(year)
                    if 1900 <= year_int <= 2100:
                        if year_int not in years_found:
                            years_found.append(year_int)
                        
                        if category not in categories:
                            categories.append(category)
                except:
                    # If first part is not a year, try the reverse
                    try:
                        year_int = int(parts[1].strip())
                        if 1900 <= year_int <= 2100:
                            if year_int not in years_found:
                                years_found.append(year_int)
                            
                            category = parts[0].strip()
                            if category not in categories:
                                categories.append(category)
                    except:
                        pass
        else:
            # Try to extract year from column name using regex
            import re
            year_match = re.search(r'\b(19|20)\d{2}\b', col_str)
            if year_match:
                year_int = int(year_match.group())
                if year_int not in years_found:
                    years_found.append(year_int)
                
                # Extract category name (everything before the year)
                category = col_str.replace(str(year_int), '').strip()
                if category and category not in categories:
                    categories.append(category)
    
    # Filter to only include selected years
    years_to_plot = [year for year in years_found if year in selected_years]
    
    if not years_to_plot or not categories:
        st.warning("No valid data found for plotting")
        return
    
    # Prepare data for plotting - only use rows 0 and 2
    plot_data = []
    summary_data = []
    
    for category in categories:
        for year in years_to_plot:
            # Find the column that matches this category and year
            target_col = None
            for col in data_columns:
                col_str = str(col)
                if (f"{year}-{category}" in col_str or 
                    f"{year} - {category}" in col_str or
                    f"{year}{category}" in col_str):
                    target_col = col
                    break
            
            if target_col is not None:
                # Get percentage from row 0 (first data row)
                value = clean_value(df.iloc[0][target_col])
                if value > 0:
                    # Get miles from row 2 (third row)
                    miles_value = 0
                    if len(df) > 2:
                        try:
                            miles_value = clean_value(df.iloc[2][target_col])
                        except (KeyError, IndexError):
                            miles_value = 0
                    
                    plot_point = {
                        'Categoría': category,
                        'Year': year,
                        'Value': value,
                        'Miles': miles_value
                    }
                    plot_data.append(plot_point)
                    
                    # Add to summary data
                    summary_data.append({
                        'Categoría': category,
                        'Year': year,
                        'Porcentaje': value,
                        'Miles': miles_value
                    })
    
    if not plot_data:
        st.warning("No valid data found for plotting")
        return
    
    df_plot = pd.DataFrame(plot_data)
    df_summary = pd.DataFrame(summary_data)
    
    # Create summary table
    st.subheader("📊 Resumen de Datos")
    
    # Create a summary table with percentages and miles
    summary_table_data = []
    for category in categories:
        category_data = df_summary[df_summary['Categoría'] == category]
        if len(category_data) >= 2:
            year1_data = category_data[category_data['Year'] == years_to_plot[0]].iloc[0]
            year2_data = category_data[category_data['Year'] == years_to_plot[1]].iloc[0]
            
            change = year2_data['Porcentaje'] - year1_data['Porcentaje']
            
            summary_table_data.append({
                'Categoría': category,
                f'{years_to_plot[0]} (%)': f"{year1_data['Porcentaje']:.1f}",
                f'{years_to_plot[1]} (%)': f"{year2_data['Porcentaje']:.1f}",
                'Cambio (p.p.)': f"{change:+.1f}",
                f'{years_to_plot[0]} (miles)': f"{year1_data['Miles']:.0f}",
                f'{years_to_plot[1]} (miles)': f"{year2_data['Miles']:.0f}"
            })
    
    if summary_table_data:
        summary_df = pd.DataFrame(summary_table_data)
        st.dataframe(summary_df, use_container_width=True)
    
    # Create vertical bar chart
    st.subheader("📈 Gráfica de Comparación")
    
    fig = go.Figure()
    
    # Colors for different years
    colors = {'2022': '#1f77b4', '2024': '#ff7f0e'}
    
    for year in selected_years:
        year_data = df_plot[df_plot['Year'] == year]
        
        # Create custom text labels with percentage and miles
        text_labels = []
        for _, row in year_data.iterrows():
            percentage = f"{row['Value']:.1f}%"
            miles = f"[{row['Miles']:.0f}]" if row['Miles'] > 0 else ""
            text_labels.append(f"{percentage} {miles}")
        
        fig.add_trace(go.Bar(
            x=year_data['Categoría'],
            y=year_data['Value'],
            name=f'{year}',
            marker_color=colors.get(str(year), '#8884d8'),
            text=text_labels,
            textposition='outside',
            hovertemplate=f"{year}: %{{y:.1f}}%<br>Miles: %{{customdata}}<extra></extra>",
            customdata=year_data['Miles'].tolist()
        ))
    
    # Add change indicators if we have two years
    if len(selected_years) >= 2:
        year1, year2 = selected_years[0], selected_years[1]
        year1_data = df_plot[df_plot['Year'] == year1].set_index('Categoría')['Value']
        year2_data = df_plot[df_plot['Year'] == year2].set_index('Categoría')['Value']
        
        # Calculate changes
        changes = []
        for categoria in categories:
            if categoria in year1_data.index and categoria in year2_data.index:
                change = year2_data[categoria] - year1_data[categoria]
                # Convert to scalar if it's a Series
                if hasattr(change, 'item'):
                    try:
                        change = change.item()
                    except ValueError:
                        change = change.iloc[0] if len(change) > 0 else 0
                elif hasattr(change, 'iloc'):
                    change = change.iloc[0] if len(change) > 0 else 0
                elif isinstance(change, (list, tuple)):
                    change = change[0] if len(change) > 0 else 0
                
                changes.append({
                    'Categoría': categoria,
                    'Change': change
                })
        
        # Add change annotations with prettier styling
        for change_info in changes:
            categoria = change_info['Categoría']
            change = change_info['Change']
            
            # Use prettier arrows and colors
            if change < 0:
                arrow = "▼"  # Down arrow
                color = "#27ae60"  # Green
                change_text = f"▼ {abs(change):.1f} pp"
            elif change > 0:
                arrow = "▲"  # Up arrow
                color = "#e74c3c"  # Red
                change_text = f"▲ +{change:.1f} pp"
            else:
                arrow = "→"  # Neutral arrow
                color = "#95a5a6"  # Gray
                change_text = f"→ {change:.1f} pp"
            
            # Find the position for the annotation (above the chart)
            year2_value = year2_data.get(categoria, 0)
            max_value = max(df_plot['Value'])
            
            fig.add_annotation(
                x=categoria,
                y=max_value * 1.05,  # Position above the chart area
                text=change_text,
                showarrow=False,
                font=dict(
                    color=color,
                    size=12,
                    family="Arial, sans-serif"
                ),
                yanchor='bottom',
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor=color,
                borderwidth=1
            )
    
    fig.update_layout(
        title="Población en pobreza por categoría",
        xaxis_title="",
        yaxis_title="Porcentaje (%)",
        height=700,  # Increased from 500
        barmode='group',
        showlegend=True,
        legend=dict(
            yanchor="bottom",
            y=0.01,
            xanchor="right",
            x=0.99
        ),
        yaxis=dict(range=[0, max(df_plot['Value']) * 1.15])
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_graph5_and_6(sheets, selected_years):
    """Render Graph 5 and 6: Combined horizontal bar charts for carencias"""
    
    # Check if both sheets exist
    graph5_df = sheets.get('Gráfica 5')
    graph6_df = sheets.get('Gráfica 6')
    
    if graph5_df is None and graph6_df is None:
        st.warning("No se encontraron las hojas 'Gráfica 5' y 'Gráfica 6'")
        return
    
    st.title("📊 Carencias - Gráfica 5 y 6")
    
    # Create two columns for side-by-side display
    col1, col2 = st.columns(2)
    
    if graph5_df is not None:
        with col1:
            st.subheader("🇲🇽 Gráfica 5 - Carencias México")
            render_carencias_chart(graph5_df, selected_years, "México")
    
    if graph6_df is not None:
        with col2:
            st.subheader("🏛️ Gráfica 6 - Carencias Nuevo León")
            render_carencias_chart(graph6_df, selected_years, "Nuevo León")

def render_carencias_chart(df, selected_years, location_name):
    """Render a single carencias chart"""
    if df is None or df.empty:
        st.warning(f"No hay datos disponibles para {location_name}")
        return
    
    # Find year columns in the format "Porcentaje YYYY"
    year_columns = {}
    change_column = None    
    
    for col in df.columns:
        col_str = str(col)
        if 'porcentaje' in col_str.lower() or 'percentage' in col_str.lower():
            # Extract year from column name
            import re
            year_match = re.search(r'\b(19|20)\d{2}\b', col_str)
            if year_match:
                year = int(year_match.group())
                if year in selected_years:
                    year_columns[year] = col
        elif 'cambio' in col_str.lower() or 'change' in col_str.lower():
            change_column = col
    
    if not year_columns:
        st.warning(f"No se encontraron datos para los años seleccionados en {location_name}")
        return
    
    # Prepare data for plotting
    plot_data = []
    carencia_col = df.columns[0]  # First column should be the carencia names
    
    for _, row in df.iterrows():
        carencia = str(row[carencia_col])
        if carencia and carencia != 'nan' and not pd.isna(carencia):
            for year, col in year_columns.items():
                value = clean_value(row[col])
                if value > 0:
                    plot_data.append({
                        'Carencia': carencia,
                        'Year': year,
                        'Value': value,
                        'Change': clean_change_value(row[change_column]) if change_column else 0
                    })
    
    if not plot_data:
        st.warning(f"No se encontraron datos válidos para {location_name}")
        return
    
    df_plot = pd.DataFrame(plot_data)
    
    # Create horizontal bar chart
    fig = go.Figure()
    
    # Colors for different years
    colors = {'2022': '#1f77b4', '2024': '#ff7f0e'}
    
    # Sort by values for better visualization
    if len(selected_years) >= 2:
        year_for_sorting = max(selected_years)
        sort_data = df_plot[df_plot['Year'] == year_for_sorting].sort_values('Value', ascending=True)
        carencia_order = sort_data['Carencia'].tolist()
    else:
        carencia_order = df_plot['Carencia'].unique()
    
    for year in sorted(year_columns.keys()):
        year_data = df_plot[df_plot['Year'] == year]
        
        # Create custom text labels with percentage
        text_labels = []
        for _, row in year_data.iterrows():
            percentage = f"{row['Value']:.1f}%"
            text_labels.append(percentage)
        
        fig.add_trace(go.Bar(
            x=year_data['Value'],
            y=year_data['Carencia'],
            name=f'{year}',
            orientation='h',
            marker_color=colors.get(str(year), '#8884d8'),
            text=text_labels,
            textposition='auto',
            hovertemplate=f"{year}: %{{x:.1f}}%<extra></extra>"
        ))
    
    # Add change indicators if we have change data and two years
    if change_column and len(selected_years) >= 2:
        changes_added = set()
        for _, row in df_plot.iterrows():
            carencia = row['Carencia']
            if carencia not in changes_added:
                change = row['Change']
                
                if abs(change) > 0.001:  # Only show significant changes
                    # Use prettier arrows and colors
                    if change < 0:
                        color = "#27ae60"  # Green for decrease (good)
                        change_text = f"↘️ {abs(change):.1f} pp"
                    elif change > 0:
                        color = "#e74c3c"  # Red for increase (bad)
                        change_text = f"↗️ +{change:.1f} pp"
                    else:
                        color = "#95a5a6"  # Gray for no change
                        change_text = f"→ {change:.1f} pp"
                    
                    # Find the maximum value for positioning
                    max_value = max(df_plot['Value'])
                    
                    fig.add_annotation(
                        x=max_value * 1.15,
                        y=carencia,
                        text=change_text,
                        showarrow=False,
                        font=dict(
                            color=color,
                            size=10,
                            family="Arial, sans-serif"
                        ),
                        xanchor='left',
                        bgcolor="rgba(255, 255, 255, 0.8)",
                        bordercolor=color,
                        borderwidth=1
                    )
                    changes_added.add(carencia)
    
    fig.update_layout(
        title=f"Carencias {location_name}",
        xaxis_title="Porcentaje (%)",
        yaxis_title="",
        height=600,  # Increased from 400
        barmode='group',
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99
        ),
        yaxis=dict(categoryorder='array', categoryarray=carencia_order),
        xaxis=dict(range=[0, max(df_plot['Value']) * 1.3] if change_column else [0, max(df_plot['Value']) * 1.1])
    )
    
    st.plotly_chart(fig, use_container_width=True)

def determine_graph_type(sheet_name, df):
    """Determine the appropriate graph type based on sheet name and content"""
    sheet_lower = sheet_name.lower()
    
    # Check for poverty-related keywords in first column
    first_col_values = df.iloc[:, 0].astype(str).str.lower()
    
    if "pobreza" in sheet_lower or any("pobreza" in val for val in first_col_values):
        return "Gráfica 1 - Línea de Pobreza"
    elif "carencia" in sheet_lower or any("carencia" in val or "rezago" in val for val in first_col_values):
        return "Gráfica 2 - Carencias"
    else:
        return "Gráfica 3 - Comparación"

def main():
    st.set_page_config(
        page_title="Visualizador de Datos de Pobreza",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Visualizador de Datos de Pobreza")
    st.markdown("---")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Sube tu archivo Excel",
        type=['xlsx', 'xls'],
        help="Selecciona un archivo Excel con tus datos"
    )
    
    if uploaded_file is not None:
        # Load data
        sheets = load_excel_data(uploaded_file)
        
        if sheets:
            st.success(f"✅ Archivo cargado exitosamente. Hojas encontradas: {list(sheets.keys())}")
            
            # Sidebar for configuration
            st.sidebar.header("⚙️ Configuración")
            
            # Sheet selection
            selected_sheet = st.sidebar.selectbox(
                "Selecciona una hoja:",
                list(sheets.keys()),
                index=0
            )
            
            # Year selection
            df = sheets[selected_sheet]
            available_years = []
            
            # Temporary debug for troubleshooting
            st.write(f"🔍 **Debug - Sheet: {selected_sheet}**")
            st.write("**Column names:**")
            for i, col in enumerate(df.columns):
                st.write(f"  {i}: `{col}` (type: {type(col).__name__})")
            
            for col in df.columns:
                col_str = str(col)
                
                # Check for direct year columns (like 2022, 2024)
                is_direct_year = (col_str.isdigit() and len(col_str) == 4) or (isinstance(col, int) and 1900 <= col <= 2100)
                
                # Check for years embedded in column names (like "Porcentaje 2024" or "Total-2024")
                embedded_year = None
                if isinstance(col, str):
                    import re
                    # Look for year patterns in column names
                    year_match = re.search(r'\b(19|20)\d{2}\b', col_str)
                    if year_match:
                        embedded_year = int(year_match.group())
                        st.write(f"  ✅ Found embedded year in `{col}`: **{embedded_year}**")
                    
                    # Also check for patterns like "Total-2024", "Primera Infancia-2022"
                    if '-' in col_str:
                        parts = col_str.split('-')
                        if len(parts) >= 2:
                            try:
                                # Try first part as year
                                year_part = parts[0].strip()
                                year_int = int(year_part)
                                if 1900 <= year_int <= 2100:
                                    embedded_year = year_int
                                    st.write(f"  ✅ Found year in first part of `{col}`: **{embedded_year}**")
                            except:
                                try:
                                    # Try second part as year
                                    year_part = parts[1].strip()
                                    year_int = int(year_part)
                                    if 1900 <= year_int <= 2100:
                                        embedded_year = year_int
                                        st.write(f"  ✅ Found year in second part of `{col}`: **{embedded_year}**")
                                except:
                                    pass
                
                if is_direct_year:
                    year_value = int(col) if isinstance(col, int) else int(col_str)
                    available_years.append(year_value)
                    st.write(f"  ✅ Added direct year: **{year_value}**")
                elif embedded_year:
                    available_years.append(embedded_year)
                    st.write(f"  ✅ Added embedded year: **{embedded_year}**")
            
            st.write(f"🎯 **Final available years:** {available_years}")
            
            if available_years:
                available_years = list(set(available_years))  # Remove duplicates
                available_years.sort()
                selected_years = st.sidebar.multiselect(
                    "Selecciona los años:",
                    available_years,
                    default=available_years[:2] if len(available_years) >= 2 else available_years
                )
            else:
                st.warning("No se encontraron columnas de años en el formato YYYY")
                selected_years = []
            
            # Graph type selection
            graph_types = ["Gráfica 1 - Línea de Pobreza", "Gráfica 2 - Carencias", "Gráfica 3 - Comparación", "Gráfica 4 - Resumen y Comparación", "Gráfica 5 y 6 - Carencias Combinadas"]
            
            # Auto-detect based on sheet name
            if "5" in selected_sheet or "6" in selected_sheet:
                default_graph = "Gráfica 5 y 6 - Carencias Combinadas"
            else:
                auto_graph_type = determine_graph_type(selected_sheet, df)
                default_graph = auto_graph_type if auto_graph_type in graph_types else graph_types[0]
            
            selected_graph = st.sidebar.selectbox(
                "Tipo de gráfica:",
                graph_types,
                index=graph_types.index(default_graph) if default_graph in graph_types else 0
            )
            
            if selected_years:
                # Process data based on graph type
                if "Gráfica 1" in selected_graph:
                    render_graph1(df, selected_years)
                elif "Gráfica 2" in selected_graph:
                    render_graph2(df, selected_years)
                elif "Gráfica 3" in selected_graph:
                    render_graph3(df, selected_years)
                elif "Gráfica 4" in selected_graph:
                    render_graph4(df, selected_years)
                elif "Gráfica 5" in selected_graph or "Gráfica 6" in selected_graph:
                    render_graph5_and_6(sheets, selected_years)
                
                # Show original data
                with st.expander("📋 Ver datos originales"):
                    # Convert DataFrame to a format that Streamlit can handle
                    display_df = df.copy()
                    # Convert all columns to string to avoid Arrow serialization issues
                    for col in display_df.columns:
                        display_df[col] = display_df[col].astype(str)
                    st.dataframe(display_df)
            else:
                st.warning("Por favor selecciona al menos un año para visualizar los datos")
        else:
            st.error("❌ Error al cargar el archivo. Verifica que sea un archivo Excel válido.")
    else:
        st.info("👆 Sube un archivo Excel para comenzar")
        
        # Show example structure
        st.markdown("### 📋 Estructura esperada del archivo:")
        st.markdown("""
        Tu archivo Excel debe contener:
        - **Gráfica 1**: Columnas con años (2022, 2024, etc.) y filas con "Pobreza" y "Pobreza extrema"
        - **Gráfica 2**: Columnas con años y filas con "Carencia" o "Rezago educativo"
        - **Gráfica 3**: Columnas con años y filas con categorías para comparar
        """)

if __name__ == "__main__":
    main() 