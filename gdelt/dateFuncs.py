import datetime
import warnings

import numpy as np
from dateutil.parser import parse

from gdelt.vectorizingFuncs import vectorizer


def parse_date(var):
    """Return datetime object from string."""

    try:
        return np.where(isinstance(parse(var), datetime.datetime),
                        parse(var), "Error")
    except Exception as e:
        return "You entered an incorrect date.  Check your date format."


def dateFormatter(datearray):
    """Function to format strings for numpy arange"""
    return parse(datearray).strftime("%Y-%m-%d")


def dateRanger(originalArray):
    """Function to vectorize date formatting function.
    Creates datetime.date objects for each day in the range
    and stores in a numpy array.

    Example

    Parameters
        ----------
        originalArray : {array-like, sparse matrix}, shape (n_samples, n_features)
            Input data, where ``n_samples`` is the number of samples and
            ``n_features`` is the number of features.
    Returns
    -------
    self : object
        Returns self.
    """

    minutes = list(map(str, range(00, 60, 15)))
    hours = list(map(str, range(0, 24)))
    times = []
    for l in hours:
        if int(l) < 10:
            l = "0" + l
        for k in minutes:
            if k == "0":
                k = '00'
            times.append('{0}:{1}'.format(l, k))

    if isinstance(originalArray, str):
        """Check user input to retrieve date query."""

        return np.where(len(originalArray) == 0, "crazy",
                        parse_date(originalArray))

    elif isinstance(originalArray, list):

        if len(originalArray) == 1:
            return np.array(parse("".join(originalArray)))
        elif len(originalArray) > 2:
            #
            #             return np.array(map(parse,originalArray),dtype='datetime64[D]').tolist()
            return np.array(list(map(lambda x: parse(x), originalArray)))
        else:

            cleaner = np.vectorize(dateFormatter)
            converted = cleaner(originalArray).tolist()
            dates = np.arange(converted[0], converted[1],
                              dtype='datetime64[D]')
            dates = list(map(lambda x: datetime.datetime.combine(
                x, datetime.datetime.min.time()), dates.tolist()))
            if len(originalArray) == 2:
                adder = np.datetime64(parse(converted[1]).date())
                adder = datetime.datetime.combine(adder.tolist(),
                                                  datetime.datetime.min.time())
                return np.append(dates,
                                 adder)  # numpy range is not endpoint inclusive
            else:
                pass
            return np.array(dates)


def gdeltRangeString(element, coverage=None, version=2.0):
    """Takes a numpy datetime and converts to string"""

    ########################
    # Numpy datetime to object
    ########################


    ########################
    #     Current day check
    ########################


    minutes = list(map(str, range(00, 60, 15)))
    hours = list(map(str, range(0, 24)))
    times = []
    for l in hours:
        if int(l) < 10:
            l = "0" + l
        for k in minutes:
            if k == "0":
                k = '00'
            times.append('{0}:{1}'.format(l, k))

    element = element.tolist()

    hour = datetime.datetime.now().hour
    multiplier = (datetime.datetime.now().minute // 15)
    multiple = 15 * multiplier
    conditioner = multiplier + 1

    # calculate nearest 15 minute interval
    if not isinstance(element, list):

        if element.date() == datetime.datetime.now().date():
            if coverage and int(version) != 1:

                converted = np.array(
                    list(map(
                        lambda x: np.datetime64(parse(str(element) + " " + x)
                                                ).tolist().strftime(
                            '%Y%m%d%H%M%S'
                        ), times[:hour * 4 + conditioner])))
            else:
                converted = datetime.datetime.now().replace(
                    minute=multiple, second=0).strftime('%Y%m%d%H%M%S')

        else:
            if coverage and int(version) != 1:

                converted = restOfDay = np.array(
                    list(map(
                        lambda x: np.datetime64(parse(str(element) + " " + x)
                                                ).tolist().strftime(
                            '%Y%m%d%H%M%S'
                        ), times[:])))
            else:

                converted = element.replace(minute=int(
                    multiple), second=0).strftime('%Y%m%d%H%M%S')


    #################################
    # All non-current dates section
    #################################

    else:

        ####################
        # Handling list
        ####################

        if isinstance(element, list) is True:

            #             converted = map(lambda x: x.strftime('%Y%m%d%H%M%S'),element)
            converted = list(map(lambda x: (
                datetime.datetime.combine(x, datetime.time.min) +
                datetime.timedelta(
                    minutes=45, hours=23
                )
            ).strftime('%Y%m%d%H%M%S'), element))
        else:
            converted = (datetime.datetime.combine(
                element, datetime.time.min) +
                         datetime.timedelta(
                             minutes=45, hours=23
                         )
                         ).strftime('%Y%m%d%H%M%S')

        ####################
        # Return all 15 min intervals
        ####################
        if coverage and int(version) != 1:

            converted = []
            for i in element:
                converted.append(np.array(
                    list(map(
                        lambda x: np.datetime64(parse(str(i) + " " + x)
                                                ).tolist().strftime(
                            '%Y%m%d%H%M%S'
                        ), times[:]))))
            converted = np.concatenate(converted, axis=0)
            if len(converted.tolist()) >= (5 * 192):
                warnText = ("This query will download {0} files, and likely "
                            "exhaust your memory with possibly 10s of "
                            "GBs of data in this single query.Hit Ctr-C to kill "
                            "this query if you do not want to "
                            "continue.".format(len(converted.tolist())))
                warnings.warn(warnText)

    ########################
    # Version 1 Datestrings
    #########################
    if int(version) == 1:
        if isinstance(converted, list) is True:

            converted = list(
                map(lambda x: np.where((parse(x) >= parse(
                    '2013 04 01')), parse(x).strftime('%Y%m%d%H%M%S')[:8],
                                       np.where((parse(x) < parse(
                                           '2006 01 01') and (
                                                     int(version) == 1)),
                                                parse(x).strftime(
                                                    '%Y%m%d%H%M%S')[:4],
                                                parse(x).strftime(
                                                    '%Y%m%d%H%M%S')[:6]))
                    , converted))
            converted = list(map(lambda x: x.tolist(), converted))
            converted = list(set(converted))  # account for duplicates
        else:
            converted = np.where((parse(converted) >= parse('2013 04 01')),
                                 parse(converted).strftime('%Y%m%d%H%M%S')[:8],
                                 np.where((parse(converted) < parse(
                                     '2006 01 01') and (int(version) == 1)),
                                          parse(converted).strftime(
                                              '%Y%m%d%H%M%S')[:4],
                                          parse(converted).strftime(
                                              '%Y%m%d%H%M%S')[:6])).tolist()

    return converted


def dateMasker(dateString, version):
    mask = (np.where((int(version == 1) and parse(dateString) >= parse(
        '2013 04 01')) or (int(version) == 2),
                     vectorizer(gdeltRangeString, dateRanger(dateString))[:8],
                     np.where(int(version) == 1 and parse(
                         dateString) < parse('2006 01'),
                              vectorizer(gdeltRangeString, dateRanger(
                                  dateString))[:4],
                              vectorizer(gdeltRangeString, dateRanger(
                                  dateString))[:6]))).tolist()
    return mask
