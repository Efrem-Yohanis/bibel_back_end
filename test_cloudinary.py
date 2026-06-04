import os
import sys
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bibel_project.settings')

import cloudinary
from cloudinary import api

cloudinary.config(
    cloud_name='dleykahqd',
    api_key='284571752959753',
    api_secret='B-tJyF7f1oBSt9qIulbGNvK8Hbg',
    secure=True
)

# Check all resources in the account
print("Listing ALL resources in account...")
result = api.resources(
    type='upload',
    max_results=100
)

print(f"Found {len(result.get('resources', []))} total resources")
if result.get('resources'):
    # Group by prefix
    prefixes = {}
    for res in result.get('resources', []):
        public_id = res['public_id']
        # Get the top-level folder
        parts = public_id.split('/')
        if len(parts) > 0:
            prefix = parts[0]
            if prefix not in prefixes:
                prefixes[prefix] = 0
            prefixes[prefix] += 1
    
    print("\nResources by top-level folder:")
    for prefix in sorted(prefixes.keys()):
        print(f"  - {prefix}: {prefixes[prefix]} files")
    
    print("\nFirst 10 resources:")
    for res in result.get('resources', [])[:10]:
        print(f"  - {res['public_id']} (type: {res.get('resource_type', 'unknown')})")
else:
    print("  No resources found in account!")
