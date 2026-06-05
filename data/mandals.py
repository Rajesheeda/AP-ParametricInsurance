# -*- coding: utf-8 -*-
"""
Kurnool District Mandals Geospatial Database
Provides coordinates, areas, zones, crop configurations, and APSDMA disaster vulnerability
for all 27 pilot mandals in Kurnool District, Andhra Pradesh.

Sources:
- Andhra Pradesh State Spatial Data Infrastructure (AP State GIS Portal)
- Andhra Pradesh State Disaster Management Authority (APSDMA) Vulnerability Atlas
"""

MANDALS = [
    {
        "mandal_id": "KNL_001",
        "mandal_name": "Adoni-1",
        "centroid_lat": 15.632,
        "centroid_lon": 77.275,
        "area_ha": 21450,
        "dominant_crop": "Cotton",
        "zone": "Western",
        "flood_prone": False,
        "drought_prone": True
    },
    {
        "mandal_id": "KNL_002",
        "mandal_name": "Adoni-2",
        "centroid_lat": 15.615,
        "centroid_lon": 77.291,
        "area_ha": 19800,
        "dominant_crop": "Cotton",
        "zone": "Western",
        "flood_prone": False,
        "drought_prone": True
    },
    {
        "mandal_id": "KNL_003",
        "mandal_name": "Alur",
        "centroid_lat": 15.385,
        "centroid_lon": 77.174,
        "area_ha": 31400,
        "dominant_crop": "Groundnut",
        "zone": "Western",
        "flood_prone": False,
        "drought_prone": True
    },
    {
        "mandal_id": "KNL_004",
        "mandal_name": "Aspari",
        "centroid_lat": 15.452,
        "centroid_lon": 77.284,
        "area_ha": 28650,
        "dominant_crop": "Groundnut",
        "zone": "Western",
        "flood_prone": False,
        "drought_prone": True
    },
    {
        "mandal_id": "KNL_005",
        "mandal_name": "C. Belagal",
        "centroid_lat": 15.903,
        "centroid_lon": 77.812,
        "area_ha": 18200,
        "dominant_crop": "Jowar",
        "zone": "Northern",
        "flood_prone": True,
        "drought_prone": False
    },
    {
        "mandal_id": "KNL_006",
        "mandal_name": "Chippagiri",
        "centroid_lat": 15.195,
        "centroid_lon": 77.241,
        "area_ha": 17400,
        "dominant_crop": "Groundnut",
        "zone": "Western",
        "flood_prone": False,
        "drought_prone": True
    },
    {
        "mandal_id": "KNL_007",
        "mandal_name": "Devanakonda",
        "centroid_lat": 15.541,
        "centroid_lon": 77.562,
        "area_ha": 26900,
        "dominant_crop": "Groundnut",
        "zone": "Southern",
        "flood_prone": False,
        "drought_prone": True
    },
    {
        "mandal_id": "KNL_008",
        "mandal_name": "Gonegandla",
        "centroid_lat": 15.702,
        "centroid_lon": 77.604,
        "area_ha": 24200,
        "dominant_crop": "Cotton",
        "zone": "Central",
        "flood_prone": False,
        "drought_prone": False
    },
    {
        "mandal_id": "KNL_009",
        "mandal_name": "Gudur",
        "centroid_lat": 15.864,
        "centroid_lon": 77.875,
        "area_ha": 21500,
        "dominant_crop": "Cotton",
        "zone": "Northern",
        "flood_prone": True,
        "drought_prone": False
    },
    {
        "mandal_id": "KNL_010",
        "mandal_name": "Halaharvi",
        "centroid_lat": 15.318,
        "centroid_lon": 77.026,
        "area_ha": 29800,
        "dominant_crop": "Groundnut",
        "zone": "Western",
        "flood_prone": False,
        "drought_prone": True
    },
    {
        "mandal_id": "KNL_011",
        "mandal_name": "Holagunda",
        "centroid_lat": 15.592,
        "centroid_lon": 77.031,
        "area_ha": 33100,
        "dominant_crop": "Sunflower",
        "zone": "Western",
        "flood_prone": False,
        "drought_prone": True
    },
    {
        "mandal_id": "KNL_012",
        "mandal_name": "Kallur",
        "centroid_lat": 15.814,
        "centroid_lon": 77.985,
        "area_ha": 20400,
        "dominant_crop": "Cotton",
        "zone": "Northern",
        "flood_prone": True,
        "drought_prone": False
    },
    {
        "mandal_id": "KNL_013",
        "mandal_name": "Kodumur",
        "centroid_lat": 15.689,
        "centroid_lon": 77.782,
        "area_ha": 35200,
        "dominant_crop": "Cotton",
        "zone": "Central",
        "flood_prone": False,
        "drought_prone": True
    },
    {
        "mandal_id": "KNL_014",
        "mandal_name": "Kosigi",
        "centroid_lat": 15.856,
        "centroid_lon": 77.248,
        "area_ha": 38400,
        "dominant_crop": "Jowar",
        "zone": "Western",
        "flood_prone": True,
        "drought_prone": False
    },
    {
        "mandal_id": "KNL_015",
        "mandal_name": "Kowthalam",
        "centroid_lat": 15.678,
        "centroid_lon": 77.168,
        "area_ha": 41200,
        "dominant_crop": "Sunflower",
        "zone": "Western",
        "flood_prone": True,
        "drought_prone": False
    },
    {
        "mandal_id": "KNL_016",
        "mandal_name": "Krishnagiri",
        "centroid_lat": 15.556,
        "centroid_lon": 77.828,
        "area_ha": 22300,
        "dominant_crop": "Redgram",
        "zone": "Central",
        "flood_prone": False,
        "drought_prone": True
    },
    {
        "mandal_id": "KNL_017",
        "mandal_name": "Kurnool Rural",
        "centroid_lat": 15.795,
        "centroid_lon": 78.054,
        "area_ha": 44300,
        "dominant_crop": "Cotton",
        "zone": "Northern",
        "flood_prone": True,
        "drought_prone": False
    },
    {
        "mandal_id": "KNL_018",
        "mandal_name": "Kurnool Urban",
        "centroid_lat": 15.828,
        "centroid_lon": 78.037,
        "area_ha": 12500,
        "dominant_crop": "Cotton",
        "zone": "Northern",
        "flood_prone": True,
        "drought_prone": False
    },
    {
        "mandal_id": "KNL_019",
        "mandal_name": "Maddikera",
        "centroid_lat": 15.261,
        "centroid_lon": 77.382,
        "area_ha": 16900,
        "dominant_crop": "Groundnut",
        "zone": "Southern",
        "flood_prone": False,
        "drought_prone": True
    },
    {
        "mandal_id": "KNL_020",
        "mandal_name": "Mantralayam",
        "centroid_lat": 15.942,
        "centroid_lon": 77.425,
        "area_ha": 25400,
        "dominant_crop": "Jowar",
        "zone": "Northern",
        "flood_prone": True,
        "drought_prone": False
    },
    {
        "mandal_id": "KNL_021",
        "mandal_name": "Nandavaram",
        "centroid_lat": 15.954,
        "centroid_lon": 77.576,
        "area_ha": 23100,
        "dominant_crop": "Jowar",
        "zone": "Northern",
        "flood_prone": True,
        "drought_prone": False
    },
    {
        "mandal_id": "KNL_022",
        "mandal_name": "Orvakal",
        "centroid_lat": 15.676,
        "centroid_lon": 78.134,
        "area_ha": 45800,
        "dominant_crop": "Redgram",
        "zone": "Eastern",
        "flood_prone": False,
        "drought_prone": True
    },
    {
        "mandal_id": "KNL_023",
        "mandal_name": "Pattikonda",
        "centroid_lat": 15.402,
        "centroid_lon": 77.421,
        "area_ha": 37200,
        "dominant_crop": "Groundnut",
        "zone": "Southern",
        "flood_prone": False,
        "drought_prone": True
    },
    {
        "mandal_id": "KNL_024",
        "mandal_name": "Pedda Kadubur",
        "centroid_lat": 15.748,
        "centroid_lon": 77.368,
        "area_ha": 20100,
        "dominant_crop": "Cotton",
        "zone": "Central",
        "flood_prone": False,
        "drought_prone": False
    },
    {
        "mandal_id": "KNL_025",
        "mandal_name": "Tuggali",
        "centroid_lat": 15.312,
        "centroid_lon": 77.581,
        "area_ha": 32900,
        "dominant_crop": "Groundnut",
        "zone": "Southern",
        "flood_prone": False,
        "drought_prone": True
    },
    {
        "mandal_id": "KNL_026",
        "mandal_name": "Veldurthy",
        "centroid_lat": 15.572,
        "centroid_lon": 77.944,
        "area_ha": 34100,
        "dominant_crop": "Redgram",
        "zone": "Central",
        "flood_prone": False,
        "drought_prone": True
    },
    {
        "mandal_id": "KNL_027",
        "mandal_name": "Yemmiganur",
        "centroid_lat": 15.768,
        "centroid_lon": 77.478,
        "area_ha": 27300,
        "dominant_crop": "Cotton",
        "zone": "Central",
        "flood_prone": False,
        "drought_prone": False
    }
]

def get_all_mandals():
    """
    Returns the complete list of Kurnool mandal dictionaries.
    
    Returns:
        list: List of dictionaries representing all 27 mandals.
    """
    return MANDALS

def get_mandal(mandal_id):
    """
    Retrieve metadata for a specific mandal in Kurnool district.

    Args:
        mandal_id (str): The unique ID of the mandal (e.g., 'KNL_001').

    Returns:
        dict: The dictionary containing the mandal metadata.

    Raises:
        ValueError: If the mandal_id does not exist.
    """
    for mandal in MANDALS:
        if mandal["mandal_id"] == mandal_id:
            return mandal
    raise ValueError(f"Mandal with ID '{mandal_id}' is not modeled or found in Kurnool district.")
