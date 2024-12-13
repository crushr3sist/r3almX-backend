import duckdb
import geojson
import h3
from shapely import unary_union, wkt
from shapely.geometry import mapping

from src.lat_long_service.main import latlong_service


@latlong_service.get("/fetch")
def get_latlong(lat: str, long: str, res: int):
    return {"message": f"{lat}-{long}"}


@latlong_service.get("/fetch/polylines")
def get_cell(lat: float, long: float, res: int):
    try:
        #TODO understand the query and fix the returning data
        
        con = duckdb.connect("my_database.duckdb")  # Connect to the persistent database

        cells = list(h3.cell_to_children(h3.latlng_to_cell(lat, long, res)))[0]
        print(cells)
        geo_wkt_df = [con.sql(
            f"""
                SELECT geo_wkt
                FROM conductors
                WHERE site_1_h3_12 in {cell}
                """
        ).fetchdf() for cell in cells]
        
        # Extract WKT strings
        wkt_strings = geo_wkt_df["geo_wkt"].tolist()
        print(wkt_strings)
        if not wkt_strings:
            return {
                "message": "No geometries found for the specified cells",
                "status": 404,
            }

        # Handle geometries
        geometries = [wkt.loads(wkt_str) for wkt_str in wkt_strings]
        combined_geometry = (
            unary_union(geometries) if len(geometries) > 1 else geometries[0]
        )

        # Convert to GeoJSON format
        geojson_feature = geojson.Feature(
            geometry=mapping(combined_geometry), properties={}
        )
        print("GeoJSON Feature:", geojson_feature)

        return {"data": geojson.dumps(geojson_feature, indent=2)}

    except (duckdb.Error, Exception) as e:
        return {"message": f"exception was called: {e}", "status": 500}


@latlong_service.get("/fetch/cells")
def fetch_cells(lat: float, long: float, res: int):

    return {
        "status": 200,
        "cells": list(h3.cell_to_children(h3.latlng_to_cell(lat, long, res))),
    }
    }
