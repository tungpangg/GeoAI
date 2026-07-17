import datetime

import ee
import folium

# กำหนด Project ID สำหรับ Google Earth Engine
ee.Initialize(project="pp-aonpreeya9226")


def add_ee_layer(self, ee_image_object, vis_params, name):
    """Adds an Earth Engine image layer to a folium map and returns the layer."""
    map_id_dict = ee.Image(ee_image_object).getMapId(vis_params)
    tile_layer = folium.raster_layers.TileLayer(
        tiles=map_id_dict['tile_fetcher'].url_format,
        attr='Google Earth Engine',
        name=name,
        overlay=True,
        control=True,
    )
    tile_layer.add_to(self)
    return tile_layer


folium.Map.add_ee_layer = add_ee_layer

# ขอบเขตประเทศไทยจาก dataset มาตรฐานของ Earth Engine
countries = ee.FeatureCollection('FAO/GAUL/2015/level0')
thailand = countries.filter(ee.Filter.eq('ADM0_NAME', 'Thailand'))
thailand_geom = thailand.geometry()

start_date = '2026-01-01'
end_date = datetime.date.today().isoformat()

# Cloud Score+ ให้ผลการมาสก์เมฆที่แม่นยำกว่า QA60 bitmask แบบเดิม
cs_plus = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED')
QA_BAND = 'cs_cdf'
CLEAR_THRESHOLD = 0.60

filtered = (
    ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterBounds(thailand_geom)
    .filterDate(start_date, end_date)
    # เก็บเฉพาะภาพที่มีเมฆไม่เกิน 10%
    .filter(ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', 10))
    .linkCollection(cs_plus, [QA_BAND])
)

image_count = filtered.size().getInfo()

dataset = filtered.map(
    lambda image: image.updateMask(image.select(QA_BAND).gte(CLEAR_THRESHOLD)).divide(10000)
)

composite = dataset.median().clip(thailand_geom)

visualization = {
    'min': 0.0,
    'max': 0.3,
    'bands': ['B4', 'B3', 'B2'],
}

center_lon, center_lat = thailand_geom.centroid().coordinates().getInfo()

m = folium.Map(location=[center_lat, center_lon], zoom_start=6, tiles=None)

# Google Satellite basemap (ไม่มีชื่อถนน/ป้ายกำกับ)
folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
    attr='Google',
    name='Google Satellite',
    overlay=False,
    control=True,
).add_to(m)

composite_layer = m.add_ee_layer(composite, visualization, 'Sentinel-2 Median (Thailand)')

# เส้นขอบเขตประเทศไทย
folium.GeoJson(
    thailand_geom.getInfo(),
    name='ขอบเขตประเทศไทย',
    style_function=lambda feature: {
        'fillOpacity': 0,
        'color': 'yellow',
        'weight': 2,
    },
).add_to(m)

folium.LayerControl().add_to(m)

# กล่องข้อมูล + แถบเลื่อนความโปร่งใสของภาพ composite
info_box_html = f"""
<div id="info-box" style="position: fixed; top: 10px; left: 60px; z-index: 9999;
     background: rgba(255,255,255,0.92); padding: 10px 14px; border-radius: 6px;
     box-shadow: 0 1px 6px rgba(0,0,0,0.35); font-family: Tahoma, sans-serif;
     font-size: 13px; max-width: 480px;">
  <div style="font-weight: bold; font-size: 15px; margin-bottom: 4px; color: #1a56db; white-space: nowrap;">
    Sentinel-2 Median Composite &mdash; ประเทศไทย
  </div>
  <div style="color:#555; margin-bottom:8px;">
    {start_date} ถึง {end_date} | เมฆ &lt; 10% + Cloud Score+ mask | {image_count} ภาพ | RGB (B4-B3-B2)
  </div>
  <div>
    ความโปร่งใส:
    <input id="opacity-slider" type="range" min="0" max="1" step="0.01" value="1"
           style="vertical-align: middle; width: 160px;">
  </div>
</div>
<script>
  document.getElementById('opacity-slider').addEventListener('input', function(e) {{
    {composite_layer.get_name()}.setOpacity(parseFloat(e.target.value));
  }});
</script>
"""
m.get_root().html.add_child(folium.Element(info_box_html))

# บันทึกแผนที่เป็นไฟล์ HTML
m.save('Sentinel2_Thailand.html')

print(f"Created map: Sentinel2_Thailand.html ({image_count} images)")
