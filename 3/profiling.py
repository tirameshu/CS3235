"""
To run:
python3 profiling.py -i [in_dir_absolute] -d [dictionary_output]
Assumption:
1-anon. Profiles are in the same dir as the python file

Methodology:
1-anon. Collect metadata of the traffic
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
import sys

from collections import defaultdict
from datetime import datetime
from pathlib import Path

def parse_time(time):
    return datetime.strptime(time, '%H:%M:%S.%f')

def print_dict(dictionary):
    for url_id in dictionary:
        print(f'\nURL {url_id}')
        for field in dictionary[url_id]:
            print(f'{field}: {dictionary[url_id][field]}')

"""
Only store distinct values and match based 
only on no. of matches for unique values
- ie if the values are [1-anon, 2, 3], even if 10 occurrences of 1-anon is encountered,
    it is counted as 1-anon match
- this is done because the count for each unique value is
    an aggregate of all the profiles. Requires standardisation for file size
    otherwise.
- also assumed that connections of different sites are different enough
    
Alternative:
1-anon) Compare by absolute number of matches
    - ie given [1-anon, 2, 3] if 10 occurrences of 1-anon is encountered,
        it's counted as 10 matches.
2) Compare by percentage match for each unique file size
    - eg given [(1-anon, count: 2), (2, count: 3), (3, count: 9)] in profile,
        observed [(1-anon, count: 1-anon), (2, count: 5), (3, count: 3)], 
        percentage match: (1-anon/2 + 1-anon + 3/9)/3
        
"""
def write_to_disk(out_dict, raw_dict):
    items = [(int(k), v) for k, v in raw_dict.items()]
    items.sort(key=lambda x: x[0])
    processed_dict = dict(items)

    # print_dict(processed_dict)

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

        # extract and save url ID
        for file in file_paths:
            url_id = file.stem

            # get all lines from the current document
            lines = linecache.getlines(str(file))

            for line in lines:

                timestamp, data_size, direction = line.strip().split(" ")
                data_size = int(data_size)

                if direction == "in":

                    if url_id not in raw_dict:
                        raw_dict[url_id] = {"in": 0, "out": 0,
                                                  "in_size": set(), "out_size": set()}
                    raw_dict[url_id]["in"] += 1
                    raw_dict[url_id]["in_size"].add(data_size)
                elif direction == "out":

                    if url_id not in raw_dict:
                        raw_dict[url_id] = {"in": 0, "out": 0,
                                                  "in_size": set(), "out_size": set()}
                    raw_dict[url_id]["out"] += 1
                    raw_dict[url_id]["out_size"].add(data_size)
                else:
                    print("Unknown direction!\n")
                    sys.exit(2)

    # process data and write dict to file
    write_to_disk(out_dict, raw_dict)

    print("Done indexing")

def usage():
    print("usage: " + "python3 profiling.py -i directory-of-documents -d dictionary-output-file")

input_directory = output_file_dictionary = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'i:d:')
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
