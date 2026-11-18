// GEE-3  Sentinel-1 flood mapping per event (change detection, orbit-matched).
// Method: UN-SPIDER Recommended Practice (S1 flood mapping in GEE), with the fixed 1.25 ratio threshold
// replaced by Otsu thresholds computed per event (Twele et al. 2016, DLR S1 flood service):
//   1. VH, IW, same relative orbit + pass for pre and post; focal-median speckle filter (50 m).
//   2. diff = post_dB - pre_dB. Flooded if diff < Otsu(diff) AND post_dB < Otsu(post_dB).
//   3. Exclude permanent water (JRC GSW seasonality >= 10 months), HAND > 15 m (MERIT Hydro, Twele 2016),
//      and connected clusters < 8 pixels.
//   4. Crop damage area = flooded AND ESA WorldCover cropland (class 40); YSR parcels: flooded fraction per parcel.
// Outputs (Drive folder ap_poc): flood_mandal_<id>.csv, flood_parcel_ysr_<id>.csv, flood_map_<id>.tif
// Each CSV row carries post_image_time, so the 72-hour window can be checked.

var ASSETS = 'projects/YOUR_PROJECT/assets/';          // <-- change once
var mandals = ee.FeatureCollection(ASSETS + 'poc_mandals');
var parcels = ee.FeatureCollection(ASSETS + 'ysr_parcels');

// Filled from poc/data/derived/event_catalogue_*.csv (extreme_rain / unseasonal_rain / cyclone).
// dists: department district codes to process for that event.
var EVENTS = [
  {"id": "10_20201124_NIVAR", "start": "2020-11-24", "end": "2020-11-28", "dists": ["10"]},
  {"id": "10_20211111_UNNAMED", "start": "2021-11-11", "end": "2021-11-11", "dists": ["10"]},
  {"id": "10_20221208_MANDOUS", "start": "2022-12-08", "end": "2022-12-12", "dists": ["10"]},
  {"id": "10_20231202_MICHAUNG", "start": "2023-12-02", "end": "2023-12-06", "dists": ["10"]},
  {"id": "10_20240601", "start": "2024-06-01", "end": "2024-06-07", "dists": ["10"]},
  {"id": "11_20200924", "start": "2020-09-24", "end": "2020-09-28", "dists": ["11"]},
  {"id": "11_20201124", "start": "2020-11-24", "end": "2020-11-28", "dists": ["11"]},
  {"id": "11_20231205_MICHAUNG", "start": "2023-12-05", "end": "2023-12-05", "dists": ["11"]},
  {"id": "14_20210925_GULAB", "start": "2021-09-25", "end": "2021-09-29", "dists": ["14"]},
  {"id": "14_20220805", "start": "2022-08-05", "end": "2022-08-09", "dists": ["14"]},
  {"id": "14_20240907", "start": "2024-09-07", "end": "2024-09-11", "dists": ["14"]},
  {"id": "14_20250816", "start": "2025-08-16", "end": "2025-08-19", "dists": ["14"]},
  {"id": "14_20260702", "start": "2026-07-02", "end": "2026-07-07", "dists": ["14"]},
  {"id": "14_20260909", "start": "2026-09-09", "end": "2026-09-13", "dists": ["14"]},
  {"id": "14_20260920_UNNAMED", "start": "2026-09-20", "end": "2026-09-26", "dists": ["14"]},
  {"id": "22_20200911", "start": "2020-09-11", "end": "2020-09-15", "dists": ["22"]},
  {"id": "22_20210720", "start": "2021-07-20", "end": "2021-07-24", "dists": ["22"]},
  {"id": "22_20220511_ASANI", "start": "2022-05-11", "end": "2022-05-11", "dists": ["22"]},
  {"id": "22_20230718", "start": "2023-07-18", "end": "2023-07-28", "dists": ["22"]},
  {"id": "22_20231203_MICHAUNG", "start": "2023-12-03", "end": "2023-12-07", "dists": ["22"]},
  {"id": "22_20240829", "start": "2024-08-29", "end": "2024-09-03", "dists": ["22"]},
  {"id": "22_20251028_MONTHA", "start": "2025-10-28", "end": "2025-10-29", "dists": ["22"]}
];

var jrc = ee.Image('JRC/GSW1_4/GlobalSurfaceWater').select('seasonality');
var merit = ee.Image('MERIT/Hydro/v1_0_1').select('hnd');
var cropland = ee.ImageCollection('ESA/WorldCover/v200').first().eq(40);

function otsu(histogram) {
  histogram = ee.Dictionary(histogram);
  var counts = ee.Array(histogram.get('histogram'));
  var means = ee.Array(histogram.get('bucketMeans'));
  var size = means.length().get([0]);
  var total = counts.reduce(ee.Reducer.sum(), [0]).get([0]);
  var sum = means.multiply(counts).reduce(ee.Reducer.sum(), [0]).get([0]);
  var mean = sum.divide(total);
  var indices = ee.List.sequence(1, size);
  var bss = indices.map(function (i) {
    var aCounts = counts.slice(0, 0, i);
    var aCount = aCounts.reduce(ee.Reducer.sum(), [0]).get([0]);
    var aMeans = means.slice(0, 0, i);
    var aMean = aMeans.multiply(aCounts).reduce(ee.Reducer.sum(), [0]).get([0]).divide(aCount);
    var bCount = total.subtract(aCount);
    var bMean = sum.subtract(aCount.multiply(aMean)).divide(bCount);
    return aCount.multiply(aMean.subtract(mean).pow(2)).add(bCount.multiply(bMean.subtract(mean).pow(2)));
  });
  return means.sort(bss).get([-1]);
}

function s1col(region, start, end) {
  return ee.ImageCollection('COPERNICUS/S1_GRD').filterBounds(region).filterDate(start, end)
    .filter(ee.Filter.eq('instrumentMode', 'IW'))
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
    .select('VH');
}

EVENTS.forEach(function (ev) {
  var aoiFc = mandals.filter(ee.Filter.inList('dist', ev.dists));
  var aoi = aoiFc.geometry();
  var start = ee.Date(ev.start), end = ee.Date(ev.end);

  // first acquisition after the event ends defines orbit + pass
  var postAll = s1col(aoi, end, end.advance(12, 'day')).sort('system:time_start');
  var first = ee.Image(postAll.first());
  var orbit = first.get('relativeOrbitNumber_start');
  var pass = first.get('orbitProperties_pass');
  var postDay = ee.Date(first.get('system:time_start'));
  var post = postAll.filter(ee.Filter.eq('relativeOrbitNumber_start', orbit))
    .filterDate(postDay, postDay.advance(1, 'day')).mosaic().focalMedian(50, 'circle', 'meters');
  var pre = s1col(aoi, start.advance(-36, 'day'), start)
    .filter(ee.Filter.eq('relativeOrbitNumber_start', orbit))
    .filter(ee.Filter.eq('orbitProperties_pass', pass))
    .median().focalMedian(50, 'circle', 'meters');

  var diff = post.subtract(pre).rename('diff');
  var sample = ee.Image.cat([diff, post.rename('post')]).updateMask(cropland);
  var hDiff = sample.select('diff').reduceRegion({reducer: ee.Reducer.histogram(255, 0.1), geometry: aoi, scale: 30, maxPixels: 1e10, bestEffort: true}).get('diff');
  var hPost = sample.select('post').reduceRegion({reducer: ee.Reducer.histogram(255, 0.1), geometry: aoi, scale: 30, maxPixels: 1e10, bestEffort: true}).get('post');
  var tDiff = otsu(hDiff), tPost = otsu(hPost);

  var flood = diff.lt(ee.Number(tDiff)).and(post.lt(ee.Number(tPost)))
    .updateMask(jrc.unmask(0).lt(10))
    .updateMask(merit.lte(15))
    .selfMask();
  flood = flood.updateMask(flood.connectedPixelCount(8, true).gte(8)).rename('flood');
  var cropFlood = flood.and(cropland).unmask(0).rename('crop_flood');

  var meta = {event_id: ev.id, event_start: ev.start, event_end: ev.end,
    post_image_time: postDay.format('YYYY-MM-dd HH:mm'),
    hours_after_event_end: postDay.difference(end, 'hour'),
    orbit: orbit, pass: pass, t_diff_db: tDiff, t_post_db: tPost};

  var areaImg = ee.Image.cat([cropFlood.multiply(ee.Image.pixelArea()).divide(1e4).rename('crop_flood_ha'),
                              cropland.unmask(0).multiply(ee.Image.pixelArea()).divide(1e4).rename('cropland_ha')]);
  var byMandal = areaImg.reduceRegions({collection: aoiFc.select(['dist', 'mid', 'mandal']), reducer: ee.Reducer.sum(), scale: 10, tileScale: 8})
    .map(function (f) { return f.set(meta).setGeometry(null); });
  Export.table.toDrive({collection: byMandal, description: 'flood_mandal_' + ev.id, folder: 'ap_poc', fileFormat: 'CSV',
    selectors: ['event_id', 'dist', 'mid', 'mandal', 'crop_flood_ha', 'cropland_ha', 'post_image_time', 'hours_after_event_end', 'orbit', 'pass', 't_diff_db', 't_post_db']});

  if (ev.dists.indexOf('11') >= 0) {
    var byParcel = flood.unmask(0).rename('flood_frac').reduceRegions({collection: parcels.select(['pid']), reducer: ee.Reducer.mean(), scale: 10, tileScale: 8})
      .map(function (f) { return f.set('event_id', ev.id).setGeometry(null); });
    Export.table.toDrive({collection: byParcel, description: 'flood_parcel_ysr_' + ev.id, folder: 'ap_poc', fileFormat: 'CSV',
      selectors: ['event_id', 'pid', 'flood_frac']});
  }

  Export.image.toDrive({image: cropFlood.toByte(), description: 'flood_map_' + ev.id, folder: 'ap_poc',
    region: aoi.bounds(), scale: 20, maxPixels: 1e10});
});
