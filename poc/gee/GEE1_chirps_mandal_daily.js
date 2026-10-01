// GEE-1  CHIRPS daily rainfall, areal mean per POC mandal, 1995-01-01 onward.
// Paste into code.earthengine.google.com, set ASSETS, Run, then start the task in the Tasks tab.
// Output: Google Drive folder ap_poc / chirps_mandal_daily.csv  (columns: dist, mid, mandal, date, rain_mm)

var ASSETS = 'projects/YOUR_PROJECT/assets/';          // <-- change once
var mandals = ee.FeatureCollection(ASSETS + 'poc_mandals');

var chirps = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY')
  .filterDate('1995-01-01', '2026-10-01')
  .select('precipitation');

var table = chirps.map(function (img) {
  return img.reduceRegions({collection: mandals, reducer: ee.Reducer.mean().setOutputs(['rain_mm']), scale: 5566})
    .map(function (f) { return f.set('date', img.date().format('YYYY-MM-dd')).setGeometry(null); });
}).flatten();

Export.table.toDrive({
  collection: table, description: 'chirps_mandal_daily', folder: 'ap_poc',
  fileFormat: 'CSV', selectors: ['dist', 'mid', 'mandal', 'date', 'rain_mm']
});
