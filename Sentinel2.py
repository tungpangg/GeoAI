import ee
import folium

# กำหนด Project ID สำหรับ Google Earth Engine
ee.Initialize(project="pp-aonpreeya9226")


def add_ee_layer(self, ee_image_object, vis_params, name):
    """Adds an Earth Engine image layer to a folium map."""
    map_id_dict = ee.Image(ee_image_object).getMapId(vis_params)
    folium.raster_layers.TileLayer(
        tiles=map_id_dict['tile_fetcher'].url_format,
        attr='Google Earth Engine',
        name=name,
        overlay=True,
        control=True,
    ).add_to(self)


folium.Map.add_ee_layer = add_ee_layer


def mask_s2_clouds(image):
    """Masks clouds in a Sentinel-2 image using the QA band.

    Args:
        image (ee.Image): A Sentinel-2 image.

    Returns:
        ee.Image: A cloud-masked Sentinel-2 image.
    """
    qa = image.select('QA60')

    # Bits 10 and 11 are clouds and cirrus, respectively.
    cloud_bit_mask = 1 << 10
    cirrus_bit_mask = 1 << 11

    # Both flags should be set to zero, indicating clear conditions.
    mask = (
        qa.bitwiseAnd(cloud_bit_mask)
        .eq(0)
        .And(qa.bitwiseAnd(cirrus_bit_mask).eq(0))
    )

    return image.updateMask(mask).divide(10000)


dataset = (
    ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterDate('2020-01-01', '2020-01-30')
    # Pre-filter to get less cloudy granules.
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
    .map(mask_s2_clouds)
)

visualization = {
    'min': 0.0,
    'max': 0.3,
    'bands': ['B4', 'B3', 'B2'],
}

m = folium.Map(location=[17.7009, 83.277], zoom_start=12)
m.add_ee_layer(dataset.mean(), visualization, 'RGB')
folium.LayerControl().add_to(m)

# บันทึกแผนที่เป็นไฟล์ HTML
m.save('Sentinel2.html')

print("Created map: Sentinel2.html")
