// GEE-2  Kharif season time series: Sentinel-2 NDVI + Sentinel-1 VH/VV, 10-day windows.
//   (a) every matched YSR parcel     -> ts_parcels_ysr_<year>.csv
//   (b) cropland of every POC mandal -> ts_mandals_<year>.csv
// Cloud masking: S2 Cloud Probability (s2cloudless) < 40 AND SCL not in {3 shadow, 8/9 cloud, 10 cirrus}.
// Cropland mask for mandals: ESA WorldCover v200 class 40.
// SAR: S1 GRD IW, VH/VV in dB, mean per window (all orbits; orbit-matched pairs are used only in GEE-3 flood change detection).
// Runs one Export per year. Set YEARS, then start each task in the Tasks tab.

var ASSETS = 'projects/YOUR_PROJECT/assets/';          // <-- change once
var YEARS = [2023, 2024, 2025, 2026];
var parcels = ee.FeatureCollection(ASSETS + 'ysr_parcels');
var mandals = ee.FeatureCollection(ASSETS + 'poc_mandals');
var cropland = ee.ImageCollection('ESA/WorldCover/v200').first().eq(40);

function s2Masked(start, end, region) {
  var sr = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(region).filterDate(start, end);
  var prob = ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY').filterBounds(region).filterDate(start, end);
  var joined = ee.Join.saveFirst('cp').apply(sr, prob, ee.Filter.equals({leftField: 'system:index', rightField: 'system:index'}));
  return ee.ImageCollection(joined).map(function (img) {
    img = ee.Image(img);
    var cp = ee.Image(img.get('cp')).select('probability');
    var scl = img.select('SCL');
    var clear = cp.lt(40).and(scl.neq(3)).and(scl.neq(8)).and(scl.neq(9)).and(scl.neq(10));
    return img.normalizedDifference(['B8', 'B4']).rename('ndvi').updateMask(clear);
  });
}

function s1(start, end, region) {
  return ee.ImageCollection('COPERNICUS/S1_GRD').filterBounds(region).filterDate(start, end)
    .filter(ee.Filter.eq('instrumentMode', 'IW'))
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
    .select(['VH', 'VV']);
}

function windows(year) {
  // Kharif: 1 Jun to 31 Jan next year, 10-day windows
  var start = ee.Date.fromYMD(year, 6, 1);
  var n = ee.Date.fromYMD(year + 1, 2, 1).difference(start, 'day').divide(10).floor();
  return ee.List.sequence(0, n.subtract(1)).map(function (i) { return start.advance(ee.Number(i).multiply(10), 'day'); });
}

function stack(d, region) {
  d = ee.Date(d);
  var e = d.advance(10, 'day');
  var ndvi = s2Masked(d, e, region).max();                  // max-NDVI composite limits residual cloud
  var sar = s1(d, e, region).mean();
  var empty = ee.Image.constant([0, 0, 0]).rename(['ndvi', 'VH', 'VV']).updateMask(0);
  return ee.ImageCollection([empty, ee.Image.cat([ndvi.rename('ndvi'), sar]).float()]).mosaic()
    .set('win', d.format('YYYY-MM-dd'));
}

YEARS.forEach(function (year) {
  var region = mandals.geometry().bounds();
  var ws = windows(year);

  var pt = ee.FeatureCollection(ws.map(function (d) {
    var img = stack(d, parcels.geometry().bounds());
    return img.reduceRegions({collection: parcels.select(['pid']), reducer: ee.Reducer.median(), scale: 10, tileScale: 8})
      .map(function (f) { return f.set('win', img.get('win')).setGeometry(null); });
  })).flatten();
  Export.table.toDrive({collection: pt, description: 'ts_parcels_ysr_' + year, folder: 'ap_poc', fileFormat: 'CSV',
    selectors: ['pid', 'win', 'ndvi', 'VH', 'VV']});

  var mt = ee.FeatureCollection(ws.map(function (d) {
    var img = stack(d, region).updateMask(cropland);
    return img.reduceRegions({collection: mandals.select(['dist', 'mid', 'mandal']), reducer: ee.Reducer.median(), scale: 20, tileScale: 8})
      .map(function (f) { return f.set('win', img.get('win')).setGeometry(null); });
  })).flatten();
  Export.table.toDrive({collection: mt, description: 'ts_mandals_' + year, folder: 'ap_poc', fileFormat: 'CSV',
    selectors: ['dist', 'mid', 'mandal', 'win', 'ndvi', 'VH', 'VV']});
});
