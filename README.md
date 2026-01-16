# Government Schools Distance Analysis System

## Overview
A comprehensive Flask-based web application that analyzes and compares distances from government schools to BEC (Balochistan Education Commission), NHCD (National Highway and Communication Development), and BEF (Balochistan Education Foundation) schools. The system identifies which special school type is nearest to each government school.

## Features

### 🎯 Core Functionality
- **Multi-School Type Analysis**: Compare distances to BEC, NHCD, and BEF schools simultaneously
- **Precise Distance Calculation**: Uses Haversine formula for accurate geographic distance measurements
- **Nearest School Detection**: Automatically identifies the closest school of each type for every government school

### 📊 Analysis & Reporting
- **Summary Statistics**: Comprehensive overview of school distributions and distances
- **Distance Range Breakdowns**: Categorizes schools by distance ranges (0-2km, 2-5km, 5-10km, 10+km)
- **Excel Export**: Multi-sheet Excel reports with summary, detailed analysis, and distance ranges
- **Interactive Charts**: Visual representations using Chart.js for better insights

### 🗺️ Mapping & Visualization
- **Interactive Map**: Leaflet-based map showing all schools with color-coded markers
- **School Popups**: Detailed information on click for each school
- **Map Export**: Download standalone HTML map files for offline viewing
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile devices

### 🎨 User Interface
- **Professional Design**: Modern, clean interface with gradient backgrounds
- **File Upload**: Drag-and-drop support for CSV and Excel files
- **Real-time Filtering**: Search and filter results by school type
- **Detailed Modal Views**: Pop-up modals with comprehensive school information

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup Instructions

1. **Navigate to the project directory**:
   ```bash
   cd GovToSchoolsDistanceSystem
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**:
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```

4. **Install required packages**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Starting the Application

1. **Run the Flask application**:
   ```bash
   python app.py
   ```

2. **Open your web browser** and navigate to:
   ```
   http://localhost:5000
   ```

### Using the System

#### Step 1: Upload Data Files

**Government Schools File** should contain:
- BemisCode
- School Name
- X-Cord, Y-Cord (coordinates)
- District, Tehsil, UC
- Level, Gender, Enrollmen
- Space for new Rooms, Total Rooms
- Toilets, Boundry wall, Drinking Water

**BEC/NHCD/BEF Schools File** should contain:
- BemisCode
- SchoolName
- Division, District, Tehsil
- Gender, SchoolLevel
- FunctionalStatus
- Student Count
- Source (must contain "BEC", "NHCD", or "BEF")
- _xCord, _yCord (coordinates)
- School Owned

#### Step 2: Analyze Data
- Click the "Analyze Distances" button
- Wait for the processing to complete
- You'll be automatically redirected to the results page

#### Step 3: View Results
The results page includes:
- **Summary Statistics**: Overview of all schools and their nearest types
- **Distribution Charts**: Visual breakdown of distance ranges
- **Interactive Map**: Geographic visualization of all schools
- **Detailed Table**: Searchable and filterable data table

#### Step 4: Export Results
- **Download Excel Report**: Click "Download Excel Report" for complete analysis
- **Download Map**: Click "Download Map" for offline map viewing

## File Structure

```
GovToSchoolsDistanceSystem/
│
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── README.md                   # This file
│
├── templates/
│   ├── index.html             # Upload page
│   └── results.html           # Results page
│
├── static/
│   ├── css/
│   │   └── style.css          # All styles
│   └── js/
│       ├── main.js            # Upload page JavaScript
│       └── results.js         # Results page JavaScript
│
├── uploads/                    # Uploaded files (auto-created)
└── downloads/                  # Generated reports (auto-created)
```

## Technical Details

### Distance Calculation
The system uses the Haversine formula to calculate great-circle distances between two points on Earth:

```
a = sin²(Δφ/2) + cos φ1 ⋅ cos φ2 ⋅ sin²(Δλ/2)
c = 2 ⋅ atan2(√a, √(1−a))
d = R ⋅ c
```

Where:
- φ is latitude
- λ is longitude
- R is Earth's radius (6,371 km)

### Analysis Process
1. **Data Loading**: Reads CSV/Excel files with proper encoding handling
2. **Coordinate Cleaning**: Validates and cleans coordinate data
3. **Distance Calculation**: Computes distances from each government school to all special schools
4. **Nearest School Detection**: Identifies the closest BEC, NHCD, and BEF school for each government school
5. **Summary Generation**: Creates statistical summaries and distance range breakdowns
6. **Report Creation**: Generates Excel reports with multiple sheets

### Performance Optimizations
- Efficient distance calculations using NumPy
- Minimal redundant computations
- Optimized data structures for quick lookups
- Client-side filtering and searching

## Browser Compatibility
- Chrome (recommended)
- Firefox
- Safari
- Edge
- Opera

## Supported File Formats
- CSV (.csv)
- Excel (.xlsx, .xls)

Maximum file size: 50MB

## Troubleshooting

### Common Issues

**Issue**: "Could not identify coordinate columns"
- **Solution**: Ensure your files have columns named X-Cord/Y-Cord or _xCord/_yCord

**Issue**: No schools showing on map
- **Solution**: Verify that coordinate data is present and in the correct format (decimal degrees)

**Issue**: File upload fails
- **Solution**: Check file size (must be under 50MB) and format (CSV or Excel)

**Issue**: Distance calculations seem incorrect
- **Solution**: Verify that coordinates are in decimal degrees, not DMS format

## Credits
- **Mapping**: Leaflet.js with OpenStreetMap tiles
- **Charts**: Chart.js
- **Icons**: Font Awesome
- **Backend**: Flask (Python)
- **Frontend**: Vanilla JavaScript

## License
© 2026 Government Schools Distance Analysis System. All rights reserved.

## Support
For questions or issues, please contact the development team.

## Version History
- **v1.0.0** (January 2026): Initial release with full functionality
