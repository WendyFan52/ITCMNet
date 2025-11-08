import geopandas as gpd
from shapely.geometry import box, Polygon, MultiPolygon
import numpy as np
import pandas as pd

# Calculate the centroid of a polygon
def get_centroid(polygon):
    return polygon.centroid

# Calculate the distance from the centroid of a polygon to a point
def calculate_distance(polygon, point):
    return polygon.centroid.distance(point)

# Create 2048x2048 grids with 50% overlap
def create_grid(bounds, grid_size=2048 * 0.02, overlap=0.5):
    min_x, min_y, max_x, max_y = bounds
    x_step = grid_size * (1 - overlap)
    y_step = grid_size * (1 - overlap)

    x_coords = np.arange(min_x, max_x, x_step)
    y_coords = np.arange(min_y, max_y, y_step)

    grid_boxes = []

    for x in x_coords:
        for y in y_coords:
            grid_boxes.append(box(x, y, x + grid_size, y + grid_size))

    return grid_boxes

# Determine if one polygon is completely contained within another
def is_polygon_contained(poly1, poly2):
    return poly2.contains(poly1)

# Normalization function
def normalize_series(series):
    min_val = series.min()
    max_val = series.max()
    if max_val == min_val:
        return series * 0 + 1  # If all values are equal, normalize to 1
    return (series - min_val) / (max_val - min_val)

# Process polygons within each grid, handling 30% overlap + distance and 80% overlap cases
def process_grid(shp_data, grid_box, weight_area=0.5, weight_distance=0.5,
                 overlap_threshold_30=0.3, overlap_threshold_80=0.7):
    polys_in_grid = shp_data[shp_data.intersects(grid_box)].copy()

    if len(polys_in_grid) < 2:
        return polys_in_grid

    grid_center = grid_box.centroid

    # Calculate area and distance normalization
    polys_in_grid['area'] = polys_in_grid.geometry.area
    polys_in_grid['distance'] = polys_in_grid.geometry.apply(lambda p: calculate_distance(p, grid_center))
    polys_in_grid['area_norm'] = normalize_series(polys_in_grid['area'])
    polys_in_grid['distance_norm'] = normalize_series(polys_in_grid['distance'])

    # Weighted score, higher score means higher priority to keep
    polys_in_grid['score'] = weight_area * polys_in_grid['area_norm'] + weight_distance * (1 - polys_in_grid['distance_norm'])

    to_drop = set()

    for i, poly1 in polys_in_grid.iterrows():
        if i in to_drop:
            continue

        for j, poly2 in polys_in_grid.iterrows():
            if i >= j or j in to_drop:
                continue

            overlap_area = poly1['geometry'].intersection(poly2['geometry']).area
            overlap_ratio1 = overlap_area / poly1['geometry'].area
            overlap_ratio2 = overlap_area / poly2['geometry'].area

            # If fully contained, remove the smaller one
            if is_polygon_contained(poly1['geometry'], poly2['geometry']):
                to_drop.add(i)
                continue
            elif is_polygon_contained(poly2['geometry'], poly1['geometry']):
                to_drop.add(j)
                continue

            # If overlap exceeds 80%, remove the smaller one
            if overlap_ratio1 > overlap_threshold_80 or overlap_ratio2 > overlap_threshold_80:
                if poly1['area'] < poly2['area']:
                    to_drop.add(i)
                else:
                    to_drop.add(j)
                continue

            # If overlap exceeds 30%, apply weighted rule
            if overlap_ratio1 > overlap_threshold_30 or overlap_ratio2 > overlap_threshold_30:
                if poly1['score'] < poly2['score']:
                    to_drop.add(i)
                else:
                    to_drop.add(j)

    polys_in_grid = polys_in_grid.drop(list(to_drop))
    print(f"Processed grid: {grid_box.bounds}, removed {len(to_drop)} polygons.")

    # Remove temporary columns
    return polys_in_grid.drop(columns=['area', 'distance', 'area_norm', 'distance_norm', 'score'])

# Assign polygons to corresponding grids
def assign_polygons_to_grids(shp_data, grid_boxes):
    assigned_polygons = gpd.GeoDataFrame(columns=shp_data.columns)

    for idx, poly in shp_data.iterrows():
        if isinstance(poly['geometry'], (Polygon, MultiPolygon)) and not poly['geometry'].is_empty:
            best_grid = determine_polygon_grid(poly['geometry'], grid_boxes)
            if best_grid:
                poly['grid'] = best_grid
                assigned_polygons = pd.concat([assigned_polygons, pd.DataFrame([poly])], ignore_index=True)

    return assigned_polygons

# Determine which grid a polygon belongs to
def determine_polygon_grid(poly, grid_boxes):
    if not isinstance(poly, (Polygon, MultiPolygon)) or poly.is_empty:
        return None

    max_area = 0
    best_grid = None
    for grid_box in grid_boxes:
        if isinstance(grid_box, Polygon):
            intersection_area = poly.intersection(grid_box).area
            if intersection_area > max_area:
                max_area = intersection_area
                best_grid = grid_box

    return best_grid

# Main function
def process_shp(shp_file, output_file, grid_size=2048 * 0.02, overlap=0.5,
                weight_area=0.5, weight_distance=0.5,
                overlap_threshold_30=0.3, overlap_threshold_80=0.8):
    shp_data = gpd.read_file(shp_file)
    print(f"Loaded {len(shp_data)} polygons from {shp_file}.")

    bounds = shp_data.total_bounds
    grid_boxes = create_grid(bounds, grid_size, overlap)
    print(f"Created {len(grid_boxes)} grids.")

    assigned_polygons = assign_polygons_to_grids(shp_data, grid_boxes)

    processed_polys = []
    for grid_box in grid_boxes:
        polys_in_grid = assigned_polygons[assigned_polygons['grid'] == grid_box]
        if not polys_in_grid.empty:
            processed_polys.append(
                process_grid(polys_in_grid, grid_box, weight_area, weight_distance,
                             overlap_threshold_30, overlap_threshold_80)
            )

    processed_shp = gpd.GeoDataFrame(pd.concat(processed_polys, ignore_index=True))

    if 'grid' in processed_shp.columns:
        processed_shp = processed_shp.drop(columns=['grid'])

    valid_columns = {col: processed_shp[col].dtype for col in processed_shp.columns if col != 'geometry'}
    print(f"Saving with columns: {valid_columns}")

    processed_shp.to_file(output_file, driver='ESRI Shapefile')
    print(f"Finished processing. Output saved to {output_file}.")

# Execute main function
input_shp = r'D:\DL\md3_original-convnext\outputs\input.shp'
output_shp = r'D:\DL\md3_original-convnext\outputs\output.shp'
process_shp(input_shp, output_shp)
