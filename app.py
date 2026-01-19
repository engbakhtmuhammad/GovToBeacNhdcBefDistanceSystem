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

def analyze_distances(gov_df, special_df, session_id=None, progress_callback=None):
    """
    For each government school, find ALL custom schools (BEC/NHCD/BEF) within 5km
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
    
    # Identify coordinate columns in government data
    # NOTE: X-Cord contains LATITUDE and Y-Cord contains LONGITUDE in government data (swapped!)
    gov_lat_col = None
    gov_lon_col = None
    for col in gov_df.columns:
        col_lower = col.lower()
        if 'x' in col_lower and ('cord' in col_lower or 'coord' in col_lower or col_lower == 'x-cord'):
            gov_lat_col = col  # X-Cord actually contains latitude
        elif 'y' in col_lower and ('cord' in col_lower or 'coord' in col_lower or col_lower == 'y-cord'):
            gov_lon_col = col  # Y-Cord actually contains longitude
    
    # Identify coordinate columns in custom schools data
    special_lat_col = None
    special_lon_col = None
    for col in special_df.columns:
        col_lower = col.lower()
        if 'y' in col_lower and ('cord' in col_lower or 'coord' in col_lower):
            special_lat_col = col
        elif 'x' in col_lower and ('cord' in col_lower or 'coord' in col_lower):
            special_lon_col = col
    
    if not all([gov_lat_col, gov_lon_col, special_lat_col, special_lon_col]):
        raise ValueError("Could not identify coordinate columns in the uploaded files")
    
    print(f"Coordinate columns detected:")
    print(f"  Gov Latitude: {gov_lat_col}, Gov Longitude: {gov_lon_col}")
    print(f"  Custom Latitude: {special_lat_col}, Custom Longitude: {special_lon_col}")
    
    # Find enrollment column in government data
    enrollment_col = None
    for col in gov_df.columns:
        col_lower = col.lower()
        if 'enroll' in col_lower:
            enrollment_col = col
            break
    
    print(f"Enrollment column found: {enrollment_col}")
    
    # Process each government school
    valid_gov_schools = 0
    skipped_gov_schools = 0
    
    for idx, gov_school in gov_df.iterrows():
        gov_lat = clean_coordinate(gov_school.get(gov_lat_col))
        gov_lon = clean_coordinate(gov_school.get(gov_lon_col))
        
        if gov_lat is None or gov_lon is None:
            skipped_gov_schools += 1
            if skipped_gov_schools <= 3:  # Log first 3 skipped schools
                print(f"Skipping school {idx}: Invalid coordinates - Lat: {gov_school.get(gov_lat_col)}, Lon: {gov_school.get(gov_lon_col)}")
            continue
        
        valid_gov_schools += 1
        if valid_gov_schools <= 2:  # Log first 2 valid schools
            print(f"Processing school {idx}: {gov_school.get('School Name')} - Lat: {gov_lat}, Lon: {gov_lon}")
        
        # Get government school info
        gov_school_name = gov_school.get('School Name', 'N/A')
        gov_bemis_code = gov_school.get('BemisCode', 'N/A')
        gov_district = gov_school.get('District', 'N/A')
        gov_tehsil = gov_school.get('Tehsil', 'N/A')
        gov_uc = gov_school.get('UC', 'N/A')
        gov_level = gov_school.get('Level', 'N/A')
        gov_gender = gov_school.get('Gender', 'N/A')
        
        # Additional government school fields
        gov_space_for_rooms = gov_school.get('Space for new Rooms', 'N/A')
        gov_total_rooms = gov_school.get('Total Rooms', 'N/A')
        gov_toilets = gov_school.get('Toilets', 'N/A')
        gov_boundary_wall = gov_school.get('Boundry wall', gov_school.get('Boundary wall', 'N/A'))
        gov_drinking_water = gov_school.get('Drinking Water', 'N/A')
        
        # Get enrollment value
        enrollment_value = gov_school.get(enrollment_col, 'N/A') if enrollment_col else 'N/A'
        if pd.isna(enrollment_value) or str(enrollment_value).strip().upper() == 'N/A':
            enrollment_value = 'N/A'
        
        # Find ALL custom schools within 5km using vectorized calculation
        custom_schools_within_5km = []
        
        # Vectorized distance calculation to all custom schools at once
        custom_lats = special_df[special_lat_col].apply(clean_coordinate).values
        custom_lons = special_df[special_lon_col].apply(clean_coordinate).values
        
        # Filter out invalid coordinates
        valid_mask = ~(pd.isna(custom_lats) | pd.isna(custom_lons))
        valid_indices = np.where(valid_mask)[0]
        
        if len(valid_indices) > 0:
            # Calculate all distances at once
            distances = haversine_vectorized(gov_lat, gov_lon, 
                                            custom_lats[valid_mask], 
                                            custom_lons[valid_mask])
            
            # Find schools within 5km
            within_5km_mask = distances <= 5.0
            within_5km_indices = valid_indices[within_5km_mask]
            within_5km_distances = distances[within_5km_mask]
            
            # Create result entries for schools within 5km
            for idx_offset, (custom_idx, distance) in enumerate(zip(within_5km_indices, within_5km_distances)):
                custom_school = special_df.iloc[custom_idx]
                
                custom_info = {
                    'custom_school_name': custom_school.get('SchoolName', 'N/A'),
                    'custom_bemis_code': custom_school.get('BemisCode', 'N/A'),
                    'custom_division': custom_school.get('Division', 'N/A'),
                    'custom_district': custom_school.get('District', 'N/A'),
                    'custom_tehsil': custom_school.get('Tehsil', 'N/A'),
                    'custom_level': custom_school.get('SchoolLevel', custom_school.get('Level', 'N/A')),
                    'custom_gender': custom_school.get('Gender', 'N/A'),
                    'custom_students': custom_school.get('Student Count', custom_school.get('Students', 'N/A')),
                    'custom_functional_status': custom_school.get('FunctionalStatus', 'N/A'),
                    'custom_source': custom_school.get('Source', 'N/A'),
                    'distance': round(float(distance), 2),
                    'custom_latitude': custom_lats[custom_idx],
                    'custom_longitude': custom_lons[custom_idx]
                }
                custom_schools_within_5km.append(custom_info)
        
        # Sort by distance (nearest first)
        custom_schools_within_5km.sort(key=lambda x: x['distance'])
        
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
                'custom_schools_count': len(custom_schools_within_5km)  # How many custom schools near this gov school
            }
            results.append(result)
        
        processed += 1
        
        if processed <= 3 or processed % 50 == 0:  # Log first 3 and every 50th school
            print(f"Gov school {processed}/{total_schools}: Found {len(custom_schools_within_5km)} custom schools within 5km")
        
        # Report progress less frequently (every 10 schools instead of every school)
        if progress_callback and session_id and (processed % 10 == 0 or processed == total_schools):
            # Always report progress, even if no schools found
            if results:  # If we have any results at all
                progress_callback(session_id, results[-1], processed, total_schools)
            elif processed == total_schools:  # End of processing
                progress_callback(session_id, None, processed, total_schools)
    
    print(f"\n=== Analysis Complete ===")
    print(f"Total government schools processed: {processed}")
    print(f"Total results generated: {len(results)}")
    print(f"Valid gov schools: {valid_gov_schools}, Skipped: {skipped_gov_schools}")
    
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
    
    # Count total custom schools found
    total_custom_schools = len(results)
    
    # Calculate average distance
    distances = [r['distance_km'] for r in results]
    avg_distance = round(np.mean(distances), 2) if distances else 0
    
    # Calculate average distances by source type
    bec_distances = [r['distance_km'] for r in results if r.get('custom_source') == 'BEC']
    nhcd_distances = [r['distance_km'] for r in results if r.get('custom_source') == 'NHCD']
    bef_distances = [r['distance_km'] for r in results if r.get('custom_source') == 'BEF']
    
    avg_bec_distance = round(np.mean(bec_distances), 2) if bec_distances else 0
    avg_nhcd_distance = round(np.mean(nhcd_distances), 2) if nhcd_distances else 0
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
    bec_dist_0_2 = sum(1 for d in bec_distances if d <= 2)
    bec_dist_2_5 = sum(1 for d in bec_distances if 2 < d <= 5)
    bec_dist_5_10 = 0  # We only show up to 5km
    bec_dist_10_plus = 0
    
    nhcd_dist_0_2 = sum(1 for d in nhcd_distances if d <= 2)
    nhcd_dist_2_5 = sum(1 for d in nhcd_distances if 2 < d <= 5)
    nhcd_dist_5_10 = 0
    nhcd_dist_10_plus = 0
    
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
        'avg_bec_distance': avg_bec_distance,
        'avg_nhcd_distance': avg_nhcd_distance,
        'avg_bef_distance': avg_bef_distance,
        'avg_custom_schools_per_gov': avg_custom_per_gov,
        'distance_ranges': {
            '0-2km': dist_0_2,
            '2-5km': dist_2_5
        },
        'bec_distance_ranges': {
            '0-2km': bec_dist_0_2,
            '2-5km': bec_dist_2_5,
            '5-10km': bec_dist_5_10,
            '10+km': bec_dist_10_plus
        },
        'nhcd_distance_ranges': {
            '0-2km': nhcd_dist_0_2,
            '2-5km': nhcd_dist_2_5,
            '5-10km': nhcd_dist_5_10,
            '10+km': nhcd_dist_10_plus
        },
        'bef_distance_ranges': {
            '0-2km': bef_dist_0_2,
            '2-5km': bef_dist_2_5,
            '5-10km': bef_dist_5_10,
            '10+km': bef_dist_10_plus
        },
        'nearest_bec_count': len(bec_distances),
        'nearest_nhcd_count': len(nhcd_distances),
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
            json.dump({'results': results, 'summary': summary}, f)
        
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
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Summary sheet
        summary_data = {
            'Metric': [
                'Total Result Rows',
                'Total Government Schools',
                'Total Custom Schools Found (within 5km)',
                'Average Distance (km)',
                'Average Custom Schools per Government School'
            ],
            'Value': [
                summary['total_rows'],
                summary['total_gov_schools'],
                summary['total_custom_schools_found'],
                summary['avg_distance'],
                summary['avg_custom_schools_per_gov']
            ]
        }
        pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
        
        # Detailed results sheet - Government school first, then custom schools nearby
        detailed_data = []
        for r in results:
            row = {
                'Government_School_Name': r['gov_school_name'],
                'Government_BemisCode': r['gov_bemis_code'],
                'Government_District': r['gov_district'],
                'Government_Tehsil': r['gov_tehsil'],
                'Government_UC': r['gov_uc'],
                'Government_Level': r['gov_level'],
                'Government_Gender': r['gov_gender'],
                'Government_Enrollment': r['gov_enrollment'],
                'Government_Space_for_new_Rooms': r.get('gov_space_for_rooms', 'N/A'),
                'Government_Total_Rooms': r.get('gov_total_rooms', 'N/A'),
                'Government_Toilets': r.get('gov_toilets', 'N/A'),
                'Government_Boundary_Wall': r.get('gov_boundary_wall', 'N/A'),
                'Government_Drinking_Water': r.get('gov_drinking_water', 'N/A'),
                'Custom_School_Name': r['custom_school_name'],
                'Custom_BemisCode': r['custom_bemis_code'],
                'Custom_Source': r['custom_source'],
                'Custom_Division': r['custom_division'],
                'Custom_District': r['custom_district'],
                'Custom_Tehsil': r['custom_tehsil'],
                'Custom_Level': r['custom_level'],
                'Custom_Gender': r['custom_gender'],
                'Custom_Students': r['custom_students'],
                'Custom_Functional_Status': r['custom_functional_status'],
                'Distance_km': str(r['distance_km']) + ' km'
            }
            detailed_data.append(row)
        
        pd.DataFrame(detailed_data).to_excel(writer, sheet_name='Detailed Analysis', index=False)

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
                    'progress': session['progress'],
                    'total': session['total'],
                    'results': session['results'][-5:] if len(session['results']) > 0 else [],  # Last 5 results
                    'summary': session['summary'],
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
    """Get current session data"""
    if session_id in analysis_sessions:
        return jsonify(analysis_sessions[session_id])
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
        # First check if session is in memory
        if session_id in analysis_sessions:
            session = analysis_sessions[session_id]
            if session['status'] == 'completed':
                return jsonify({
                    'results': session['results'],
                    'summary': session['summary']
                })
        
        # Otherwise try to load from file
        results_path = os.path.join(app.config['DOWNLOAD_FOLDER'], f"results_{session_id}.json")
        with open(results_path, 'r') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['DOWNLOAD_FOLDER'], exist_ok=True)
    
    app.run(debug=True, port=5000)
