"""
To run:
python3 profiling.py -i [in_dir_absolute] -d [dictionary_output]
Assumption:
1. Profiles are in the same dir as the python file

Methodology:
1. Collect metadata of the traffic
- (discrete) number of connections
- average duration between packets..? (or maybe assume normal distri with mean = x bar?)
    use numpy, s^2 = sample variance
- range of size of data sent? (approximate to normal d as above)
2. Calculate probability for each URL
- connections: eg {URL_1: [P(conn <= x1), P(x1 < conn <= x2), P(x2 < conn)] ...},
                or directly store probability for each discrete value
- duration, size of data, etc
3. Handle case of equal probability (should be unlikely?)
"""
import getopt
import linecache
import pickle
import statistics
import sys

from collections import defaultdict
from datetime import datetime
from datetime import timedelta
from pathlib import Path

def parse_time(time):
    return datetime.strptime(time, '%H:%M:%S.%f')

def write_to_disk(out_dict, raw_dict):
    processed_dict = defaultdict()

    for url_id in raw_dict:
        processed_dict[url_id] = {}

        processed_dict[url_id]["ratio"] = '%.3f'%(raw_dict[url_id]["in"]/raw_dict[url_id]["out"])

        list_in_dur = raw_dict[url_id]["in_dur"]
        mu_in_dur, sigma_in_dur = statistics.mean(list_in_dur), statistics.variance(list_in_dur)
        processed_dict[url_id]["in_dur_var"] = (mu_in_dur, sigma_in_dur) # mean, variance

        list_out_dur = raw_dict[url_id]["out_dur"]
        mu_out_dur, sigma_out_dur = statistics.mean(list_out_dur), statistics.variance(list_out_dur)
        processed_dict[url_id]["in_dur_var"] = (mu_out_dur, sigma_out_dur)

        list_in_size = raw_dict[url_id]["in_size"]
        mu_in_size, sigma_in_size = statistics.mean(list_in_size), statistics.variance(list_in_size)
        processed_dict[url_id]["in_dur_var"] = (mu_in_size, sigma_in_size)

        list_out_size = raw_dict[url_id]["out_size"]
        mu_out_size, sigma_out_size = statistics.mean(list_out_size), statistics.variance(list_out_size)
        processed_dict[url_id]["in_dur_var"] = (mu_out_size, sigma_out_size)

    with open(out_dict, 'wb') as dict_file:
        pickle.dump(processed_dict, dict_file)

def build_index(in_dir, out_dict):

    raw_dict = {}

    # obtain file paths of documents to be indexed
    dir_paths = [f for f in Path(in_dir).iterdir() if f.is_dir()]

    print(f'\nAccessing profiles at {in_dir}')

    for profile_dir in dir_paths:
        print(f"\n== At {profile_dir.stem} ==")

        file_paths = [f for f in Path(profile_dir).iterdir() if f.is_file()]

        # extract and save document ID
        for file in file_paths:
            url_id = file.stem

            # get all lines from the current document
            lines = linecache.getlines(str(file))

            # count number of ins and outs, and take ratio?
            # - the first few connections may be impt?
            # record duration betw consecutive ins
            # record duration betw consecutive outs
            # record in_size
            # record out_size

            last_in = 0
            last_out = 0

            zeroth_time = parse_time('00:00:00.0')

            for line in lines:

                timestamp, data_size, direction = line.strip().split(" ")

                timestamp = (parse_time(timestamp) - zeroth_time).total_seconds()  # timedelta obj
                data_size = int(data_size)

                if direction == "in":
                    in_dur = timestamp - last_in
                    last_in = timestamp

                    if url_id not in raw_dict:
                        raw_dict[url_id] = {"in": 1, "out": 0, "in_dur": [in_dur], "out_dur": [],
                                                  "in_size": [data_size], "out_size": []}
                    else:
                        raw_dict[url_id]["in"] += 1
                        raw_dict[url_id]["in_dur"].append(in_dur)
                        raw_dict[url_id]["in_size"].append(data_size)
                else:
                    out_dur = timestamp - last_out
                    last_out = timestamp

                    if url_id not in raw_dict:
                        raw_dict[url_id] = {"out": 1, "in": 0, "in_dur": [], "out_dur": [out_dur],
                                                  "in_size": [], "out_size": [data_size]}
                    else:
                        raw_dict[url_id]["out"] += 1
                        raw_dict[url_id]["out_dur"].append(out_dur)
                        raw_dict[url_id]["out_size"].append(data_size)

    # process data and write dict to file
    write_to_disk(out_dict, raw_dict)

    print("Done indexing")

def usage():
    print("usage: " + "python3 profiling.py -i directory-of-documents -d dictionary-output-file")

input_directory = output_file_dictionary = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'i:d:p:')
except getopt.GetoptError:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-i': # input directory
        input_directory = a
    elif o == '-d': # dictionary file
        output_file_dictionary = a
    else:
        assert False, "unhandled option"

if input_directory == None or output_file_dictionary == None:
    usage()
    sys.exit(2)

build_index(input_directory, output_file_dictionary)
