# USAspending Scripts

This repository contains scripts that download and summarize U.S. federal spending data from [USAspending.gov](http://www.usaspending.gov "USAspending.gov").

It creates files that look like:
* [data/assistance_totals_sample.csv](data/assistance_totals_sample.csv "assistance awards summary sample file") (for assistance awards) and
* [data/contract_totals_sample.csv](data/contract_totals_sample.csv "contract awards summary sample file") (contracts)

These scripts are adapted from my work at [National Priorities Project](https://www.nationalpriorities.org/ "National Priorities Project"). USAspending powers NPP's [State Smart](https://www.nationalpriorities.org/smart/ "State Smart") and [Local Spending Data](https://www.nationalpriorities.org/interactive-data/database/ "Local Spending Data") applications.

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

The output file summarizes these dollar amounts:
* fed_funding_amount: total federal obligated dollars
* non_fed_funding_amount: total non-federal funding
* total funding amount
* face_loan_guaran: total face value of direct loans or loan guarantees
* orig_sub_guran: total original subsidy costs of direct loans or guarantees

These dollar amounts are summarized by the fields below:

* recipient country
* recipient state
* recipient county
* catalog of federal domestic assistance number/description
* agency
* assistance type
* assistance category
* recipient type

To see an example of what the summarized file looks like, see [data/assistance_totals_sample.csv](data/assistance_totals_sample.csv "assistance awards summary sample file")

### Contracts

The command for creating a summary of contract awards is:

        $ python usaspending_contracts.py [--output_dir] FISCALYEAR

For example, to download and summarize contract award data for fiscal year 2014 to the folder in this project called *data*:

        $ python usaspending_contracts.py --output_dir=data 2014

The script will run and let you know when it's saved the summary file:

    Saved 2014 aggregates to data\contract_totals_2014_20151115.csv

The output file summarizes _dollarsobligated_ (dollar amount obligated via contract transactions) by the following fields:

* place of performance country
* place of performance state
* major agency

To see an example of what the summarized contract file looks like, see [data/contract_totals_sample.csv](data/contract_totals_sample.csv "contract awards summary sample file").

## More Information and Caveats

Visit [USAspending's data page](https://www.usaspending.gov/about/Pages/TheData.aspx "USAspending data") to learn more about the spending data that's included (and not included) on the website.

A [PDF version of the data dictionary](https://www.usaspending.gov/about/PublishingImages/Pages/TheData/USAspending.gov%20Data%20Dictionary.pdf "USAspending data dictionary").

The spending amounts reported by USAspending represent [obligated dollars](https://www.nationalpriorities.org/budget-basics/federal-budget-101/glossary/#obligations "National Priorities Project Federal Budget Glossary"), not [outlays](https://www.nationalpriorities.org/budget-basics/federal-budget-101/glossary/#outlays "National Priorities Project Federal Budget Glossary").

There are known issues with the data quality on USAspending. That said, this is currently the only place to get a single source of granular federal spending data. The scripts here try to clean up some of the obvious errors and low-hanging fruit. Ultimately, however, there's no script that can fix missing and incorrect information on the site. Thus, the totals in the summary files should match what's reported on USAspending but may not always provide a true picture of U.S. federal spending.
