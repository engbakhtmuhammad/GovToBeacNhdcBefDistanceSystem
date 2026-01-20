from flask import Flask, render_template, request, jsonify, send_file, Response, stream_with_context
import pandas as pd
import numpy as np
from math import radians, cos, sin, asin, sqrt
import os
from datetime import datetime
import json
from werkzeug.utils import secure_filename
import threading
import time
from queue import Queue

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DOWNLOAD_FOLDER'] = 'downloads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

# Store analysis sessions and their progress
analysis_sessions = {}
analysis_locks = {}

def make_json_serializable(obj):
    """Convert numpy/pandas types to JSON-serializable Python types"""
    if isinstance(obj, dict):
        return {key: make_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        # Check for NaN or Infinity
        if np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif pd.isna(obj):
        return None
    elif isinstance(obj, (float, int)):
        # Check Python native floats for NaN/Inf
        if isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
            return None
        return obj
    elif isinstance(obj, str):
        # Ensure string is valid (remove any null bytes or control characters)
        return obj.replace('\x00', '').strip()
    else:
        return obj

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    Returns distance in kilometers
    """
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r

def haversine_vectorized(lat1, lon1, lat2_array, lon2_array):
    """
    Vectorized haversine distance calculation
    Calculate distance from one point to multiple points
    Returns array of distances in kilometers
    """
    # Convert to radians
    lat1_rad = np.radians(lat1)
    lon1_rad = np.radians(lon1)
    lat2_rad = np.radians(lat2_array)
    lon2_rad = np.radians(lon2_array)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = np.sin(dlat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    
    return 6371 * c  # Earth radius in kilometers

def read_excel_or_csv(file_path):
    """Read CSV or Excel file"""
    try:
        if file_path.endswith('.csv'):
            return pd.read_csv(file_path, encoding='utf-8')
        else:
            return pd.read_excel(file_path)
    except UnicodeDecodeError:
        return pd.read_csv(file_path, encoding='latin-1')

def clean_coordinate(coord):
    """Clean and convert coordinate to float"""
    if pd.isna(coord):
        return None
    try:
        return float(str(coord).strip())
    except:
        return None

def get_column_mapping(df, data_type='unknown'):
    """Get flexible column mapping for different data formats"""
    columns = [col.strip() for col in df.columns]
    mapping = {}
    
    # Column mapping patterns
    patterns = {
        'bemis_code': ['bemiscode', 'bemis_code', 'bemis code'],
        'school_name': ['school name', 'schoolname', 'school_name'],
        'district': ['district'],
        'tehsil': ['tehsil'],
        'uc': ['uc'],
        'gender': ['gender', 'gende'],  # Handle typo in actual data
        'enrollment': ['enrollment', 'student count', 'students'],
        'level': ['level', 'schoollevel', 'school level'],
        'functional_status': ['functionalstatus', 'functional_status', 'functional status'],
        'source': ['source'],
        'division': ['division'],
        'space_for_rooms': ['space for new rooms', 'space_for_rooms'],
        'total_rooms': ['total rooms', 'total_rooms'],
        'toilets': ['toilets'],
        'boundary_wall': ['boundary wall', 'boundry wall', 'boundary_wall', 'boundry_wall'],
        'drinking_water': ['drinking water', 'drinking_water'],
        'school_owned': ['school owned', 'school_owned'],
        'toilets': ['toilets'],
        'boundary_wall': ['boundary wall', 'boundry wall', 'boundary_wall', 'boundry_wall'],
        'drinking_water': ['drinking water', 'drinking_water'],
        'school_owned': ['school owned', 'school_owned']
    }
    
    # Find matching columns
    for field, possible_names in patterns.items():
        for col in columns:
            if col.lower() in possible_names:
                mapping[field] = col
                break
    
    # Handle coordinates based on data type
    if data_type == 'government':
        # Government data: X-Cord = Latitude, Y-Cord = Longitude (swapped!)
        for col in columns:
            col_lower = col.lower()
            if ('x-cord' in col_lower or 'x cord' in col_lower) and 'cord' in col_lower:
                mapping['latitude'] = col  # X-Cord contains latitude
            elif ('y-cord' in col_lower or 'y cord' in col_lower) and 'cord' in col_lower:
                mapping['longitude'] = col  # Y-Cord contains longitude
    else:
        # Custom data: _yCord = Latitude, _xCord = Longitude (underscore format)
        for col in columns:
            col_lower = col.lower()
            if col_lower in ['_ycord', '_y_cord'] or ('_y' in col_lower and 'cord' in col_lower):
                mapping['latitude'] = col
            elif col_lower in ['_xcord', '_x_cord'] or ('_x' in col_lower and 'cord' in col_lower):
                mapping['longitude'] = col
            # Also handle X-Cord/Y-Cord format (normal: X=lon, Y=lat)
            elif 'y' in col_lower and ('cord' in col_lower or 'coord' in col_lower) and not col_lower.startswith('_'):
                mapping['latitude'] = col
            elif 'x' in col_lower and ('cord' in col_lower or 'coord' in col_lower) and not col_lower.startswith('_'):
                mapping['longitude'] = col
    
    return mapping

def analyze_distances(gov_df, special_df, session_id=None, progress_callback=None):
    """
    For each government school, find ALL custom schools (BEAC/NCHD/BEF) within 5km
    Returns detailed analysis with multiple rows per government school
    """
    results = []
    total_schools = len(gov_df)  # Iterate through government schools
    processed = 0
    
    # Standardize column names
    gov_df.columns = gov_df.columns.str.strip()
    special_df.columns = special_df.columns.str.strip()
    
    print(f"Government schools columns: {list(gov_df.columns)}")
    print(f"Custom schools columns: {list(special_df.columns)}")
    
    # Get column mappings for both datasets
    gov_mapping = get_column_mapping(gov_df, 'government')
    special_mapping = get_column_mapping(special_df, 'custom')
    
    print(f"Government column mapping: {gov_mapping}")
    print(f"Custom column mapping: {special_mapping}")
    
    # CRITICAL DIAGNOSTIC: Show actual values in Source and School Owned columns
    source_col = special_mapping.get('source')
    school_owned_col = special_mapping.get('school_owned')
    
    print(f"\n🔍 CRITICAL DIAGNOSTIC - Column Analysis:")
    print(f"   Source column found: '{source_col}'")
    print(f"   School Owned column found: '{school_owned_col}'")
    
    if source_col:
        print(f"\n   📋 Unique values in '{source_col}' column:")
        source_values = special_df[source_col].unique()
        for val in source_values:
            count = len(special_df[special_df[source_col] == val])
            print(f"      '{val}' : {count} schools")
    else:
        print(f"   ⚠️ Source column NOT found!")
    
    if school_owned_col:
        print(f"\n   📋 Unique values in '{school_owned_col}' column:")
        owned_values = special_df[school_owned_col].unique()
        for val in owned_values:
            count = len(special_df[special_df[school_owned_col] == val])
            print(f"      '{val}' : {count} schools")
    else:
        print(f"   ⚠️ School Owned column NOT found!")
    
    print(f"\n   📊 Sample rows from custom schools data:")
    if source_col and school_owned_col:
        for idx in range(min(5, len(special_df))):
            row = special_df.iloc[idx]
            name = row.get(special_mapping.get('school_name', 'Unknown'), 'Unknown')
            src = row.get(source_col, 'N/A')
            owned = row.get(school_owned_col, 'N/A')
            print(f"      {idx+1}. {name[:40]}")
            print(f"         Source='{src}', School_Owned='{owned}'")
    print()
    
    # Validate required columns
    if 'latitude' not in gov_mapping or 'longitude' not in gov_mapping:
        raise ValueError(f"Could not identify coordinate columns in government data. Available: {list(gov_df.columns)}")
    
    if 'latitude' not in special_mapping or 'longitude' not in special_mapping:
        raise ValueError(f"Could not identify coordinate columns in custom data. Available: {list(special_df.columns)}")
    
    print(f"Coordinate columns detected:")
    print(f"  Gov Latitude: {gov_mapping['latitude']}, Gov Longitude: {gov_mapping['longitude']}")
    print(f"  Custom Latitude: {special_mapping['latitude']}, Custom Longitude: {special_mapping['longitude']}")
    
    print(f"Enrollment column found: {gov_mapping.get('enrollment', 'Not found')}")
    
    # Pre-calculate custom school source breakdown for comparison tracking
    source_col = special_mapping.get('source')
    custom_sources_available = {}
    custom_sources_with_valid_coords = {}
    
    if source_col:
        for idx, row in special_df.iterrows():
            source = row.get(source_col, 'Unknown')
            custom_sources_available[source] = custom_sources_available.get(source, 0) + 1
            
            # Check if this school has valid coordinates
            lat = clean_coordinate(row.get(special_mapping['latitude']))
            lon = clean_coordinate(row.get(special_mapping['longitude']))
            if lat is not None and lon is not None:
                custom_sources_with_valid_coords[source] = custom_sources_with_valid_coords.get(source, 0) + 1
    
    print(f"\n📌 Custom Schools Available for Comparison:")
    for src in sorted(custom_sources_available.keys()):
        total = custom_sources_available[src]
        valid = custom_sources_with_valid_coords.get(src, 0)
        invalid = total - valid
        print(f"   {src}: {total} schools total ({valid} with valid coordinates, {invalid} invalid)")
        
        # Show sample coordinates for each source
        if valid > 0 and src in ['BEAC', 'NCHD', 'BEF']:
            source_schools = special_df[special_df[source_col] == src]
            sample_count = 0
            print(f"      Sample {src} coordinates:")
            for idx, school in source_schools.iterrows():
                lat = clean_coordinate(school.get(special_mapping['latitude']))
                lon = clean_coordinate(school.get(special_mapping['longitude']))
                if lat is not None and lon is not None:
                    name = school.get(special_mapping.get('school_name', 'Unknown'), 'Unknown')
                    district = school.get(special_mapping.get('district', 'Unknown'), 'Unknown')
                    print(f"         {name[:40]} ({district}): Lat={lat:.6f}, Lon={lon:.6f}")
                    sample_count += 1
                    if sample_count >= 2:  # Show 2 samples per source
                        break
    print()
    
    # Process each government school
    valid_gov_schools = 0
    invalid_coordinate_schools = 0
    first_school_sample_done = False
    
    for idx, gov_school in gov_df.iterrows():
        gov_lat = clean_coordinate(gov_school.get(gov_mapping['latitude']))
        gov_lon = clean_coordinate(gov_school.get(gov_mapping['longitude']))
        
        # Track schools with invalid coordinates
        has_valid_coords = gov_lat is not None and gov_lon is not None
        
        if not has_valid_coords:
            invalid_coordinate_schools += 1
            if invalid_coordinate_schools <= 3:  # Log first 3 invalid schools
                school_name = gov_school.get(gov_mapping.get('school_name'), 'N/A')
                print(f"⚠️ School {idx + 1}/{total_schools}: {school_name} - Invalid coordinates (will still be included in results)")
        else:
            valid_gov_schools += 1
            if valid_gov_schools <= 2:  # Log first 2 valid schools
                school_name = gov_school.get(gov_mapping.get('school_name', 'N/A'), 'N/A')
                print(f"✓ Processing school {idx + 1}/{total_schools}: {school_name} - Lat: {gov_lat}, Lon: {gov_lon}")
        
        # Get government school info using flexible mapping
        gov_school_name = gov_school.get(gov_mapping.get('school_name'), 'N/A')
        gov_bemis_code = gov_school.get(gov_mapping.get('bemis_code'), 'N/A')
        gov_district = gov_school.get(gov_mapping.get('district'), 'N/A')
        gov_tehsil = gov_school.get(gov_mapping.get('tehsil'), 'N/A')
        gov_uc = gov_school.get(gov_mapping.get('uc'), 'N/A')
        gov_level = gov_school.get(gov_mapping.get('level'), 'N/A')
        gov_gender = gov_school.get(gov_mapping.get('gender'), 'N/A')
        
        # Additional government school fields
        gov_space_for_rooms = gov_school.get(gov_mapping.get('space_for_rooms'), 'N/A')
        gov_total_rooms = gov_school.get(gov_mapping.get('total_rooms'), 'N/A')
        gov_toilets = gov_school.get(gov_mapping.get('toilets'), 'N/A')
        gov_boundary_wall = gov_school.get(gov_mapping.get('boundary_wall'), 'N/A')
        gov_drinking_water = gov_school.get(gov_mapping.get('drinking_water'), 'N/A')
        
        # Get enrollment value
        enrollment_col = gov_mapping.get('enrollment')
        enrollment_value = gov_school.get(enrollment_col, 'N/A') if enrollment_col else 'N/A'
        if pd.isna(enrollment_value) or str(enrollment_value).strip().upper() == 'N/A':
            enrollment_value = 'N/A'
        
        # Find ALL custom schools within 5km using vectorized calculation
        custom_schools_within_5km = []
        
        # Only calculate distances if government school has valid coordinates
        if has_valid_coords:
            # Vectorized distance calculation to all custom schools at once
            # SPECIAL HANDLING: BEAC and NCHD schools have swapped coordinates in the data
            custom_lats_raw = special_df[special_mapping['latitude']].apply(clean_coordinate).values
            custom_lons_raw = special_df[special_mapping['longitude']].apply(clean_coordinate).values
            
            # Swap coordinates for BEAC and NCHD schools only
            custom_lats = custom_lats_raw.copy()
            custom_lons = custom_lons_raw.copy()
            
            if source_col:
                for idx in range(len(special_df)):
                    source = special_df.iloc[idx].get(source_col)
                    if source in ['BEAC', 'NCHD']:
                        # Swap lat/lon for BEAC and NCHD
                        custom_lats[idx] = custom_lons_raw[idx]
                        custom_lons[idx] = custom_lats_raw[idx]
            
            # Filter out invalid coordinates
            valid_mask = ~(pd.isna(custom_lats) | pd.isna(custom_lons))
            valid_indices = np.where(valid_mask)[0]
            
            if len(valid_indices) > 0:
                # Calculate all distances at once
                distances = haversine_vectorized(gov_lat, gov_lon, 
                                                custom_lats[valid_mask], 
                                                custom_lons[valid_mask])
                
                # DIAGNOSTIC: For first valid school, show detailed analysis
                if not first_school_sample_done and source_col:
                    print(f"\n🔍 DIAGNOSTIC - First Government School Analysis:")
                    print(f"   School: {gov_school_name}")
                    print(f"   District: {gov_district}")
                    print(f"   Coordinates: Lat={gov_lat:.6f}, Lon={gov_lon:.6f}")
                    print(f"\n   🔍 Checking source column values during distance calc:")
                    print(f"   Source column name: '{source_col}'")
                    
                    # Show what source values are actually in the valid schools
                    valid_source_values = {}
                    for idx in valid_indices:
                        src_val = special_df.iloc[idx].get(source_col)
                        valid_source_values[src_val] = valid_source_values.get(src_val, 0) + 1
                    
                    print(f"   Source values in schools with valid coordinates:")
                    for src, cnt in valid_source_values.items():
                        print(f"      '{src}': {cnt} schools")
                    
                    print(f"\n   Distance analysis for each source type:")
                    
                    for check_source in ['BEAC', 'NCHD', 'BEF']:
                        print(f"\n      Checking for source = '{check_source}':")
                        source_mask = np.array([special_df.iloc[i].get(source_col) == check_source for i in valid_indices])
                        print(f"         Schools matching '{check_source}': {source_mask.sum()}")
                        
                        if source_mask.any():
                            source_distances = distances[source_mask]
                            source_indices = valid_indices[source_mask]
                            
                            nearest_dist = source_distances.min()
                            nearest_idx = source_indices[np.argmin(source_distances)]
                            nearest_school = special_df.iloc[nearest_idx]
                            nearest_name = nearest_school.get(special_mapping.get('school_name'), 'Unknown')
                            nearest_district = nearest_school.get(special_mapping.get('district'), 'Unknown')
                            
                            within_5km = (source_distances <= 5.0).sum()
                            within_10km = (source_distances <= 10.0).sum()
                            
                            print(f"         ✅ Found {len(source_distances)} {check_source} schools")
                            print(f"         Nearest: {nearest_name[:50]} ({nearest_district})")
                            print(f"         Distance: {nearest_dist:.2f} km")
                            print(f"         Within 5km: {within_5km} schools")
                            print(f"         Within 10km: {within_10km} schools")
                            
                            # Show closest 3 schools
                            sorted_idx = np.argsort(source_distances)[:3]
                            print(f"         Closest 3 schools:")
                            for rank, idx_pos in enumerate(sorted_idx, 1):
                                sch_idx = source_indices[idx_pos]
                                dist = source_distances[idx_pos]
                                sch = special_df.iloc[sch_idx]
                                sch_name = sch.get(special_mapping.get('school_name'), 'Unknown')
                                print(f"            {rank}. {sch_name[:40]} - {dist:.2f} km")
                        else:
                            print(f"         ❌ No schools found with source='{check_source}'")
                            print(f"         This means the Source column doesn't contain '{check_source}'")
                    
                    first_school_sample_done = True
                    print()
                
                # Find schools within 5km
                within_5km_mask = distances <= 5.0
                within_5km_indices = valid_indices[within_5km_mask]
                within_5km_distances = distances[within_5km_mask]
                
                # Create result entries for schools within 5km
                for idx_offset, (custom_idx, distance) in enumerate(zip(within_5km_indices, within_5km_distances)):
                    custom_school = special_df.iloc[custom_idx]
                    custom_source_val = custom_school.get(special_mapping.get('source'), 'N/A')
                    
                    # Use the corrected coordinates (already swapped above for BEAC/NCHD)
                    custom_info = {
                        'custom_school_name': custom_school.get(special_mapping.get('school_name'), 'N/A'),
                        'custom_bemis_code': custom_school.get(special_mapping.get('bemis_code'), 'N/A'),
                        'custom_division': custom_school.get(special_mapping.get('division'), 'N/A'),
                        'custom_district': custom_school.get(special_mapping.get('district'), 'N/A'),
                        'custom_tehsil': custom_school.get(special_mapping.get('tehsil'), 'N/A'),
                        'custom_level': custom_school.get(special_mapping.get('level'), 'N/A'),
                        'custom_gender': custom_school.get(special_mapping.get('gender'), 'N/A'),
                        'custom_students': custom_school.get(special_mapping.get('enrollment'), 'N/A'),
                        'custom_functional_status': custom_school.get(special_mapping.get('functional_status'), 'N/A'),
                        'custom_source': custom_source_val,
                        'distance': round(float(distance), 2),
                        'custom_latitude': custom_lats[custom_idx],  # Already corrected
                        'custom_longitude': custom_lons[custom_idx]  # Already corrected
                    }
                    custom_schools_within_5km.append(custom_info)
            
            # Sort by distance (nearest first)
            custom_schools_within_5km.sort(key=lambda x: x['distance'])
        
        # Create result rows - ONLY for schools with custom schools within 5km
        if has_valid_coords and len(custom_schools_within_5km) > 0:
            # Create a result row for each custom school within 5km
            for custom_info in custom_schools_within_5km:
                result = {
                    'gov_school_name': gov_school_name,
                    'gov_bemis_code': gov_bemis_code,
                    'gov_district': gov_district,
                    'gov_tehsil': gov_tehsil,
                    'gov_uc': gov_uc,
                    'gov_level': gov_level,
                    'gov_gender': gov_gender,
                    'gov_enrollment': enrollment_value,
                    'gov_space_for_rooms': gov_space_for_rooms,
                    'gov_total_rooms': gov_total_rooms,
                    'gov_toilets': gov_toilets,
                    'gov_boundary_wall': gov_boundary_wall,
                    'gov_drinking_water': gov_drinking_water,
                    'gov_latitude': gov_lat,
                    'gov_longitude': gov_lon,
                    'custom_school_name': custom_info['custom_school_name'],
                    'custom_bemis_code': custom_info['custom_bemis_code'],
                    'custom_division': custom_info['custom_division'],
                    'custom_district': custom_info['custom_district'],
                    'custom_tehsil': custom_info['custom_tehsil'],
                    'custom_level': custom_info['custom_level'],
                    'custom_gender': custom_info['custom_gender'],
                    'custom_students': custom_info['custom_students'],
                    'custom_functional_status': custom_info['custom_functional_status'],
                    'custom_source': custom_info['custom_source'],
                    'distance_km': custom_info['distance'],
                    'custom_latitude': custom_info['custom_latitude'],
                    'custom_longitude': custom_info['custom_longitude'],
                    'custom_schools_count': len(custom_schools_within_5km)
                }
                results.append(result)
        
        processed += 1
        
        # Detailed logging for tracking
        if processed <= 3 or processed % 50 == 0:  # Log first 3 and every 50th school
            if has_valid_coords and len(custom_schools_within_5km) > 0:
                print(f"📊 Gov school {processed}/{total_schools}: found {len(custom_schools_within_5km)} custom schools - INCLUDED")
            else:
                status = "invalid coords" if not has_valid_coords else "no custom schools within 5km"
                print(f"⊘ Gov school {processed}/{total_schools}: {status} - EXCLUDED")
        
        # Report progress less frequently (every 10 schools instead of every school)
        if progress_callback and session_id and (processed % 10 == 0 or processed == total_schools):
            # Always report progress with the latest result
            if results:  # If we have any results at all
                progress_callback(session_id, results[-1], processed, total_schools)
            elif processed == total_schools:  # End of processing
                progress_callback(session_id, None, processed, total_schools)
    
    # Count results by custom school source type
    source_breakdown = {}
    for r in results:
        source = r.get('custom_source', 'N/A')
        source_breakdown[source] = source_breakdown.get(source, 0) + 1
    
    # Count unique custom schools found by source
    unique_custom_found = {}
    for r in results:
        if r.get('custom_source') != 'N/A':
            key = f"{r['custom_school_name']}_{r['custom_source']}"
            source = r.get('custom_source', 'Unknown')
            if source not in unique_custom_found:
                unique_custom_found[source] = set()
            unique_custom_found[source].add(key)
    
    print(f"\n=== Analysis Complete ===")
    print(f"✓ Total government schools in file: {total_schools}")
    print(f"✓ Total government schools processed: {processed}")
    print(f"✓ Schools with valid coordinates: {valid_gov_schools}")
    print(f"⚠️ Schools with invalid coordinates: {invalid_coordinate_schools}")
    print(f"✓ Total result rows generated: {len(results)}")
    print(f"\n📊 Results by Custom School Source (Result Rows):")
    for source, count in sorted(source_breakdown.items()):
        print(f"   {source}: {count} result rows")
    
    print(f"\n🎯 Unique Custom Schools Found Within 5km:")
    if unique_custom_found:
        for source in sorted(unique_custom_found.keys()):
            print(f"   {source}: {len(unique_custom_found[source])} unique schools found")
    else:
        print(f"   No custom schools found within 5km of any government school")
    
    # Show which sources were available but not found
    gov_schools_with_matches = len(set(r['gov_school_name'] for r in results if r.get('custom_source') != 'N/A'))
    gov_schools_excluded = total_schools - gov_schools_with_matches
    
    print(f"\n📍 Summary:")
    print(f"   - Government schools WITH custom schools nearby: {gov_schools_with_matches} (INCLUDED in results)")
    print(f"   - Government schools with NO custom schools within 5km: {gov_schools_excluded} (EXCLUDED from results)")
    print(f"\n✅ Only government schools with nearby custom schools are included.")
    print(f"📊 Total result rows: {len(results)} (showing gov-to-custom school matches)")
    
    return results

def generate_summary_statistics(results):
    """Generate summary statistics from analysis results"""
    if not results:
        return {
            'total_rows': 0,
            'total_gov_schools': 0,
            'total_custom_schools_found': 0,
            'avg_distance': 0,
            'avg_custom_schools_per_gov': 0
        }
    
    # Get unique government schools
    unique_gov_schools = set(r['gov_school_name'] for r in results)
    
    # Count total custom schools found (exclude N/A entries)
    total_custom_schools = len([r for r in results if r.get('custom_source') != 'N/A'])
    
    # Calculate average distance - filter out 'N/A' string values
    distances = [r['distance_km'] for r in results if isinstance(r['distance_km'], (int, float))]
    avg_distance = round(np.mean(distances), 2) if distances else 0
    
    # Calculate average distances by source type (BEAC, NCHD, BEF only)
    beac_distances = [r['distance_km'] for r in results if r.get('custom_source') == 'BEAC' and isinstance(r['distance_km'], (int, float))]
    nchd_distances = [r['distance_km'] for r in results if r.get('custom_source') == 'NCHD' and isinstance(r['distance_km'], (int, float))]
    bef_distances = [r['distance_km'] for r in results if r.get('custom_source') == 'BEF' and isinstance(r['distance_km'], (int, float))]
    
    avg_beac_distance = round(np.mean(beac_distances), 2) if beac_distances else 0
    avg_nchd_distance = round(np.mean(nchd_distances), 2) if nchd_distances else 0
    avg_bef_distance = round(np.mean(bef_distances), 2) if bef_distances else 0
    
    # Calculate average custom schools per government school
    gov_school_counts = {}
    for r in results:
        gov_name = r['gov_school_name']
        if gov_name not in gov_school_counts:
            gov_school_counts[gov_name] = 0
        gov_school_counts[gov_name] += 1
    
    avg_custom_per_gov = round(np.mean(list(gov_school_counts.values())), 1) if gov_school_counts else 0
    
    # Distance ranges by source type
    beac_dist_0_2 = sum(1 for d in beac_distances if d <= 2)
    beac_dist_2_5 = sum(1 for d in beac_distances if 2 < d <= 5)
    beac_dist_5_10 = 0  # We only show up to 5km
    beac_dist_10_plus = 0
    
    nchd_dist_0_2 = sum(1 for d in nchd_distances if d <= 2)
    nchd_dist_2_5 = sum(1 for d in nchd_distances if 2 < d <= 5)
    nchd_dist_5_10 = 0
    nchd_dist_10_plus = 0
    
    bef_dist_0_2 = sum(1 for d in bef_distances if d <= 2)
    bef_dist_2_5 = sum(1 for d in bef_distances if 2 < d <= 5)
    bef_dist_5_10 = 0
    bef_dist_10_plus = 0
    
    # Overall distance ranges
    dist_0_2 = sum(1 for d in distances if d <= 2)
    dist_2_5 = sum(1 for d in distances if 2 < d <= 5)
    
    summary = {
        'total_rows': total_custom_schools,
        'total_gov_schools': len(unique_gov_schools),
        'total_custom_schools_found': total_custom_schools,
        'avg_distance': avg_distance,
        'avg_beac_distance': avg_beac_distance,
        'avg_nchd_distance': avg_nchd_distance,
        'avg_bef_distance': avg_bef_distance,
        'avg_custom_schools_per_gov': avg_custom_per_gov,
        'distance_ranges': {
            '0-2km': dist_0_2,
            '2-5km': dist_2_5
        },
        'beac_distance_ranges': {
            '0-2km': beac_dist_0_2,
            '2-5km': beac_dist_2_5,
            '5-10km': beac_dist_5_10,
            '10+km': beac_dist_10_plus
        },
        'nchd_distance_ranges': {
            '0-2km': nchd_dist_0_2,
            '2-5km': nchd_dist_2_5,
            '5-10km': nchd_dist_5_10,
            '10+km': nchd_dist_10_plus
        },
        'bef_distance_ranges': {
            '0-2km': bef_dist_0_2,
            '2-5km': bef_dist_2_5,
            '5-10km': bef_dist_5_10,
            '10+km': bef_dist_10_plus
        },
        'nearest_beac_count': len(beac_distances),
        'nearest_nchd_count': len(nchd_distances),
        'nearest_bef_count': len(bef_distances)
    }
    
    return summary

def process_analysis_background(session_id, gov_path, special_path):
    """
    Process analysis in background and update session data progressively
    """
    try:
        # Update session status (already initialized in upload route)
        if session_id in analysis_sessions:
            analysis_sessions[session_id]['status'] = 'reading_files'
        
        # Read files
        gov_df = read_excel_or_csv(gov_path)
        special_df = read_excel_or_csv(special_path)
        
        # Log source breakdown
        special_mapping = get_column_mapping(special_df, 'custom')
        if 'source' in special_mapping:
            source_col = special_mapping['source']
            source_counts = special_df[source_col].value_counts()
            print(f"\n=== Custom Schools Breakdown ===")
            print(f"Total custom schools: {len(special_df)}")
            for source, count in source_counts.items():
                print(f"  {source}: {count} schools")
            print("=" * 35 + "\n")
        
        if session_id in analysis_sessions:
            analysis_sessions[session_id]['total'] = len(gov_df)  # Total government schools
            analysis_sessions[session_id]['status'] = 'analyzing'
        
        def progress_callback(sid, result, processed, total):
            if sid in analysis_sessions:
                if result is not None:
                    analysis_sessions[sid]['results'].append(result)
                analysis_sessions[sid]['progress'] = processed
                analysis_sessions[sid]['total'] = total
        
        # Perform analysis with progress updates
        results = analyze_distances(gov_df, special_df, session_id, progress_callback)
        summary = generate_summary_statistics(results)
        
        # Update session with final results
        analysis_sessions[session_id]['status'] = 'completed'
        analysis_sessions[session_id]['results'] = results
        analysis_sessions[session_id]['summary'] = summary
        analysis_sessions[session_id]['progress'] = len(gov_df)  # Total government schools processed
        
        print(f"Session {session_id} completed: {len(results)} results from {len(gov_df)} schools")
        
        # Save final results to JSON
        results_filename = f"results_{session_id}.json"
        results_path = os.path.join(app.config['DOWNLOAD_FOLDER'], results_filename)
        
        with open(results_path, 'w') as f:
            json_safe_data = {
                'results': make_json_serializable(results),
                'summary': make_json_serializable(summary)
            }
            json.dump(json_safe_data, f, indent=2)
        
        # Create Excel report
        excel_filename = f"distance_analysis_{session_id}.xlsx"
        excel_path = os.path.join(app.config['DOWNLOAD_FOLDER'], excel_filename)
        create_excel_report(results, summary, excel_path)
        
        analysis_sessions[session_id]['excel_file'] = excel_filename
        analysis_sessions[session_id]['results_file'] = results_filename
        
    except Exception as e:
        print(f"Error in session {session_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        if session_id in analysis_sessions:
            analysis_sessions[session_id]['status'] = 'error'
            analysis_sessions[session_id]['error'] = str(e)

def create_excel_report(results, summary, output_path):
    """Create Excel report with custom schools and their nearby government schools"""
    try:
        print(f"📝 Creating Excel report with {len(results)} rows...")
        
        # Create DataFrame directly from results for better performance
        detailed_data = []
        for r in results:
            # Format distance properly - keep numeric if possible, otherwise as string
            distance_value = r.get('distance_km', 'N/A')
            if isinstance(distance_value, (int, float)):
                distance_display = round(distance_value, 2)
            else:
                distance_display = 'N/A'
            
            row = {
                'Government_School_Name': str(r.get('gov_school_name', 'N/A')),
                'Government_BemisCode': str(r.get('gov_bemis_code', 'N/A')),
                'Government_District': str(r.get('gov_district', 'N/A')),
                'Government_Tehsil': str(r.get('gov_tehsil', 'N/A')),
                'Government_UC': str(r.get('gov_uc', 'N/A')),
                'Government_Level': str(r.get('gov_level', 'N/A')),
                'Government_Gender': str(r.get('gov_gender', 'N/A')),
                'Government_Enrollment': r.get('gov_enrollment', 'N/A'),
                'Government_Latitude': r.get('gov_latitude', 'N/A'),
                'Government_Longitude': r.get('gov_longitude', 'N/A'),
                'Government_Space_for_new_Rooms': str(r.get('gov_space_for_rooms', 'N/A')),
                'Government_Total_Rooms': str(r.get('gov_total_rooms', 'N/A')),
                'Government_Toilets': str(r.get('gov_toilets', 'N/A')),
                'Government_Boundary_Wall': str(r.get('gov_boundary_wall', 'N/A')),
                'Government_Drinking_Water': str(r.get('gov_drinking_water', 'N/A')),
                'Custom_School_Name': str(r.get('custom_school_name', 'N/A')),
                'Custom_BemisCode': str(r.get('custom_bemis_code', 'N/A')),
                'Custom_Source': str(r.get('custom_source', 'N/A')),
                'Custom_Division': str(r.get('custom_division', 'N/A')),
                'Custom_District': str(r.get('custom_district', 'N/A')),
                'Custom_Tehsil': str(r.get('custom_tehsil', 'N/A')),
                'Custom_Level': str(r.get('custom_level', 'N/A')),
                'Custom_Gender': str(r.get('custom_gender', 'N/A')),
                'Custom_Students': r.get('custom_students', 'N/A'),
                'Custom_Functional_Status': str(r.get('custom_functional_status', 'N/A')),
                'Custom_Latitude': r.get('custom_latitude', 'N/A'),
                'Custom_Longitude': r.get('custom_longitude', 'N/A'),
                'Distance_km': distance_display,
                'Custom_Schools_Count': r.get('custom_schools_count', 0)
            }
            detailed_data.append(row)
        
        # Create DataFrames
        df_detailed = pd.DataFrame(detailed_data)
        print(f"📊 DataFrame created: {len(df_detailed)} rows, {len(df_detailed.columns)} columns")
        
        # Summary data
        summary_data = {
            'Metric': [
                'Total Result Rows',
                'Total Government Schools',
                'Total Custom Schools Found (within 5km)',
                'Average Distance (km)',
                'Average Custom Schools per Government School'
            ],
            'Value': [
                summary.get('total_rows', 0),
                summary.get('total_gov_schools', 0),
                summary.get('total_custom_schools_found', 0),
                summary.get('avg_distance', 0),
                summary.get('avg_custom_schools_per_gov', 0)
            ]
        }
        df_summary = pd.DataFrame(summary_data)
        
        # Write to Excel
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df_summary.to_excel(writer, sheet_name='Summary', index=False)
            df_detailed.to_excel(writer, sheet_name='Detailed Analysis', index=False)
        
        # Verify file was created
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"✅ Excel file created successfully: {output_path} ({file_size:,} bytes)")
        else:
            print(f"❌ Excel file was NOT created: {output_path}")
            
    except Exception as e:
        print(f"❌ Error creating Excel report: {str(e)}")
        import traceback
        traceback.print_exc()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    try:
        # Check if files are present
        if 'gov_file' not in request.files or 'special_file' not in request.files:
            return jsonify({'error': 'Both files are required'}), 400
        
        gov_file = request.files['gov_file']
        special_file = request.files['special_file']
        
        if gov_file.filename == '' or special_file.filename == '':
            return jsonify({'error': 'No files selected'}), 400
        
        if not (allowed_file(gov_file.filename) and allowed_file(special_file.filename)):
            return jsonify({'error': 'Invalid file type. Please upload CSV or Excel files'}), 400
        
        # Save uploaded files
        session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        gov_filename = secure_filename(f"gov_{session_id}_{gov_file.filename}")
        special_filename = secure_filename(f"special_{session_id}_{special_file.filename}")
        
        gov_path = os.path.join(app.config['UPLOAD_FOLDER'], gov_filename)
        special_path = os.path.join(app.config['UPLOAD_FOLDER'], special_filename)
        
        gov_file.save(gov_path)
        special_file.save(special_path)
        
        # Initialize session BEFORE starting thread
        analysis_sessions[session_id] = {
            'status': 'initializing',
            'progress': 0,
            'total': 0,
            'results': [],
            'summary': None,
            'error': None
        }
        
        # Start background processing
        thread = threading.Thread(target=process_analysis_background, args=(session_id, gov_path, special_path))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'session_id': session_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/progress/<session_id>')
def progress_stream(session_id):
    """Server-Sent Events endpoint for progress updates"""
    def generate():
        last_status = None
        while True:
            if session_id in analysis_sessions:
                session = analysis_sessions[session_id]
                
                # Only send if status changed or it's a progress update
                current_status = session['status']
                
                data = {
                    'status': session['status'],
                    'progress': int(session['progress']) if session['progress'] is not None else 0,
                    'total': int(session['total']) if session['total'] is not None else 0,
                    'results': make_json_serializable(session['results'][-5:]) if len(session['results']) > 0 else [],
                    'summary': make_json_serializable(session['summary']),
                    'error': session['error']
                }
                
                yield f"data: {json.dumps(data)}\n\n"
                
                if session['status'] in ['completed', 'error']:
                    print(f"SSE stream ending for {session_id}: status={session['status']}")
                    break
                    
                last_status = current_status
            else:
                yield f"data: {{\"status\": \"waiting\"}}\n\n"
            
            time.sleep(0.3)  # Update every 300ms (faster updates)
    
    response = Response(stream_with_context(generate()), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    return response

@app.route('/results/<session_id>')
def results(session_id):
    """Results page - loads immediately and updates progressively"""
    return render_template('results.html', session_id=session_id)

@app.route('/api/session/<session_id>')
def get_session_data(session_id):
    """Get current session data - lightweight response for polling"""
    if session_id in analysis_sessions:
        session = analysis_sessions[session_id]
        
        # ALWAYS return a lightweight response - never send all results here
        # The full results are fetched by loadFinalData() from /api/results/
        data = {
            'status': session['status'],
            'progress': int(session['progress']) if session['progress'] is not None else 0,
            'total': int(session['total']) if session['total'] is not None else 0,
            'results_count': len(session['results']),
            'error': session.get('error')
        }
        
        # Only include summary for completed sessions
        if session['status'] == 'completed' and session.get('summary'):
            data['summary'] = make_json_serializable(session['summary'])
        
        print(f"📡 API session response: status={data['status']}, progress={data['progress']}/{data['total']}, results_count={data['results_count']}")
            
        response = jsonify(data)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    return jsonify({'error': 'Session not found'}), 404

@app.route('/download/<session_id>/<file_type>')
def download(session_id, file_type):
    try:
        if file_type == 'excel':
            filename = f"distance_analysis_{session_id}.xlsx"
        else:
            filename = f"results_{session_id}.json"
        
        file_path = os.path.join(app.config['DOWNLOAD_FOLDER'], filename)
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return f"Error downloading file: {str(e)}", 500

@app.route('/api/results/<session_id>')
def get_results_data(session_id):
    try:
        print(f"📊 API results requested for session: {session_id}")
        
        # First check if session is in memory
        if session_id in analysis_sessions:
            session = analysis_sessions[session_id]
            print(f"📊 Session found in memory: status={session['status']}, results_count={len(session['results'])}")
            if session['status'] == 'completed':
                print(f"📊 Serializing {len(session['results'])} results...")
                data = {
                    'results': make_json_serializable(session['results']),
                    'summary': make_json_serializable(session['summary'])
                }
                # Check response size
                response = jsonify(data)
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response.headers['Pragma'] = 'no-cache'
                response.headers['Expires'] = '0'
                print(f"✅ Returning {len(data['results'])} results to frontend")
                return response
        
        # Otherwise try to load from file
        results_path = os.path.join(app.config['DOWNLOAD_FOLDER'], f"results_{session_id}.json")
        print(f"Trying to load from file: {results_path}")
        with open(results_path, 'r') as f:
            data = json.load(f)
        print(f"Loaded from file: {len(data.get('results', []))} results")
        return jsonify(data)
    except Exception as e:
        print(f"Error in get_results_data: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['DOWNLOAD_FOLDER'], exist_ok=True)
    
    print("\n🏫 Government Schools Distance Analysis System")
    print("=" * 50)
    print("🚀 Server starting...")
    print("📍 Upload government schools and BEF/BEAC/NCHD data")
    print("🔍 Analyze proximity within 5km radius")
    print("📊 Generate detailed reports and visualizations")
    print("🌐 Access at: http://localhost:5000")
    print("=" * 50)
    
    app.run(debug=True, port=5000)
