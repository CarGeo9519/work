import rasterio
from rasterio.features import shapes
import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import filedialog
import os
from shapely.geometry import shape, mapping
import shapely

# Function to get the georeferenced polygon of an image considering only valid pixels
def get_georeferenced_polygon(image_path):
    try:
        with rasterio.open(image_path) as dataset:
            # Read all bands
            bands = dataset.read()

            # Create mask to exclude pixels with 255 in bands 1, 2, and 3, and 0 in band 4
            mask = ~(
                (bands[0] == 255) & 
                (bands[1] == 255) & 
                (bands[2] == 255) & 
                (bands[3] == 0)
            )

            # Generate polygons from the mask
            shapes_generator = shapes(mask.astype(np.uint8), mask=mask, transform=dataset.transform)

            # Filter and combine the resulting polygons
            valid_polygons = [shape(geom) for geom, value in shapes_generator if value == 1]

            if not valid_polygons:
                return None

            # Keep only the largest polygon
            largest_polygon = max(valid_polygons, key=lambda p: p.area)

            # Convert the polygon to WKT
            polygon_wkt = largest_polygon.wkt
            return polygon_wkt
    except Exception as e:
        print(f"Error obtaining georeferenced coordinates: {e}")
        return None

# Function to export data to CSV
def export_to_csv(data, output_csv):
    try:
        # Create a DataFrame from the collected data
        df = pd.DataFrame(data, columns=['ortho_id', 'geometry'])

        # Save as CSV
        df.to_csv(output_csv, index=False)
        print(f"Georeferenced boundaries have been exported to {output_csv}")
    except Exception as e:
        print(f"Error exporting to CSV: {e}")

# Function to export the error log to a text file
def export_log(errors, log_file):
    try:
        with open(log_file, 'w') as f:
            for error in errors:
                f.write(f"{error}\n")
        print(f"Error log has been exported to {log_file}")
    except Exception as e:
        print(f"Error exporting error log: {e}")

# Function to select multiple GeoPackage files
def select_gpkg_files():
    try:
        root = tk.Tk()
        root.withdraw()
        gpkg_files = filedialog.askopenfilenames(title="Select GeoPackage files", filetypes=[("GeoPackage files", "*.gpkg")])
        if not gpkg_files:
            raise ValueError("No GeoPackage files selected.")
        
        # Request keyword to search for in layer names
        keyword = input("Enter the keyword to search for in the layer names: ")
        if not keyword:
            raise ValueError("No keyword provided.")
        
        return gpkg_files, keyword
    except Exception as e:
        print(f"Error selecting GeoPackage files: {e}")
        return None, None

# Function to select the output CSV file
def select_output_file():
    try:
        root = tk.Tk()
        root.withdraw()
        output_file = filedialog.asksaveasfilename(title="Save CSV as", defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not output_file:
            raise ValueError("No output file selected.")
        return output_file
    except Exception as e:
        print(f"Error selecting output file: {e}")
        return None

# Function to select the error log file
def select_log_file():
    try:
        root = tk.Tk()
        root.withdraw()
        log_file = filedialog.asksaveasfilename(title="Save error log as", defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if not log_file:
            raise ValueError("No log file selected.")
        return log_file
    except Exception as e:
        print(f"Error selecting log file: {e}")
        return None

def main():
    try:
        # Select multiple GeoPackage files and get the keyword
        gpkg_files, keyword = select_gpkg_files()
        if not gpkg_files or not keyword:
            raise ValueError("No valid GeoPackage files or keyword provided.")

        # Select the output CSV file
        output_csv = select_output_file()
        if not output_csv:
            raise ValueError("No valid output file selected.")

        # Select the error log file
        log_file = select_log_file()
        if not log_file:
            raise ValueError("No valid log file selected.")

        data = []
        errors = []
        for gpkg_file in gpkg_files:
            print(f"Processing GeoPackage file: {gpkg_file}")

            try:
                # Read raster layers using rasterio
                layers = []
                with rasterio.open(gpkg_file) as src:
                    layers = [s for s in src.subdatasets if keyword in s]

                if not layers:
                    error_message = f"No layers containing '{keyword}' found in GeoPackage file: {gpkg_file}"
                    print(error_message)
                    errors.append(error_message)
                    continue

                for layer_path in layers:
                    # Get the layer name to use as ortho_id
                    ortho_id = os.path.basename(layer_path).split(':')[-1]

                    # Get the georeferenced points
                    polygon_wkt = get_georeferenced_polygon(layer_path)
                    if not polygon_wkt:
                        error_message = f"Could not get georeferenced points from layer {layer_path}."
                        print(error_message)
                        errors.append(error_message)
                        continue

                    # Add the polygon and ID to the data
                    data.append([ortho_id, polygon_wkt])

            except Exception as e:
                error_message = f"Error processing GeoPackage file {gpkg_file}: {e}"
                print(error_message)
                errors.append(error_message)

        # Export boundaries as CSV
        if data:
            export_to_csv(data, output_csv)
        else:
            print("No valid data found to export.")

        # Export the error log
        if errors:
            export_log(errors, log_file)

    except Exception as e:
        print(f"Process error: {e}")

if __name__ == "__main__":
    main()
