#! /usr/bin/env python3
#
# Copyright 2016 leftcoast.io, inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
#
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import subprocess
from datetime import datetime, timedelta
from sys import platform

from dateutil.tz import tzlocal


def remove_newline(field):
    return (field.split("\n")[0]).strip()


def extract_value(field):
    """Return the entire value portion from a name:value field"""
    return remove_newline(field.split(": ")[1])


def extract_left_most_field(field):
    """Isolate and return left most whitespace delimited field"""
    return extract_value(field).split()[0]


def extract_left_most_integer(field):
    """Extract the leftmost whitespace delimited field as an integer"""
    return int(extract_left_most_field(field))


def extract_as_milliseconds_from_seconds(field):
    """Extract and trim the s off the left most number and convert to ms"""
    return int(float(extract_left_most_field(field).replace("s", "", 1)) * 1000)


def query_local_ntp_client():
    """Extract the delay, dispersion, stratum and source fields from the
        local ntp client as a dictionary.
    """

    model = {}

    local_ntp_query = subprocess.Popen(
        'w32Tm /query /status',
        shell=True,
        stdout=subprocess.PIPE,
        universal_newlines=True)

    # TODO: Add check for service not enabled or any other error code
    for field in local_ntp_query.stdout:
        if "Delay:" in field:
            model['delay'] = extract_as_milliseconds_from_seconds(field)
        elif "Dispersion:" in field:
            model['dispersion'] = extract_as_milliseconds_from_seconds(field)
        elif "Stratum:" in field:
            model['stratum'] = extract_left_most_integer(field)
        elif "Source:" in field:
            model['src'] = extract_value(field)
        elif "Poll Interval:" in field:
            model['poll_interval_as_log2_exp'] = extract_left_most_integer(
                    field)
        elif "Sync Time:" in field:
            model['last_synced'] = datetime.strptime(
                    extract_value(field), "%m/%d/%Y %I:%M:%S %p").replace(
                tzinfo=tzlocal())

    return model


def format_interval_duration(prefix, interval):
    """ format the interval parameter as seconds and a timestamp"""
    return "{0} {1:,d} seconds or {2}".format(
        prefix,
        int(interval.total_seconds()),
        (datetime.min + interval).strftime("%H:%M:%S"))


def format_time_with_tz(prefix, timestamp):
    """ format the time and date passed in per the hosts's Locale plus
        the name of the timezone
    """
    return "{0} {1}".format(prefix, timestamp.strftime("at %c %Z"))


def print_ntp_stats(ntp_stats, extended):
    """ return local ntp status information in a dictionary"""
    print("synchronized to NTP server {0} at stratum {1}".format(
        ntp_stats.get('src'),
        ntp_stats.get('stratum')))

    print("\ttime correct to within {0}ms".format(
            int((float(ntp_stats.get('delay')) +
                 float(ntp_stats.get('dispersion'))) / 2)))
    interval = timedelta(seconds=2 ** ntp_stats['poll_interval_as_log2_exp'])

    if extended:
        last_synced = ntp_stats.get('last_synced')
        now = datetime.now(tzlocal())
        next_sync = last_synced + interval
        print(format_interval_duration("\tpolling server every", interval))
        print(format_time_with_tz("\ttime last successfully synchronized at",
                                  last_synced))
        print(format_time_with_tz(
            format_interval_duration(
                "\ttime next scheduled to synchronize with {src} in".format(
                    **ntp_stats),
                next_sync - now),
            next_sync))
        print(format_time_with_tz("\tthe current time is", now).replace(" at ",
                                                                        " "))

    else:
        print("\tpolling server every {0:,d}s".format(
            int(interval.total_seconds())))

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
            prog='ntpstat.py',
            usage='ntpstat.py [--verbose]',
            description='Describe time synchronization with UTC',
            allow_abbrev=True)

    parser.add_argument(
            '--verbose',
            dest='verbose',
            action='store_true',
            default=False,
            help='show detailed ntp statistics')

    args = parser.parse_args()

    if platform == "win32":
        print_ntp_stats(query_local_ntp_client(), args.verbose)
    else:
        for line in subprocess.Popen('ntpstat',
                                     shell=True,
                                     stdout=subprocess.PIPE,
                                     universal_newlines=True).stdout:
            print(remove_newline(line))

        for line in subprocess.Popen('ntpq -p',
                                     shell=True,
                                     stdout=subprocess.PIPE,
                                     universal_newlines=True).stdout:
            print(remove_newline(line))
