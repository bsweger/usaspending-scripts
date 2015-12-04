import pandas as pd
import numpy as np
import os.path, glob, urllib, csv
from util import download
from datetime import date
from pyquery import PyQuery as pq
import click

# Aggregates and re-formats raw data from USASpending monthly archives
# and writes output to the raw_data folder

#some defaults
ASSISTANCE_LIST = ['Grants', 'Loans', 'DirectPayments', 'Insurance', 'Other']

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
    Download USAspending .csv files for specified assistance types (e.g.,
    grants, loans, insurance, direct payments, and/or other), extract,
    and save to disk
    '''

    usaspending_base_url = 'http://download.usaspending.gov'
    usaspending_url = '{}/data_archives/{}/csv/'.format(
            usaspending_base_url, archive_date[0:6])

    for name in ASSISTANCE_LIST:
        print ('Downloading {}'.format(name))
        filename = '{}_All_{}_Full_{}.csv'.format(year, name, archive_date)
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
                continue
        #if USASpending file not already unzipped, do that
        try:
            with open(filepath) as f:
                f.close()
        except:
            download.unzip_file(zipfilepath, output_dir)

def create_aggregate(archive_date, year, output_dir):
    '''
    Read .csv assistance award files in the USAspending format and return
    a single file that aggregates spending dollar amounts by:

    * country
    * state
    * county
    * catalog of federal domestic assistance number/description
    * agency
    * assistance type
    * assistance category
    * recipient type

    '''

    recip_cat_type_names = {
        'f':'For-Profit Organization',
        'g':'Government',
        'h':'Higher Education',
        'n':'Non-Profit Organization',
        'o':'Other',
        'i':'Individual'
    }

    def clean_agency_name(row):
        agency_name = row['agency_name']
        if not agency_name:
            agency_code = row['agency_code']
            if agency_code == '9575':
                agency_name = 'DELTA REGIONAL AUTHORITY'
            elif agency_code == '6800':
                agency_name = 'ENVIRONMENTAL PROTECTION AGENCY'
            else:
                agency_name = 'MISSING AGENCY NAME'
        return agency_name

    def clean_country(row):
        country = row['recipient_country_code']
        state = row['recipient_state_code']
        #If there's a missing country code but there's a valid state
        #code, set the country code to USA. When state is Puerto Rico, make
        #sure country code is consistent (chose to use 'PRI' instead of 'USA')
        if state == 'PR':
            return 'PRI'
        if country == 'missing':
            if state != '99':
                return 'USA'
            else:
                return None
        else:
            return country

    def clean_state(row):
        country = row['recipient_country_code']
        state = row['recipient_state_code']
        if country != 'USA' and state == 'VA':
            return None
        elif country != 'USA' and state in ['00','99']:
            return None
        elif state in ['0','00']:
            return '99'
        else:
            return state

    def clean_county(row):
        country = row['recipient_country_code']
        state = row['recipient_state_code']
        county = row['recipient_county_code']
        if country != 'USA':
            return None
        elif state == '99' and county != '999':
            #it happens--county code w/o state code
            return '999'
        else:
            return county

    def clean_recip_cat_type(value):
        list = value.split(': ', 1)
        if len(list) == 2 and len(list[1]):
            return list
        elif len(list) == 2:
            list[1] = recip_cat_type_names.get(list[0],'Unknown Value')
            return list
        else:
            list.append(recip_cat_type_names.get(list[0],'Unknown Value'))
            return list

    collist = [
        'unique_transaction_id',
        'cfda_program_num',
        'recipient_county_code',
        'agency_code',
        'fed_funding_amount',
        'non_fed_funding_amount',
        'total_funding_amount',
        'assistance_type',
        'cfda_program_title',
        'face_loan_guran',
        'orig_sub_guran',
        'fiscal_year',
        'recip_cat_type',
        'asst_cat_type',
        'recipient_country_code',
        'recipient_state_code'
    ]

    assistance = pd.DataFrame()
    paths = glob.glob(os.path.join(
        '{}'.format(output_dir),'{}_All_[DIGLO]*_{}.csv'.format(year, archive_date)))
    for file in paths:
        file_name = os.path.split(file)[-1]
        assistance_type = file_name.split('_')[2][0].lower()
        reader = pd.read_csv(
            file,
            usecols=collist,
            index_col=0,
            iterator=True,
            chunksize=3000,
            dtype={
                'cfda_program_num':np.object,
                'recipient_county_code':np.object,
                'recipient_state_code':np.object,
                'fiscal_year':np.object}
        )
        details = pd.concat([chunk for chunk in reader], ignore_index=True)

        #clean up missing values (so they're not excluded from the groupby)
        details = details.fillna({
            'fyq': 'missing',
            'cfda_program_num': '0',
            'recipient_county_code': '999',
            'recipient_country_code': 'missing',
            'uri': 'missing',
            'recipient_state_code': '99'
        })

        #aggregate numeric fields
        totals = details.groupby([
            details['cfda_program_num'],
            details['cfda_program_title'],
            details['agency_code'],
            details['recipient_county_code'],
            details['recipient_state_code'],
            details['recipient_country_code'],
            details['assistance_type'],
            details['fiscal_year'],
            details['asst_cat_type'],
            details['recip_cat_type'],
        ]).sum()
        totals = totals.reset_index()

        #split codes and descriptions into separate columns
        totals['agency_code'], totals['agency_name'] = zip(
            *totals['agency_code'].apply(lambda x: x.split(':', 1)))
        totals['assistance_type'], totals['assistance_type_name'] = zip(
            *totals['assistance_type'].apply(lambda x: x.split(': ', 1)))
        totals['recip_cat_type'], totals['recip_cat_type_name'] = zip(
            *totals['recip_cat_type'].apply(lambda x: clean_recip_cat_type(x)))

        #clean countries, states, counties
        totals['recipient_country_code'] = totals.apply(
            lambda row: clean_country(row),axis=1)
        totals['recipient_state_code'] = totals.apply(
            lambda row: clean_state(row), axis=1)
        totals['recipient_county_code'] = totals.apply(
            lambda row: clean_county(row), axis=1)
        totals['agency_name'] = totals.apply(
            lambda row: clean_agency_name(row), axis=1)

        #fix up data types
        totals.fed_funding_amount = totals.fed_funding_amount.astype(np.int64)
        totals.non_fed_funding_amount = totals.non_fed_funding_amount.astype(np.int64)
        totals.total_funding_amount = totals.total_funding_amount.astype(np.int64)
        totals.face_loan_guran = totals.face_loan_guran.astype(np.int64)
        totals.orig_sub_guran = totals.orig_sub_guran.astype(np.int64)

        del details
        assistance = pd.concat([assistance, totals])
        del totals
        try:
            os.remove(file)
        except:
            print ('Unable to delete {}.'.format(file), end = ' ')
            print ('You might want to do this manually to free up space.\n')
    assistance_file = 'assistance_totals_{}_{}.csv'.format(year, archive_date)
    assistance.to_csv(
        os.path.join(output_dir, assistance_file),
        index=False,
        quoting = csv.QUOTE_NONNUMERIC)
    print ('Saved {} aggregates to {}\{}\n'.format(
        year, output_dir, assistance_file))

@click.command(
    help='Download and aggregate assistance awards from USAspending.gov')
@click.argument('fiscalyear', type=click.IntRange(2000, date.today().year+1))
@click.option('--output_dir', type=click.Path(exists=True), help='Directory where the aggregated output data will be saved')
def usaspending_assistance(fiscalyear, output_dir):
    #little hack b/c click.path validation fails if user wants to write
    #files to current dir and, thus, doesn't supply an output_dir
    if not output_dir:
        output_dir = ''
    archive_date = get_archive_date()
    print ('Getting USAspending assistance files for archive date {}'.format(archive_date))
    get_data(archive_date, fiscalyear, output_dir)
    print ('Munging...')
    create_aggregate(archive_date, fiscalyear, output_dir)

if __name__ == '__main__':
    usaspending_assistance()
