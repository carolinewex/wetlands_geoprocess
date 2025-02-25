# wetlands_geoprocess

Given two wetland survey datasets, one containing a table of polygons and acres and one containing a table of lines and linear feet. Both tables include the Cowardin Aggregate attribute (a wetland classification system). This python script sums the total acreage and total linear feet recorded from across the wetland survey, then summarizes the total calculations according to the attribute Cowardin Aggregate. The output is two master tables containing the total acres and linear feet joined to a map series in ArcGIS Pro.

From these tables, you can input the unique values into dynamic text for each frame in the map series.
