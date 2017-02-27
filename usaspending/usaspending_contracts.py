import pandas as pd
import numpy as np
import os.path
import urllib
import csv
from util import download
from datetime import date
from pyquery import PyQuery as pq
import us
import click

# Aggregates and re-formats raw data from USASpending monthly archives
# and writes output to the raw_data folder

def get_archive_date():
    ''' Get date of latest archive files on USAspending.gov
    '''

    url = 'https://apps.usaspending.gov/DownloadCenter/AgencyArchive'
    d = pq(url)
    date = d('#ResultsTable').find('tr').eq(1).find('td').eq(3).text()
    date = date.split('/')
    date = date[2]+date[0]+date[1]
    return date

def get_data(archive_date, year, output_dir):
    '''
    Download USAspending .csv contract archive file,
    extract, and save to disk
    '''

    print ('Downloading Contracts')
    usaspending_base_url = 'http://download.usaspending.gov'
    usaspending_url = '{}/data_archives/{}/csv/'.format(
            usaspending_base_url, archive_date[0:6])
    filename = '{}_All_Contracts_Full_{}.csv'.format(
        year, archive_date)
    filepath = os.path.join(output_dir, filename)
    zipfilename = '{}.zip'.format(filename)
    zipfilepath = os.path.join(output_dir, zipfilename)
    #if USASpending .zip archive file not already downloaded, do that
    try:
        with open(zipfilepath) as f:
            pass
    except:
        zipfileurl = urllib.parse.urljoin(usaspending_url, zipfilename)
        r = download.download_file(zipfileurl, zipfilepath)
        if not r[0]:
            print ('Unable to download {} (status = {})'.format(
                zipfileurl, r[1]))
            return
    #if USASpending file not already unzipped, do that
    try:
        with open(filepath) as f:
            f.close()
    except:
        download.unzip_file(zipfilepath, output_dir)

def create_aggregate(archive_date, year, output_dir):
    '''
    Read .csv contract award files in the USAspending format and return
    a single file that aggregates obligated dollar amounts by:

    * place of performance country
    * place of performance state
    * major agency
    '''

    collist = [
        'dollarsobligated',
        'maj_agency_cat',
        'fiscal_year',
        'pop_state_code',
        'placeofperformancecountrycode'
    ]

    file = os.path.join(
        '{}'.format(output_dir), '{}_All_Contracts_Full_{}.csv'.format(
            year, archive_date))
    file_name = os.path.split(file)[-1]
    contract_type = file_name.split('_')[2][0].lower()
    reader = pd.read_csv(
        file,
        usecols=collist,
        iterator=True,
        dtype={'dollarsobligated':np.float},
        chunksize=3000
    )
    details = pd.concat([chunk for chunk in reader], ignore_index=True)

    #clean up missing values (so they're not excluded from aggregations)
    details['maj_agency_cat'] = details['maj_agency_cat'].replace(
        '^: $', np.nan, regex=True)
    details['pop_state_code'] = details['pop_state_code'].replace(
        '^: $', np.nan, regex=True)
    details['placeofperformancecountrycode'] = details[
        'placeofperformancecountrycode'].replace(':', np.nan)
    details = details.fillna({
        'maj_agency_cat': 'Missing: Missing',
        'pop_state_code': 'UD: Undistributed',
        'placeofperformancecountrycode': 'Missing: Missing'
    })

    #aggregate
    totals = details.groupby([
        'maj_agency_cat',
        'pop_state_code',
        'placeofperformancecountrycode',
        'fiscal_year'
    ]).sum()
    totals = totals.reset_index()

    totals['maj_agency_code'] = totals.maj_agency_cat.str.split(': ').str.get(0)
    totals['maj_agency_name'] = totals.maj_agency_cat.str.split(': ').str.get(1)
    del totals['maj_agency_cat']
    totals['placeofperformancecountrycode'] = \
        totals.placeofperformancecountrycode.str.split(':').str.get(0)

    #clean up states
    def clean_state(row):
        state = row['pop_state_code']
        country = row['placeofperformancecountrycode']
        if country != 'USA':
            return None
        try:
            state_abbr = us.states.lookup(state[:2]).abbr
        except:
            try:
                state_abbr = us.states.lookup(state.split(': ')[1]).abbr
            except:
                state_abbr = None
        return state_abbr
    totals['pop_state_code'] = totals.apply(
        lambda row: clean_state(row), axis = 1)

    contract_file = 'contract_totals_{}_{}.csv'.format(year, archive_date)
    totals.to_csv(
        os.path.join(output_dir, contract_file),
    index=False,
    quoting = csv.QUOTE_NONNUMERIC)
    print ('Saved {} aggregates to {}\{}\n'.format(
    year, output_dir, contract_file))
    del details
    del totals
    try:
        os.remove(file)
    except:
        print ('Unable to delete {}.'.format(file), end = ' ')
        print ('You might want to do this manually to free up space.\n')

@click.command(
    help='Download and aggregate contract awards from USAspending.gov')
@click.argument('fiscalyear', type=click.IntRange(2000, date.today().year+1))
@click.option('--output_dir', type=click.Path(exists=True), \
    help='Directory where the aggregated output data will be saved')
def usaspending_contract(fiscalyear, output_dir):
    #little hack b/c click.path validation fails if user wants to write
    #files to current dir and, thus, doesn't supply an output_dir
    if not output_dir:
        output_dir = ''
    archive_date = get_archive_date()
    print ('Getting USAspending contract files for archive date {}'.format(
        archive_date))
    get_data(archive_date, fiscalyear, output_dir)
    print ('Munging...')
    create_aggregate(archive_date, fiscalyear, output_dir)

if __name__ == '__main__':
    usaspending_contract()
