"""
Run:
python3 search.py -d dictionary-file -f obervation-1-anon -s obversation-2
"""

import getopt
import linecache
import pickle
import sys
import time

from collections import defaultdict
from datetime import datetime
from pathlib import Path

def parse_time(time):
    return datetime.strptime(time, '%H:%M:%S.%f')

def print_dict(dictionary):
    for field in dictionary:
        print(f'{field}: {dictionary[field]}')

def assign_rank(match_count):
    # match_count = {"in_size": [(url_id, no. of unique matches), ...], "out_size": [ same ] }
    ranked_result = {}

    for metric in match_count:
        if metric not in ranked_result:
            ranked_result[metric] = []

        labelled_lst = match_count[metric]

        labelled_lst.sort(key=lambda x: x[1], reverse=True)

        id_with_rank = []
        for i in range (len(labelled_lst)):
            id_with_rank.append((i+1, labelled_lst[i][0])) # (rank, url_id)

        id_with_rank.sort(key=lambda x: x[1]) # sorted by url_id
        ranked_result[metric] = list(map(lambda x: x[0], id_with_rank)) # list of ranks in order of url_id

    return ranked_result

def get_top_match(ranked_result):

    # ranked result = {"in_size": [ranks in order of url_id], "out_size": [...] }
    min_rank = 100
    best_matched_url = 0
    all_values = list(ranked_result.values()) # nested list of ranks

    length = len(all_values[0])

    # sanity check
    for lst in all_values:
        assert(len(lst) == length)

    for i in range (length):
        score = sum(map(lambda x: x[i], all_values))
        if score < min_rank:
            min_rank = score
            best_matched_url = i+1 # url_id

    return best_matched_url


def compare_observation(dictionary, process_result):
    # process_result = {anon_id: {"in": [count], "out": [count], "in_size": { set }, "out_size": { set } }

    match_result = {}

    for anon_id in process_result:

        # only in_size and out_size

        observed_in_size = process_result[anon_id]["in_size"]
        observed_out_size = process_result[anon_id]["out_size"]

        # key, value = metric, [absolute difference between observation and urls 1-anon - 35]
        match_count = {"in_size": [], "out_size": []}

        # assign rank to each url
        # in terms of the difference between
        # sample mean and profiled mean
        # 1-anon being the smallest; 35 being the largest
        for url_id in dictionary:
            profiled_in_size = dictionary[url_id]["in_size"]
            profiled_out_size = dictionary[url_id]["out_size"]

            match_count["in_size"].append((url_id, len(observed_in_size.intersection(profiled_in_size))))
            match_count["out_size"].append((url_id, len(observed_out_size.intersection(profiled_out_size))))

        ranked_result = assign_rank(match_count)

        # TODO: ensure 1-anon-to-1-anon mapping
        top_match = get_top_match(ranked_result)

        match_result[anon_id] = top_match

    return match_result

def process_observation(observation_dir):

    file_paths = [f for f in Path(observation_dir).iterdir() if f.is_file()]

    raw_dict = {}

    for file in file_paths:
        anon_id = file.stem.strip("-anon")

        lines = linecache.getlines(str(file))

        for line in lines:

            timestamp, data_size, direction = line.strip().split(" ")
            data_size = int(data_size)

            if direction == "in":

                if anon_id not in raw_dict:
                    raw_dict[anon_id] = {"in": 0, "out": 0,
                                        "in_size": set(), "out_size": set()}
                raw_dict[anon_id]["in"] += 1
                raw_dict[anon_id]["in_size"].add(data_size)

            elif direction == "out":

                if anon_id not in raw_dict:
                    raw_dict[anon_id] = {"in": 0, "out": 0,
                                        "in_size": set(), "out_size": set()}
                raw_dict[anon_id]["out"] += 1
                raw_dict[anon_id]["out_size"].add(data_size)

            else:
                print("Unknown direction!\n")
                sys.exit(2)

    return raw_dict

def accuracy_check(id_list):
    id_list = list(map(int, id_list))
    correct = 0
    for i in range (len(id_list)):
        if id_list[i] == i+1:
            correct += 1

    if correct == 0:
        accuracy = 0
    else:
        accuracy = correct / len(id_list)

    print(f"Accuracy: {accuracy}\n")

def search(dictionary_file, observation_1, observation_2):
    # print('\nStarting search\n')
    start_time = time.time()  # clock the run

    with open(dictionary_file, 'rb') as dict_file:
        dictionary = pickle.load(dict_file)

    # print("Processing observation1")
    # {anon_id: {"in": [count], "out": [count], "in_size": { set }, "out_size": { set } }
    process_result_1 = process_observation(observation_1)

    # print("Comparing observation1 against profiles")
    res1 = compare_observation(dictionary, process_result_1) # {anon_id: url_id}
    items_1 = list(res1.items())
    items_1.sort(key=lambda x: x[1])
    assert(len(set(items_1)) == len(items_1))

    corresponding_anon_id_1 = list(map(lambda x: x[0], items_1))
    # print(corresponding_anon_id_1)
    # accuracy_check(corresponding_anon_id_1)

    # print("Processing observation2")
    process_result_2 = process_observation(observation_2)

    # print("Comparing observation2 against profiles")
    res2 = compare_observation(dictionary, process_result_2)
    items_2 = list(res2.items())
    items_2.sort(key=lambda x: x[1])
    assert (len(set(items_2)) == len(items_2))
    corresponding_anon_id_2 = list(map(lambda x: x[0], items_2))
    # print(corresponding_anon_id_2)
    # accuracy_check(corresponding_anon_id_2)

    results_file = "result.txt"
    # parse and evaluate each query and write results to disk one by one

    assert(len(corresponding_anon_id_1) == len(corresponding_anon_id_2))

    with open(results_file, 'w') as r:
        # print("Sending to output\n")
        for i in range (len(corresponding_anon_id_1)):
            result_string = str(corresponding_anon_id_1[i]) + " " + str(corresponding_anon_id_2[i])
            r.write(result_string + '\n')

    end_time = time.time()
    # print('Matching completed in ' + str(round(end_time - start_time, 2)) + 's')

def usage():
    print("usage: " + "python3 search.py -d dictionary-output-file -f observation-1-anon -s observation-2")

dictionary_file = observation_1 = observation_2 = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'd:f:s:')
except getopt.GetoptError:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-d':
        dictionary_file = a
    elif o == '-f':
        observation_1 = a
    elif o == '-s':
        observation_2 = a
    else:
        assert False, "unhandled option"

if dictionary_file == None or observation_1 == None or observation_2 == None:
    usage()
    sys.exit(2)

search(dictionary_file, observation_1, observation_2)
