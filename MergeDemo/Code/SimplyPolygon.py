import os
import geopandas as gpd

# 1. Define folder path
input_folder = r"D:\DL\md3_original-convnext\outputs_k\merged\2"  # Input folder path
output_folder = r'D:\DL\md3_original-convnext\outputs_k\merged\3'  # Output folder path

# If the output folder does not exist, create it.
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# 2. Retrieve all .shp files within the folder
shapefiles = [f for f in os.listdir(input_folder) if f.endswith('.shp')]


# 3. Iterate through each Shapefile and process it
for shapefile in shapefiles:
    shapefile_path = os.path.join(input_folder, shapefile)

    # Read Shapefile
    gdf = gpd.read_file(shapefile_path)


    # Number of polygons deleted
    deleted_count = 0

    # 4Remove polygons with an area less than 2 and reset the index.
    gdf = gdf[gdf.geometry.area >= 2].reset_index(drop=True)
    print(f"SHP {shapefile}：After removing polygons with an area less than 2，remaining {len(gdf)} polygons")


    # 5. Iterate through each polygon, checking for overlap with other polygons.
    i = 0
    while i < len(gdf):
        geom_i = gdf.geometry.iloc[i]  # Current polygon
        area_i = geom_i.area  # The area of the current polygon

        j = i + 1
        while j < len(gdf):
            geom_j = gdf.geometry.iloc[j]  # Other polygons
            area_j = geom_j.area  # Area of other polygons

            # Calculate the overlapping portion of two polygons
            intersection = geom_i.intersection(geom_j)
            if not intersection.is_empty:
                # Calculate the proportion of the overlapping area relative to the total area of both objects.
                overlap_ratio_i = intersection.area / area_i
                overlap_ratio_j = intersection.area / area_j

                # If two polygons share more than 50% overlap
                if overlap_ratio_i > 0.2 or overlap_ratio_j > 0.2:
                    if area_i < area_j:
                        print(f" {shapefile}：Delete polygon {i}， {area_i:.2f}")
                        gdf = gdf.drop(i).reset_index(drop=True)  # Delete the current polygon and reset the index
                        deleted_count += 1
                        i -= 1  # Indexes require adjustment following deletion.
                        break  # Re-examine the index
                    else:
                        print(f" {shapefile}：Delete polygon {j}， {area_j:.2f}")
                        gdf = gdf.drop(j).reset_index(drop=True)  # Remove another polygon and reset the index
                        deleted_count += 1
                        j -= 1  # Indexes require adjustment following deletion.
            j += 1
        i += 1

    # 6. Save
    print(f" {shapefile}：A total of {deleted_count} items have been deleted. ")

    # Output
    output_shapefile_path = os.path.join(output_folder, f"{shapefile}")
    target_crs = "EPSG:25832"  #  CRS
    gdf.set_crs(target_crs, allow_override=True, inplace=True)
    #
    # Save the processed Shapefile
    gdf.to_file(output_shapefile_path)
    print(f"{shapefile}：The processed Shapefile has been saved to {output_shapefile_path}")
