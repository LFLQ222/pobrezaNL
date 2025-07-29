# 📊 Streamlit Poverty Dashboard

An interactive dashboard for visualizing poverty data from Excel files using Streamlit and Plotly.

## 🚀 Features

- **📈 Interactive Charts**: Line charts, horizontal bars, vertical bars, and combined views
- **📅 Year Selection**: Dynamic filtering by years
- **📊 Multiple Graph Types**: 
  - Graph 1: Poverty trends over time
  - Graph 2: Horizontal bar charts with deficiencies 
  - Graph 3: Vertical bar charts by categories
  - Graph 4: Combined summary views
  - Graph 5 & 6: Side-by-side carencias comparison
- **🎯 Change Indicators**: Visual arrows showing percentage point changes
- **📱 Responsive Design**: Works on desktop and mobile

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd streamlit-poverty-dashboard
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   streamlit run streamlit_app.py
   ```

## 📁 Usage

1. **Upload Excel File**: Use the file uploader to select your Excel file
2. **Select Graph Type**: Choose from the available visualization options
3. **Filter by Years**: Select specific years to compare
4. **Interact**: Hover over charts for detailed information

## 📋 Excel File Format

The application expects Excel files with the following structure:

### Sheet Names
- `Gráfica 1`, `Gráfica 2`, `Gráfica 3`, `Gráfica 4`, `Gráfica 5`, `Gráfica 6`

### Data Format
- **Percentage columns**: Named like "Porcentaje 2024", "Porcentaje 2022"
- **Change columns**: Named like "Cambio p.p"
- **Category columns**: First column should contain category/carencia names
- **Headers**: Can be in single or multi-row format

## 🎨 Features

### Change Indicators
- **↘️ Green arrows**: Decreases (improvement in poverty metrics)
- **↗️ Red arrows**: Increases (worsening in poverty metrics)  
- **→ Gray arrows**: No change
- **Values**: Displayed as percentage points (pp)

### Chart Types
- **Line Charts**: Trends over time
- **Horizontal Bars**: Category comparisons
- **Vertical Bars**: Grouped data visualization
- **Combined Views**: Side-by-side comparisons

## 🔧 Technical Details

### Dependencies
- **Streamlit**: Web application framework
- **Pandas**: Data manipulation and analysis
- **Plotly**: Interactive plotting library
- **OpenPyXL**: Excel file reading
- **NumPy**: Numerical computations

### Key Functions
- `load_excel_data()`: Smart Excel parsing with multi-row header support
- `clean_value()`: Data cleaning for percentage values
- `clean_change_value()`: Specialized cleaning for change values
- `render_graphX()`: Individual chart rendering functions

## 📊 Supported Data Types

- **Percentage values**: Automatically converts decimals to percentages
- **Absolute values**: Displayed in "miles de personas" format  
- **Change values**: Converted to percentage points (pp)
- **Multi-year data**: Supports dynamic year selection

## 🎯 Best Practices

1. **File Format**: Ensure Excel files follow the expected structure
2. **Data Quality**: Clean data for better visualizations
3. **Year Selection**: Select at least 2 years for change comparisons
4. **Chart Selection**: Choose appropriate chart types for your data

## 🐛 Troubleshooting

### Common Issues
- **"No se encontraron columnas de años"**: Check year column naming format
- **Empty charts**: Verify data format and year selection
- **Upload errors**: Ensure file is a valid Excel format (.xlsx)

### Data Format Tips
- Years should be in YYYY format (e.g., 2024, 2022)
- Percentage columns should contain "Porcentaje" or "Percentage"
- Change columns should contain "Cambio" or "Change"

## 📈 Example Usage

```python
# The app automatically detects:
# - Graph types based on sheet names
# - Years from column headers  
# - Data types (percentages vs absolute values)
# - Change calculations for multi-year data
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

---

**Made with ❤️ using Streamlit and Plotly** 