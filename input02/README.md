# Historical folder: MATLAB files and preliminary adaption to Python

This folder contains MATLAB codes that the former architecture used to read data from preformated CSV files at [CO-OPS](https://tidesandcurrents.noaa.gov/). Noticeable differences include the absence of an input folder for the CSV files, the absence of a generated output folder to contain result files such as CSV data files and plots, and Jupyter Notebook and Python files from earlier stages of editing.

## Input files

- The data originate from sites listed by [CO-OPS Historic Current Data](https://tidesandcurrents.noaa.gov/cdata/StationList?type=Current+Data&filter=historic)
  - For testing purposes, LIS1016 served as the data source for its proximity to the Verdant Power project in the original GitHub repository made by hosseinsz93
- The input files follow this format: {site ID on CO-OPS}_{depth in meters and centimeters, with two decimal places for each unit}-{dataset's initial date as year-month-day, with four decimal places for year and two decimal places for month and day}
  - In a discontinuous dataset, the user can mark files with the same site and depth bin, but with different initial dates
    - E.g., LIS1016_05m76cm-2010-06-09.csv, LIS1016_05m76cm-2010-07-10.csv

## MATLAB files

1. FolderReadCSV.m reads the preformated files to extract necessary info for use by the files downstream
2. VertVelPlot.m calls FolderReadCSV.m, and then it conducts basic calculations for further inputs downstream
3. identifyTidalFlow.m works in the same way as the classification in principal_flood_ebb_calculation.ipynb and the export of depth-dependent velocity components in label_df-depthDep
4. extractCosineTideParameters.m intends to process the data after identification for fitting to cosine cycles, with the expected output being what tidal-cycles.ipynb provides
5. flowVisualized.m accepts the processed data to make post-processed visuals including flow data, time series, representation by northward and eastward components, and current rose

## Python and Jupyter Notebook files

- folderRead_DFsave.ipynb is the counterpart of FolderReadCSV.m, but it saves data from Pandas dataframes into CSV files for access by other files
- test_load_data.py is only a testing file that explored alternative saving options such as through [Numpy](https://numpy.org/numpy-tutorials/save-load-arrays/)
