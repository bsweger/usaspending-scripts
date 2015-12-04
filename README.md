# USAspending Scripts

This repository contains scripts that download and summarize U.S. federal spending data from [USAspending.gov](http://www.usaspending.gov "USAspending.gov").

It creates files that look like this: [data/assistance_totals_sample.csv](data/assistance_totals_sample.csv "assistance awards summary sample file").

## Background

The data on USAspending represents (mostly) individual awards. For example, a grant to a university or a contract to buy something. That's interesting, but sometimes it's also useful to see award amounts summarized by agency, program, and geographic area. The Census Bureau used to publish this summarized award information (and much more) in the annual Consolidated Federal Funds Report (CFFR), but that report stopped when the Federal Financial Statistics program was terminated in 2012.

These scripts don't recreate the CFFR exactly, but they do take a year's worth of individual awards and aggregate the dollar amounts by descriptors like state, county, agency, and "program" (see below for complete file layout).

## What it Does

At a high level, the scripts:
* Download a fiscal year's worth of spending data from the latest available versions of the full [monthly archive files](https://www.usaspending.gov/DownloadCenter/Pages/dataarchives.aspx "USAspending data archives").
* Tidy up the data.
* Summarize the total spending amounts (see below).
* Save the results as a .csv

USAspending has federal spending data in two different formats: assistance awards and contracts. Assistance awards are grants, loans, insurance, and direct payments to individuals (for example, Social Security). Contracts represent federal purchases from vendors.

## Installing

Assuming that you already have a Python 3 development environment up and running:

1. From the command line, clone the project repository from GitHub to your local environment: ```git clone git@github.com:bsweger/usaspending-scripts.git```
2. If you don't have a GitHub account and want to get a read-only version of the code use this command instead: ```git clone git://github.com/bsweger/usaspending-scripts.git```
3. Change to the project directory: ```cd usaspending-scripts```
4. Install Python dependencies: ```pip install -r requirements.txt```

## Using

### Assistance Awards

The command for creating a summary of assistance awards is:

        $ python usaspending_assistance.py [--output_dir] FISCALYEAR

For example, to download and summarize assistance award data for fiscal year 2015 to the folder in this project called *data*:

        $ python usaspending_assistance.py --output_dir=data 2015

The script will run and let you know when it's saved the summary file:

    Saved 2015 aggregates to data\assistance_totals_2016_20151115.csv

Dollar amounts in the assistance file are summarized by these fields. To see an example of what the file will look like, see [data/assistance_totals_sample.csv](data/assistance_totals_sample.csv "assistance awards summary sample file").

* country
* state
* county
* catalog of federal domestic assistance number/description
* agency
* assistance type
* assistance category
* recipient type

### Contracts

TODO
