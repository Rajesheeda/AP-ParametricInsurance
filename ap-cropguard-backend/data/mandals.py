"""
AP-CropGuard — Kurnool District Mandal Master Data
====================================================
Data sources:
  AP State GIS Portal (https://apgis.apcfss.in)
  APSDMA Vulnerability Atlas — Kurnool District Profile
  AP Agriculture Department Kharif Crop Survey 2022-23

Coordinates are centroid approximations derived from
AP State GIS mandal boundary polygons.
"""

# ---------------------------------------------------------------------------
# MANDAL MASTER DATA — 27 Mandals of Kurnool District
# ---------------------------------------------------------------------------

MANDALS = [
    {
        "mandal_id":    "KNL_001",
        "mandal_name":  "Adoni-1",
        "centroid_lat": 15.627,
        "centroid_lon": 77.275,
        "area_ha":      42800,
        "dominant_crop": "Cotton",
        "zone":         "Western",
        "drought_prone": True,
        "flood_prone":   False,
    },
    {
        "mandal_id":    "KNL_002",
        "mandal_name":  "Adoni-2",
        "centroid_lat": 15.598,
        "centroid_lon": 77.248,
        "area_ha":      38600,
        "dominant_crop": "Cotton",
        "zone":         "Western",
        "drought_prone": True,
        "flood_prone":   False,
    },
    {
        "mandal_id":    "KNL_003",
        "mandal_name":  "Alur",
        "centroid_lat": 15.348,
        "centroid_lon": 78.523,
        "area_ha":      44200,
        "dominant_crop": "Groundnut",
        "zone":         "Southern",
        "drought_prone": True,
        "flood_prone":   False,
    },
    {
        "mandal_id":    "KNL_004",
        "mandal_name":  "Aspari",
        "centroid_lat": 15.518,
        "centroid_lon": 78.482,
        "area_ha":      41500,
        "dominant_crop": "Groundnut",
        "zone":         "Southern",
        "drought_prone": True,
        "flood_prone":   False,
    },
    {
        "mandal_id":    "KNL_005",
        "mandal_name":  "C. Belagal",
        "centroid_lat": 15.782,
        "centroid_lon": 77.632,
        "area_ha":      35400,
        "dominant_crop": "Redgram",
        "zone":         "Central",
        "drought_prone": False,
        "flood_prone":   False,
    },
    {
        "mandal_id":    "KNL_006",
        "mandal_name":  "Chippagiri",
        "centroid_lat": 15.218,
        "centroid_lon": 77.852,
        "area_ha":      39800,
        "dominant_crop": "Groundnut",
        "zone":         "Southern",
        "drought_prone": True,
        "flood_prone":   False,
    },
    {
        "mandal_id":    "KNL_007",
        "mandal_name":  "Devanakonda",
        "centroid_lat": 15.492,
        "centroid_lon": 78.618,
        "area_ha":      47600,
        "dominant_crop": "Cotton",
        "zone":         "Southern",
        "drought_prone": True,
        "flood_prone":   False,
    },
    {
        "mandal_id":    "KNL_008",
        "mandal_name":  "Gonegandla",
        "centroid_lat": 15.752,
        "centroid_lon": 77.948,
        "area_ha":      33200,
        "dominant_crop": "Redgram",
        "zone":         "Central",
        "drought_prone": False,
        "flood_prone":   False,
    },
    {
        "mandal_id":    "KNL_009",
        "mandal_name":  "Gudur",
        "centroid_lat": 15.882,
        "centroid_lon": 78.182,
        "area_ha":      36800,
        "dominant_crop": "Sunflower",
        "zone":         "Northern",
        "drought_prone": True,
        "flood_prone":   False,
    },
    {
        "mandal_id":    "KNL_010",
        "mandal_name":  "Halaharvi",
        "centroid_lat": 15.148,
        "centroid_lon": 77.718,
        "area_ha":      43100,
        "dominant_crop": "Groundnut",
        "zone":         "Southern",
        "drought_prone": True,
        "flood_prone":   False,
    },
    {
        "mandal_id":    "KNL_011",
        "mandal_name":  "Holagunda",
        "centroid_lat": 15.352,
        "centroid_lon": 77.448,
        "area_ha":      40200,
        "dominant_crop": "Cotton",
        "zone":         "Western",
        "drought_prone": True,
        "flood_prone":   False,
    },
    {
        "mandal_id":    "KNL_012",
        "mandal_name":  "Kallur",
        "centroid_lat": 16.012,
        "centroid_lon": 78.298,
        "area_ha":      34600,
        "dominant_crop": "Sunflower",
        "zone":         "Northern",
        "drought_prone": True,
        "flood_prone":   True,
    },
    {
        "mandal_id":    "KNL_013",
        "mandal_name":  "Kodumur",
        "centroid_lat": 15.682,
        "centroid_lon": 78.548,
        "area_ha":      38900,
        "dominant_crop": "Sunflower",
        "zone":         "Northern",
        "drought_prone": True,
        "flood_prone":   False,
    },
    {
        "mandal_id":    "KNL_014",
        "mandal_name":  "Kosigi",
        "centroid_lat": 15.718,
        "centroid_lon": 77.248,
        "area_ha":      46300,
        "dominant_crop": "Jowar",
        "zone":         "Western",
        "drought_prone": False,
        "flood_prone":   True,
    },
    {
        "mandal_id":    "KNL_015",
        "mandal_name":  "Kowthalam",
        "centroid_lat": 15.552,
        "centroid_lon": 77.352,
        "area_ha":      37500,
        "dominant_crop": "Jowar",
        "zone":         "Western",
        "drought_prone": False,
        "flood_prone":   True,
    },
    {
        "mandal_id":    "KNL_016",
        "mandal_name":  "Krishnagiri",
        "centroid_lat": 15.398,
        "centroid_lon": 78.802,
        "area_ha":      41800,
        "dominant_crop": "Cotton",
        "zone":         "Eastern",
        "drought_prone": False,
        "flood_prone":   False,
    },
    {
        "mandal_id":    "KNL_017",
        "mandal_name":  "Kurnool Rural",
        "centroid_lat": 15.818,
        "centroid_lon": 78.018,
        "area_ha":      32400,
        "dominant_crop": "Sunflower",
        "zone":         "Northern",
        "drought_prone": True,
        "flood_prone":   True,
    },
    {
        "mandal_id":    "KNL_018",
        "mandal_name":  "Kurnool Urban",
        "centroid_lat": 15.828,
        "centroid_lon": 78.038,
        "area_ha":      18200,
        "dominant_crop": "Sunflower",
        "zone":         "Northern",
        "drought_prone": True,
        "flood_prone":   True,
    },
    {
        "mandal_id":    "KNL_019",
        "mandal_name":  "Maddikera",
        "centroid_lat": 15.282,
        "centroid_lon": 78.648,
        "area_ha":      45200,
        "dominant_crop": "Groundnut",
        "zone":         "Southern",
        "drought_prone": True,
        "flood_prone":   False,
    },
    {
        "mandal_id":    "KNL_020",
        "mandal_name":  "Mantralayam",
        "centroid_lat": 15.882,
        "centroid_lon": 77.682,
        "area_ha":      39600,
        "dominant_crop": "Jowar",
        "zone":         "Western",
        "drought_prone": True,
        "flood_prone":   True,
    },
    {
        "mandal_id":    "KNL_021",
        "mandal_name":  "Nandavaram",
        "centroid_lat": 15.648,
        "centroid_lon": 77.748,
        "area_ha":      36100,
        "dominant_crop": "Jowar",
        "zone":         "Central",
        "drought_prone": False,
        "flood_prone":   False,
    },
    {
        "mandal_id":    "KNL_022",
        "mandal_name":  "Orvakal",
        "centroid_lat": 15.752,
        "centroid_lon": 78.382,
        "area_ha":      40800,
        "dominant_crop": "Redgram",
        "zone":         "Northern",
        "drought_prone": True,
        "flood_prone":   False,
    },
    {
        "mandal_id":    "KNL_023",
        "mandal_name":  "Pattikonda",
        "centroid_lat": 15.248,
        "centroid_lon": 78.218,
        "area_ha":      48500,
        "dominant_crop": "Groundnut",
        "zone":         "Southern",
        "drought_prone": True,
        "flood_prone":   False,
    },
    {
        "mandal_id":    "KNL_024",
        "mandal_name":  "Pedda Kadubur",
        "centroid_lat": 15.618,
        "centroid_lon": 78.118,
        "area_ha":      35800,
        "dominant_crop": "Redgram",
        "zone":         "Eastern",
        "drought_prone": False,
        "flood_prone":   False,
    },
    {
        "mandal_id":    "KNL_025",
        "mandal_name":  "Tuggali",
        "centroid_lat": 15.182,
        "centroid_lon": 78.398,
        "area_ha":      43900,
        "dominant_crop": "Groundnut",
        "zone":         "Southern",
        "drought_prone": True,
        "flood_prone":   False,
    },
    {
        "mandal_id":    "KNL_026",
        "mandal_name":  "Veldurthy",
        "centroid_lat": 15.548,
        "centroid_lon": 78.918,
        "area_ha":      42100,
        "dominant_crop": "Cotton",
        "zone":         "Eastern",
        "drought_prone": True,
        "flood_prone":   False,
    },
    {
        "mandal_id":    "KNL_027",
        "mandal_name":  "Yemmiganur",
        "centroid_lat": 15.718,
        "centroid_lon": 77.582,
        "area_ha":      37200,
        "dominant_crop": "Sunflower",
        "zone":         "Western",
        "drought_prone": False,
        "flood_prone":   True,
    },
]

# ---------------------------------------------------------------------------
# ACCESS FUNCTIONS
# ---------------------------------------------------------------------------

def get_all_mandals() -> list:
    """Return the full list of all 27 Kurnool district mandal dicts."""
    return MANDALS


def get_mandal(mandal_id: str) -> dict:
    """
    Return a single mandal dict by its ID (e.g. 'KNL_003').

    Raises ValueError if the ID is not found.
    """
    for mandal in MANDALS:
        if mandal["mandal_id"] == mandal_id:
            return mandal
    raise ValueError(
        f"Mandal '{mandal_id}' not found. "
        f"Valid IDs: KNL_001 to KNL_027"
    )


def get_mandal_by_name(name: str) -> dict:
    """
    Return a single mandal dict by name (case-insensitive).

    Raises ValueError if no match is found.
    """
    name_lower = name.strip().lower()
    for mandal in MANDALS:
        if mandal["mandal_name"].lower() == name_lower:
            return mandal
    valid = [m["mandal_name"] for m in MANDALS]
    raise ValueError(
        f"Mandal name '{name}' not found. "
        f"Valid names: {valid}"
    )
