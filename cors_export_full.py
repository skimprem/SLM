"""
CORS Data Export Script - Complete Data Dump
Exports all available CORS station data from SLM API to CSV and JSON
with English headers and comprehensive information

Usage: python cors_export_full.py [remote_host] [--format csv|json|both]
Example:
    python cors_export_full.py http://192.168.8.252
    python cors_export_full.py http://192.168.8.252 --format csv
"""

import requests
import json
import csv
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys
import argparse
from urllib.parse import urljoin

class CORSDataExporter:
    """Export complete CORS station data from SLM public API"""
    
    def __init__(self, api_base_url: str = "http://localhost"):
        self.api_base_url = api_base_url.rstrip('/')
        self.api_endpoint = f"{self.api_base_url}/api/public/stations/"
        self.stations = []
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    def fetch_all_stations(self) -> bool:
        """Fetch all stations with pagination"""
        try:
            print(f"\n📡 Connecting to API: {self.api_endpoint}")
            
            # Fetch first page to get total count
            response = requests.get(self.api_endpoint, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            self.stations = data.get('data', [])
            total = data.get('recordsTotal', 0)
            filtered = data.get('recordsFiltered', 0)
            
            print(f"✓ Page 1: Fetched {len(self.stations)} stations")
            print(f"  Total in database: {total} | Filtered: {filtered}")
            
            # Fetch remaining pages
            page = 2
            next_url = data.get('next')
            while next_url:
                print(f"  Loading page {page}...")
                response = requests.get(next_url, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                page_data = data.get('data', [])
                self.stations.extend(page_data)
                print(f"✓ Page {page}: Fetched {len(page_data)} stations (Total: {len(self.stations)})")
                
                next_url = data.get('next')
                page += 1
            
            print(f"\n✓ Successfully downloaded {len(self.stations)} total stations")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"✗ API connection error: {e}")
            return False
    
    def flatten_station_data(self, station: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten nested station data for CSV export"""
        
        # Extract nested structures
        llh = station.get('llh', [None, None, None])
        xyz = station.get('xyz', [None, None, None])
        agencies = station.get('agencies', [])
        networks = station.get('networks', [])
        
        # Format dates
        last_publish = station.get('last_publish', '')
        if last_publish:
            try:
                dt = datetime.fromisoformat(last_publish.replace('Z', '+00:00'))
                last_publish = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                last_publish = last_publish[:10] if last_publish else ''
        
        last_rinex2 = station.get('last_rinex2', '')
        if last_rinex2:
            try:
                dt = datetime.fromisoformat(last_rinex2.replace('Z', '+00:00'))
                last_rinex2 = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass
        
        last_rinex3 = station.get('last_rinex3', '')
        if last_rinex3:
            try:
                dt = datetime.fromisoformat(last_rinex3.replace('Z', '+00:00'))
                last_rinex3 = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass
        
        last_rinex4 = station.get('last_rinex4', '')
        if last_rinex4:
            try:
                dt = datetime.fromisoformat(last_rinex4.replace('Z', '+00:00'))
                last_rinex4 = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass
        
        last_data_time = station.get('last_data_time', '')
        if last_data_time:
            try:
                dt = datetime.fromisoformat(last_data_time.replace('Z', '+00:00'))
                last_data_time = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass
        
        return {
            'station_name': station.get('name', ''),
            'status': self._get_status_name(station.get('status', 0)),
            'domes_number': station.get('domes_number', ''),
            'city': station.get('city', ''),
            'state': station.get('state', ''),
            'country': station.get('country', ''),
            
            # Coordinates
            'latitude': f"{llh[0]:.8f}" if llh[0] is not None else '',
            'longitude': f"{llh[1]:.8f}" if llh[1] is not None else '',
            'height_m': f"{llh[2]:.3f}" if llh[2] is not None else '',
            
            # Cartesian coordinates
            'x_meters': f"{xyz[0]:.3f}" if xyz[0] is not None else '',
            'y_meters': f"{xyz[1]:.3f}" if xyz[1] is not None else '',
            'z_meters': f"{xyz[2]:.3f}" if xyz[2] is not None else '',
            
            # Antenna information
            'antenna_type': station.get('antenna_type', ''),
            'antenna_serial_number': station.get('antenna_serial_number', ''),
            'antenna_marker_UNE_north': station.get('antenna_marker_une', [0, 0, 0])[0] if station.get('antenna_marker_une') else '',
            'antenna_marker_UNE_east': station.get('antenna_marker_une', [0, 0, 0])[1] if station.get('antenna_marker_une') else '',
            'antenna_marker_UNE_up': station.get('antenna_marker_une', [0, 0, 0])[2] if station.get('antenna_marker_une') else '',
            'antenna_calibration': station.get('antcal', ''),
            
            # Radome information
            'radome_type': station.get('radome_type', ''),
            
            # Receiver information
            'receiver_type': station.get('receiver_type', ''),
            'receiver_serial_number': station.get('serial_number', ''),
            'receiver_firmware': station.get('firmware', ''),
            
            # Frequency standard
            'frequency_standard': station.get('frequency_standard', ''),
            
            # Satellite systems
            'satellite_systems': '|'.join(station.get('satellite_system', [])),
            
            # Tide gauges
            'tide_gauges': '|'.join([str(tg) for tg in station.get('tide_gauges', [])]),
            
            # Data center
            'data_center': station.get('data_center', ''),
            
            # Data availability
            'last_rinex2': last_rinex2,
            'last_rinex3': last_rinex3,
            'last_rinex4': last_rinex4,
            'last_data_time': last_data_time,
            'last_data': station.get('last_data', ''),
            
            # Timestamps
            'join_date': station.get('join_date', ''),
            'last_publish': last_publish,
            
            # Agencies and networks (as pipe-separated values)
            'agencies': '|'.join([f"{a.get('short_name', a.get('name', ''))} ({a.get('country', '')})" for a in agencies]),
            'networks': '|'.join([n.get('name', '') for n in networks]),
        }
    
    def _get_status_name(self, status_code: int) -> str:
        """Map status code to name"""
        status_map = {
            1: "PROPOSED",
            2: "UPDATED",
            3: "PUBLISHED",
            4: "PUBLISHED",
        }
        return status_map.get(status_code, f"STATUS_{status_code}")
    
    def export_csv(self) -> Optional[str]:
        """Export all data to CSV with English headers"""
        if not self.stations:
            print("⚠ No data to export")
            return None
        
        filename = f"cors_stations_complete_{self.timestamp}.csv"
        
        # Flatten data
        flat_data = [self.flatten_station_data(s) for s in self.stations]
        
        if not flat_data:
            print("✗ Error: No data to export")
            return None
        
        # Get fieldnames from first record
        fieldnames = flat_data[0].keys()
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(flat_data)
        
        file_size_mb = __import__('os').path.getsize(filename) / (1024 * 1024)
        print(f"✓ CSV exported: {filename}")
        print(f"  Records: {len(flat_data)}")
        print(f"  Columns: {len(fieldnames)}")
        print(f"  Size: {file_size_mb:.2f} MB")
        
        return filename
    
    def export_json(self) -> Optional[str]:
        """Export all data to JSON with English keys"""
        if not self.stations:
            print("⚠ No data to export")
            return None
        
        filename = f"cors_stations_complete_{self.timestamp}.json"
        
        # Map all station data with English keys
        json_data = {
            'metadata': {
                'export_time': datetime.now().isoformat(),
                'source': self.api_endpoint,
                'total_stations': len(self.stations),
                'api_version': '1.0',
            },
            'stations': []
        }
        
        for station in self.stations:
            llh = station.get('llh', [None, None, None])
            xyz = station.get('xyz', [None, None, None])
            agencies = station.get('agencies', [])
            networks = station.get('networks', [])
            
            station_data = {
                'station': {
                    'name': station.get('name'),
                    'status': self._get_status_name(station.get('status', 0)),
                    'domes_number': station.get('domes_number'),
                    'join_date': station.get('join_date'),
                    'last_publish': station.get('last_publish'),
                },
                'location': {
                    'city': station.get('city'),
                    'state': station.get('state'),
                    'country': station.get('country'),
                    'coordinates': {
                        'latitude': llh[0],
                        'longitude': llh[1],
                        'height_meters': llh[2],
                    },
                    'cartesian': {
                        'x_meters': xyz[0],
                        'y_meters': xyz[1],
                        'z_meters': xyz[2],
                    }
                },
                'antenna': {
                    'type': station.get('antenna_type'),
                    'serial_number': station.get('antenna_serial_number'),
                    'marker_UNE': {
                        'north': station.get('antenna_marker_une', [0, 0, 0])[0] if station.get('antenna_marker_une') else None,
                        'east': station.get('antenna_marker_une', [0, 0, 0])[1] if station.get('antenna_marker_une') else None,
                        'up': station.get('antenna_marker_une', [0, 0, 0])[2] if station.get('antenna_marker_une') else None,
                    },
                    'calibration': station.get('antcal'),
                },
                'radome': {
                    'type': station.get('radome_type'),
                },
                'receiver': {
                    'type': station.get('receiver_type'),
                    'serial_number': station.get('serial_number'),
                    'firmware': station.get('firmware'),
                },
                'frequency_standard': station.get('frequency_standard'),
                'satellite_systems': station.get('satellite_system', []),
                'tide_gauges': station.get('tide_gauges', []),
                'data_center': station.get('data_center'),
                'data_availability': {
                    'last_rinex2': station.get('last_rinex2'),
                    'last_rinex3': station.get('last_rinex3'),
                    'last_rinex4': station.get('last_rinex4'),
                    'last_data_time': station.get('last_data_time'),
                    'last_data': station.get('last_data'),
                },
                'organizations': {
                    'agencies': agencies,
                    'networks': networks,
                }
            }
            json_data['stations'].append(station_data)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        file_size_mb = __import__('os').path.getsize(filename) / (1024 * 1024)
        print(f"✓ JSON exported: {filename}")
        print(f"  Records: {len(self.stations)}")
        print(f"  Size: {file_size_mb:.2f} MB")
        
        return filename
    
    def print_summary(self):
        """Print data summary"""
        if not self.stations:
            return
        
        print(f"\n{'='*80}")
        print("📊 DATA SUMMARY")
        print(f"{'='*80}\n")
        
        # Status distribution
        status_count = {}
        for station in self.stations:
            status = self._get_status_name(station.get('status', 0))
            status_count[status] = status_count.get(status, 0) + 1
        
        print("Status Distribution:")
        for status, count in sorted(status_count.items()):
            percent = count * 100 // len(self.stations) if self.stations else 0
            print(f"  {status:12} : {count:3} stations ({percent:2}%)")
        
        # Country distribution
        country_count = {}
        for station in self.stations:
            country = station.get('country', 'UNKNOWN')
            country_count[country] = country_count.get(country, 0) + 1
        
        print(f"\nTop 15 Countries (by station count):")
        for i, (country, count) in enumerate(
            sorted(country_count.items(), key=lambda x: x[1], reverse=True)[:15], 1
        ):
            print(f"  {i:2}. {country:3} : {count:3} stations")
        
        # Equipment statistics
        antenna_types = {}
        receiver_types = {}
        
        for station in self.stations:
            ant = station.get('antenna_type', 'Unknown')
            antenna_types[ant] = antenna_types.get(ant, 0) + 1
            
            rec = station.get('receiver_type', 'Unknown')
            receiver_types[rec] = receiver_types.get(rec, 0) + 1
        
        print(f"\nTop 5 Antenna Types:")
        for i, (ant, count) in enumerate(
            sorted(antenna_types.items(), key=lambda x: x[1], reverse=True)[:5], 1
        ):
            print(f"  {i}. {ant[:40]:40} : {count:3} stations")
        
        print(f"\nTop 5 Receiver Types:")
        for i, (rec, count) in enumerate(
            sorted(receiver_types.items(), key=lambda x: x[1], reverse=True)[:5], 1
        ):
            print(f"  {i}. {rec[:40]:40} : {count:3} stations")
        
        print(f"\n{'='*80}\n")

def main():
    parser = argparse.ArgumentParser(
        description='Complete CORS Data Export - Full dump from SLM API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cors_export_full.py http://192.168.8.252
  python cors_export_full.py http://192.168.8.252 --format csv
  python cors_export_full.py http://192.168.8.252 --format json
  python cors_export_full.py http://192.168.8.252 --format both
        """
    )
    
    parser.add_argument('api_url', nargs='?', default='http://localhost',
                       help='SLM server URL (default: http://localhost)')
    parser.add_argument('--format', choices=['csv', 'json', 'both'], default='both',
                       help='Export format (default: both)')
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("🌍 CORS COMPLETE DATA EXPORT - FULL DUMP FROM SLM API")
    print("="*80)
    
    # Initialize exporter
    exporter = CORSDataExporter(args.api_url)
    
    # Fetch all data
    if not exporter.fetch_all_stations():
        sys.exit(1)
    
    # Print summary
    exporter.print_summary()
    
    # Export based on format
    files = []
    if args.format in ['csv', 'both']:
        f = exporter.export_csv()
        if f:
            files.append(f)
    
    if args.format in ['json', 'both']:
        f = exporter.export_json()
        if f:
            files.append(f)
    
    if files:
        print("\n✓ Export completed successfully!")
        print(f"Files created: {len(files)}")
        for f in files:
            print(f"  • {f}")
    else:
        print("\n✗ Export failed")
        sys.exit(1)
    
    print()

if __name__ == '__main__':
    main()
