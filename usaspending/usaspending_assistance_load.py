import configparser
import glob
import logging
import os.path
import urllib
from datetime import date

import click
import pandas as pd
from pyquery import PyQuery as pq
from usaspending.db import get_connection
from usaspending.util import download

logger = logging.getLogger(__name__)
config = configparser.ConfigParser()
config.read('config.ini')

# some defaults
ASSISTANCE_LIST = ['Grants', 'Loans', 'DirectPayments', 'Insurance', 'Other']


def get_archive_date():
    """Get date of latest archive files on USAspending.gov"""
    url = 'https://apps.usaspending.gov/DownloadCenter/AgencyArchive'
    d = pq(url)
    archive_date = d('#ResultsTable').find('tr').eq(1).find('td').eq(3).text()
    archive_date = archive_date.split('/')
    archive_date = archive_date[2]+archive_date[0]+archive_date[1]
    return archive_date


def get_data(archive_date, year, output_dir):
    """
    Download USAspending .csv files for specified assistance types (e.g.,
    grants, loans, insurance, direct payments, and/or other), extract,
    and save to disk
    """
    usaspending_base_url = 'http://download.usaspending.gov'
    usaspending_url = '{}/data_archives/{}/csv/'.format(
            usaspending_base_url, archive_date[0:6])

    for name in ASSISTANCE_LIST:
        print ('Downloading {}'.format(name))
        filename = '{}_All_{}_Full_{}.csv'.format(year, name, archive_date)
        filepath = os.path.join(output_dir, filename)
        zipfilename = '{}.zip'.format(filename)
        zipfilepath = os.path.join(output_dir, zipfilename)
        # if USASpending .zip archive file not already downloaded, do that
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
        # if USASpending file not already unzipped, do that
        try:
            with open(filepath) as f:
                f.close()
        except:
            download.unzip_file(zipfilepath, output_dir)


def load_file(archive_date, year, output_dir, conn):
    """
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
    """
    recip_cat_type_names = {
        'f': 'For-Profit Organization',
        'g': 'Government',
        'h': 'Higher Education',
        'n': 'Non-Profit Organization',
        'o': 'Other',
        'i': 'Individual'
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
        # If there's a missing country code but there's a valid state
        # code, set the country code to USA. When state is Puerto Rico, make
        # sure country code is consistent (chose to use 'PRI' instead of 'USA')
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
        elif country != 'USA' and state in ['00', '99']:
            return None
        elif state in ['0', '00']:
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
            # it happens--county code w/o state code
            return '999'
        else:
            return county

    def clean_recip_cat_type(value):
        cat_list = value.split(': ', 1)
        if len(cat_list) == 2 and len(cat_list[1]):
            return cat_list
        elif len(cat_list) == 2:
            cat_list[1] = recip_cat_type_names.get(cat_list[0], 'Unknown Value')
            return cat_list
        else:
            cat_list.append(recip_cat_type_names.get(cat_list[0], 'Unknown Value'))
            return cat_list

    paths = glob.glob(os.path.join(
        '{}'.format(output_dir), '{}_All_[DIGLO]*_{}.csv'.format(year, archive_date)))
    total_records = 0
    for file in paths:
        file_name = os.path.split(file)[-1]
        assistance_type = file_name.split('_')[2][0].lower()
        # use the 'usecols' parameter to load a subset of the .csv columns
        # these is also where you can map incoming column names to alternate names
        # https://github.com/fedspendingtransparency/data-act-broker-backend/blob/development/dataactvalidator/scripts/load_sf133.py#L62
        logger.info('Beginning {} file'.format(assistance_type))
        reader = pd.read_csv(
            file,
            index_col=0,
            iterator=True,
            chunksize=100000,
            dtype=str
        )

        details = pd.concat([chunk for chunk in reader], ignore_index=True)

        # for chunk in reader:
        #     logger.info('Processing chunk...')
        #     details = chunk

        # clean countries, states, counties
        logger.info('Cleaning country codes')
        details['recipient_country_code'] = details.apply(
            lambda row: clean_country(row), axis=1)
        logger.info('Cleaning state codes')
        details['recipient_state_code'] = details.apply(
            lambda row: clean_state(row), axis=1)
        logger.info('Cleaning country codes')
        details['recipient_county_code'] = details.apply(
            lambda row: clean_county(row), axis=1)
        logger.info('Cleaning agency names')
        details['agency_name'] = details.apply(
            lambda row: clean_agency_name(row), axis=1)

        # insert to db
        # this is for demo purposes only--in a django app you'd likely
        # use the ORM's bulk load option
        details.to_sql('assistance', conn, if_exists='append', index=False, chunksize=100000)

        total_records += len(details)
        logger.info('Total assistance records inserted: {}'.format(total_records))



@click.command(
    help='Download and aggregate assistance awards from USAspending.gov')
@click.argument('fiscalyear', type=click.IntRange(2000, date.today().year+1))
@click.option('--output_dir', type=click.Path(exists=True),
              help='Directory where the aggregated output data will be saved')
def usaspending_assistance(fiscalyear, output_dir):
    # little hack b/c click.path validation fails if user wants to write
    # files to current dir and, thus, doesn't supply an output_dir
    if not output_dir:
        output_dir = ''
    archive_date = get_archive_date()
    print('Getting USAspending assistance files for archive date {}'.format(archive_date))
    get_data(archive_date, fiscalyear, output_dir)
    conn = get_connection(config['DATABASE']['user'], config['DATABASE']['password'], 'usaspending')
    load_file(archive_date, fiscalyear, output_dir, conn)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    usaspending_assistance()
