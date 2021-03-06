import datetime
import json
import os
from functools import partial
from multiprocessing import Pool, cpu_count

import pandas as pd
import requests

from gdelt.dateFuncs import (dateRanger, gdeltRangeString)
from gdelt.getHeaders import events1Heads, events2Heads, mentionsHeads, \
    gkgHeads
from gdelt.helpers import cameos
from gdelt.inputChecks import (dateInputCheck)
from gdelt.parallel import mp_worker
from gdelt.vectorizingFuncs import urlBuilder

##############################################
#  Admin to load local files
##############################################


this_dir, this_filename = os.path.split(__file__)
BASE_DIR = os.path.dirname(this_dir)

UTIL_FILES_PATH = os.path.join(BASE_DIR, "gdeltPyR", "utils", "schema_csvs")

try:

    codes = json.load(open(os.path.join(UTIL_FILES_PATH,
                                        "cameoCodes.json")))


except:

    a = 'https://raw.githubusercontent.com/linwoodc3/gdeltPyR/master' \
        '/utils/' \
        'schema_csvs/cameoCodes.json'
    codes = json.loads((requests.get(a).content.decode('utf-8')))

##############################
# Core GDELT class
##############################

'''Gig line'''


###############################################################################

class gdelt(object):
    """GDELT Object
        Read more in the :ref:`User Guide <k_means>`.
        Parameters
        ----------
        version : int, optional, default: 2
            The version of GDELT services used by gdelt. 1 or 2
        gdelt2url : string,default: http://data.gdeltproject.org/gdeltv2/
            Base url for GDELT 2.0 services.
        gdelt1url : string, default: http://data.gdeltproject.org/events/
            Base url for GDELT 1.0 services.
        cores : int, optional, default:
            Count of total CPU cores available.
        pool: function
            Standard multiprocessing function to establish Pool workers

        Attributes
        ----------
        version : int, default: 2
            The version of GDELT services used by gdelt. 1 or 2
        cores :
            Cores used for multiprocessing pipelines
        pool : string
            pool variable for multiprocessing workers.
        baseUrl : string
            Url for GDELT queries.


        Examples
        --------
        >>> from gdelt
        >>> gd = gdelt.gdelt(version=2)
        >>> results = gd.Search(['2016 10 19'],table='events',coverage=True)
        >>> print(len(results))
        244767
        >>> print(results.columns)
        Index(['GLOBALEVENTID', 'SQLDATE', 'MonthYear', 'Year', 'FractionDate',
       'Actor1Code', 'Actor1Name', 'Actor1CountryCode', 'Actor1KnownGroupCode',
       'Actor1EthnicCode', 'Actor1Religion1Code', 'Actor1Religion2Code',
       'Actor1Type1Code', 'Actor1Type2Code', 'Actor1Type3Code', 'Actor2Code',
       'Actor2Name', 'Actor2CountryCode', 'Actor2KnownGroupCode',
       'Actor2EthnicCode', 'Actor2Religion1Code', 'Actor2Religion2Code',
       'Actor2Type1Code', 'Actor2Type2Code', 'Actor2Type3Code', 'IsRootEvent',
       'EventCode', 'EventBaseCode', 'EventRootCode', 'QuadClass',
       'GoldsteinScale', 'NumMentions', 'NumSources', 'NumArticles', 'AvgTone',
       'Actor1Geo_Type', 'Actor1Geo_FullName', 'Actor1Geo_CountryCode',
       'Actor1Geo_ADM1Code', 'Actor1Geo_ADM2Code', 'Actor1Geo_Lat',
       'Actor1Geo_Long', 'Actor1Geo_FeatureID', 'Actor2Geo_Type',
       'Actor2Geo_FullName', 'Actor2Geo_CountryCode', 'Actor2Geo_ADM1Code',
       'Actor2Geo_ADM2Code', 'Actor2Geo_Lat', 'Actor2Geo_Long',
       'Actor2Geo_FeatureID', 'ActionGeo_Type', 'ActionGeo_FullName',
       'ActionGeo_CountryCode', 'ActionGeo_ADM1Code', 'ActionGeo_ADM2Code',
       'ActionGeo_Lat', 'ActionGeo_Long', 'ActionGeo_FeatureID', 'DATEADDED',
       'SOURCEURL'],
       dtype='object')


        Notes
        ------
        gdeltPyR retrieves Global Database of Events, Language, and Tone
        (GDELT) data (version 1.0 or version 2.0) via parallel HTTP GET
        requests and is an alternative to accessing GDELT
        data via Google BigQuery .

        Performance will vary based on the number of available cores
        (i.e. CPUs), internet connection speed, and available RAM. For
        systems with limited RAM, Later iterations of gdeltPyR will include
        an option to store the output directly to disc.
        """

    def __init__(self,
                 gdelt2url='http://data.gdeltproject.org/gdeltv2/',
                 gdelt1url='http://data.gdeltproject.org/events/',
                 version=2.0,
                 cores=cpu_count(),
                 pool=Pool(processes=cpu_count())

                 ):

        self.version = version
        self.cores = cores
        self.pool = pool
        if int(version) == 2:
            self.baseUrl = gdelt2url
        elif int(version) == 1:
            self.baseUrl = gdelt1url
        self.codes = codes

    ###############################
    # Searcher function for GDELT
    ###############################

    def Search(self,
               date,
               table='events',
               headers=None,
               coverage=None,
               queryTime=datetime.datetime.now().strftime('%m-%d-%Y %H:%M:%S')
               ):
        """Placeholder text"""
        dateInputCheck(date, self.version)
        self.coverage = coverage
        self.date = date
        version = self.version
        baseUrl = self.baseUrl
        self.table = table
        self.datesString = gdeltRangeString(dateRanger(self.date),
                                            version=version,
                                            coverage=self.coverage)

        ##################################
        # Partial Functions
        #################################

        v1RangerCoverage = partial(gdeltRangeString, version=1,
                                   coverage=True)
        v2RangerCoverage = partial(gdeltRangeString, version=2,
                                   coverage=True)
        v1RangerNoCoverage = partial(gdeltRangeString, version=1,
                                     coverage=False)
        v2RangerNoCoverage = partial(gdeltRangeString, version=2,
                                     coverage=False)

        urlsv1gkg = partial(urlBuilder, version=1, table='gkg')
        urlsv2mentions = partial(urlBuilder, version=2, table='mentions')
        urlsv2events = partial(urlBuilder, version=2, table='events')
        urlsv1events = partial(urlBuilder, version=1, table='events')
        urlsv2gkg = partial(urlBuilder, version=2, table='gkg')

        eventWork = partial(mp_worker, table='events')
        codeCams = partial(cameos, codes=codes)

        #####################################
        # GDELT Version 2.0 Headers
        #####################################

        if int(self.version) == 2:
            ###################################
            # Download 2.0 Headers
            ###################################

            self.events_columns = events2Heads()
            self.mentions_columns = mentionsHeads()
            self.gkg_columns = gkgHeads()

        #####################################
        # GDELT Version 1.0 Analytics, Header, Downloads
        #####################################

        if int(self.version) == 1:

            if self.table is "mentions":
                raise BaseException('GDELT 1.0 does not have the "mentions'
                                    ' table. Specify the "events" or "gkg"'
                                    'table.')
            else:
                pass

            self.events_columns = events1Heads()
            columns = self.events_columns


            if self.table == 'gkg':
                self.download_list = (urlsv1gkg(v1RangerCoverage(
                    dateRanger(self.date))))

            elif self.table == 'events' or self.table == '':

                if self.coverage is True:

                    self.download_list = (urlsv1events(v1RangerCoverage(
                        dateRanger(self.date))))

                else:
                    # print("I'm here at line 125")
                    self.download_list = (urlsv1events(v1RangerNoCoverage(
                        dateRanger(self.date))))
            else:
                raise Exception('You entered an incorrect table type for '
                                'GDELT 1.0.')

        #####################################
        # GDELT Version 2.0 Analytics and Download
        #####################################
        elif self.version == 2:

            if self.table == 'events' or self.table == '':
                columns = self.events_columns
                if self.coverage is True:

                    self.download_list = (urlsv2events(v2RangerCoverage(
                        dateRanger(self.date))))
                else:
                    self.download_list = (urlsv2events(v2RangerNoCoverage(
                        dateRanger(self.date))))

            if self.table == 'gkg':
                columns = self.gkg_columns
                if self.coverage is True:

                    self.download_list = (urlsv2gkg(v2RangerCoverage(
                        dateRanger(self.date))))
                else:
                    self.download_list = (urlsv2gkg(v2RangerNoCoverage(
                        dateRanger(self.date))))
                    # print ("2 gkg", urlsv2gkg(self.datesString))

            if self.table == 'mentions':
                columns = self.mentions_columns
                if self.coverage is True:

                    self.download_list = (urlsv2mentions(v2RangerCoverage(
                        dateRanger(self.date))))

                else:

                    self.download_list = (urlsv2mentions(v2RangerNoCoverage(
                        dateRanger(self.date))))

        #########################
        # DEBUG Print
        #########################
        # print (self.version, self.table, self.coverage, self.datesString,
        #
        # print (self.download_list)

        #########################
        # Download section
        #########################

        if isinstance(self.datesString, str):

            if self.table == 'events':

                results = eventWork(self.download_list)
            else:
                results = mp_worker(self.download_list)
        else:

            if self.table == 'events':
                p
                pool = Pool(processes=cpu_count())
                downloaded_dfs = list(pool.imap_unordered(eventWork,
                                                          self.download_list))
            else:

                pool = Pool(processes=cpu_count())
                downloaded_dfs = list(pool.imap_unordered(mp_worker,
                                                          self.download_list))
            pool.close()
            pool.terminate()
            pool.join()
            results = pd.concat(downloaded_dfs)
            del downloaded_dfs
            results.reset_index(drop=True, inplace=True)

        if self.table == 'gkg' and self.version == 1:
            results.columns = results.ix[0].values.tolist()
            results.drop([0], inplace=True)

        else:
            results.columns = columns

        if (len(results)) == 0:
            raise ValueError("This GDELT query returned no data. Check "
                             "internet connection or query parameters and "
                             "retry")

        # Add column of human readable codes; need updated CAMEO
        if self.table == 'events':
            cameoDescripts = results.EventCode.apply(codeCams)

            results.insert(27, 'CAMEOCodeDescription',
                           value=cameoDescripts.values)

        self.final = results

        #########################
        # Return the result
        #########################
        return self.final
