# Test Data Files

This folder contains sample data files for testing the Distance Analysis System.

## 📁 Files Available

### Government Schools
- **government_schools.csv** - CSV format (40 schools)
- **government_schools.xlsx** - Excel format (40 schools)

**Columns:**
- School Name
- BemisCode
- District
- Tehsil
- UC
- Level (Primary/Middle/High)
- Gender (Boys/Girls)
- Enrollment
- Y-Cord (Latitude)
- X-Cord (Longitude)

### Custom Schools (BEC/NHCD/BEF)
- **custom_schools.csv** - CSV format (20 schools)
- **custom_schools.xlsx** - Excel format (20 schools)

**Columns (matching actual BEF data structure):**
- BemisCode
- SchoolName
- Division
- District
- Tehsil
- Gender
- SchoolLevel
- FunctionalStatus
- Student Count
- Source (BEC/NHCD/BEF)
- _xCord (Longitude)
- _yCord (Latitude)
- School Owned

## 📊 Data Distribution

### By District:
- **Ziarat District:** 27 government schools, 10 custom schools
- **Quetta District:** 5 government schools, 4 custom schools
- **Pishin District:** 8 government schools, 6 custom schools

### Custom Schools by Type:
- **BEC Schools:** 6 schools
- **NHCD Schools:** 7 schools
- **BEF Schools:** 7 schools

## 🎯 How to Use

1. Open the Distance Analysis System at http://localhost:5000
2. Upload **government_schools.csv** (or .xlsx) as the Government Schools file
3. Upload **custom_schools.csv** (or .xlsx) as the BEC/NHCD/BEF Schools file
4. Click "Start Analysis"
5. View results showing all government schools within 5km of each custom school

## 📍 GPS Coordinates

All schools have realistic GPS coordinates from the Balochistan region:
- Ziarat District: ~30.38°N, 67.72°E
- Quetta District: ~30.19°N, 67.02°E
- Pishin District: ~30.58°N, 66.85°E

Schools are positioned within 0-5km of each other to test the distance analysis functionality.

## 📋 Expected Results

When you run the analysis with these test files, you should see:
- Multiple rows for each custom school (one per government school within 5km)
- Distance values ranging from 0 km (same location) to ~5 km
- Proper enrollment data displayed
- All custom school fields preserved in the output

## 🔄 Format

The output Excel file will have columns matching your specified format:
```
Custom_School_Name | Custom_Division | Custom_District | Custom_Tehsil | Custom_Level | 
Custom_Gender | Custom_Students | Custom_Functional_Status | Government_School_Name | 
Government_School_Level | Government_School_Gender | Government_School_District | 
Distance_km | Government_School_Enrollment
```
