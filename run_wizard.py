import urllib.request
import json
import webbrowser
import os
import subprocess
import time

API_BASE = "https://tasking-manager-api.hotosm.org/api/v2/projects/"
GEOFABRIK_INDEX = "https://download.geofabrik.de/index-v1.json"

print("========================================")
print(" Welcome to OSM QA Buddy (Local Mode)")
print("========================================\n")
project_id = input("Enter the HOT TM Project ID (e.g., 14111): ").strip()

print(f"\n[*] Fetching Project #{project_id} data from HOT TM API...")
try:
    # 1. Fetch AOI
    aoi_req = urllib.request.urlopen(f"{API_BASE}{project_id}/queries/aoi/")
    aoi_data = aoi_req.read().decode('utf-8')
    with open("project_aoi.geojson", "w") as f:
        f.write(aoi_data)

    # 2. Fetch Tasks
    tasks_req = urllib.request.urlopen(f"{API_BASE}{project_id}/tasks/")
    tasks_data = tasks_req.read().decode('utf-8')
    with open("project_tasks.geojson", "w") as f:
        f.write(tasks_data)

    # 3. Fetch Country Name for Geofabrik Routing
    info_req = urllib.request.urlopen(f"{API_BASE}{project_id}/")
    info_data = json.loads(info_req.read().decode('utf-8'))
    country_tags = info_data.get("countryTag", [])
    
    geofabrik_url = "https://download.geofabrik.de/"
    if country_tags:
        country_name = country_tags[0].lower().replace(" ", "-")
        # Check Geofabrik Index
        gf_req = urllib.request.urlopen(GEOFABRIK_INDEX)
        gf_index = json.loads(gf_req.read().decode('utf-8'))
        for feature in gf_index.get("features", []):
            props = feature.get("properties", {})
            if props.get("name", "").lower().replace(" ", "-") == country_name:
                geofabrik_url = props.get("urls", {}).get("html", geofabrik_url)
                break

    print(f"[+] AOI and Tasks downloaded successfully.")
    print(f"[*] Opening Geofabrik for region: {country_tags[0] if country_tags else 'Global'}...")
    time.sleep(2)
    webbrowser.open(geofabrik_url)

    print("\n========================================")
    print(" ACTION REQUIRED:")
    print(" 1. Download the .osm.pbf file from the webpage that just opened.")
    print(f" 2. Move the .pbf file into this exact folder: {os.getcwd()}")
    print("========================================")
    input("Press ENTER when the .pbf file is in the folder...")

    # 4. Trigger Docker
    print("\n[*] Booting up Docker QA Pipeline...")
    subprocess.run([
        "docker", "run", "--rm",
        "-v", f"{os.getcwd()}:/data",
        "qabot"
    ])

except Exception as e:
    print(f"\n[!] Error: {e}")
    input("Press Enter to exit.")