"""
Run:
python3 search.py -d dictionary-file -ob1 obervation-1 -ob2 obversation-2
"""

import getopt
import linecache
import pickle
import statistics
import sys
import time

from collections import defaultdict
from datetime import datetime
from pathlib import Path

def parse_time(time):
    return datetime.strptime(time, '%H:%M:%S.%f')

def assign_rank(difference):
    ranked_result = {}

    for metric in difference:
        if metric not in ranked_result:
            ranked_result[metric] = []

        lst = difference[metric]
        labelled_lst = list(map(lambda x: (x, lst.index(x)+1), lst)) # lst.index(x) gives url_id
        # TODO: detect duplicate here?

        labelled_lst.sort(key=lambda x: x[0])

        id_with_rank = []
        for i in range (len(labelled_lst)):
            id_with_rank.append((i+1, labelled_lst[i][1])) # (rank, url_id)

        id_with_rank.sort(key=lambda x: x[1])
        ranked_result[metric] = list(map(lambda x: x[0], id_with_rank))

    return ranked_result

def get_top_match(ranked_result):
    min_rank = 100
    best_matched_url = 0
    all_values = list(ranked_result.values()) # nested list of ranks

    length = len(all_values[0])

    for lst in all_values:
        assert(len(lst) == length) # sanity check

    for i in range (length):
        score = sum(map(lambda x: x[i], all_values))
        if score < min_rank:
            min_rank = score
            best_matched_url = i+1 # url_id

    return best_matched_url


def compare_observation(dictionary, process_result):

    match_result = {}

    for anon_id in process_result:

        observed_ratio = process_result[anon_id]["ratio"]
        observed_in_dur = process_result[anon_id]["in_dur"]
        observed_out_dur = process_result[anon_id]["out_dur"]
        observed_in_size = process_result[anon_id]["in_size"]
        observed_out_size = process_result[anon_id]["out_size"]

        # key, value = metric, [absolute difference between observation and urls 1 - 35]
        difference = {"ratio": [], "in_dur": [], "out_dur": [], "in_size": [], "out_size": []}

        # assign rank to each url
        # in terms of the difference between
        # sample mean and profiled mean
        # 1 being the smallest; 35 being the largest
        for url_id in dictionary:
            assert (type(url_id) == int)
            profiled_ratio = dictionary[url_id]["ratio"]
            profiled_in_dur = dictionary[url_id]["in_dur"]
            profiled_out_dur = dictionary[url_id]["out_dur"]
            profiled_in_size = dictionary[url_id]["in_size"]
            profiled_out_size = dictionary[url_id]["out_size"]

            difference["ratio"].append(abs(float(observed_ratio) - float(profiled_ratio)))
            difference["in_dur"].append(abs(observed_in_dur - profiled_in_dur[0]))
            difference["out_dur"].append(abs(observed_out_dur - profiled_out_dur[0]))
            difference["in_size"].append(abs(observed_in_size - profiled_in_size[0]))
            difference["out_size"].append(abs(observed_out_size - profiled_out_size[0]))

        ranked_result = assign_rank(difference)

        # TODO: ensure 1-to-1 mapping
        top_match = get_top_match(ranked_result)

        match_result[anon_id] = top_match

    return match_result

def process_observation(observation_dir):

    process_result = {}

    file_paths = [f for f in Path(observation_dir).iterdir() if f.is_file()]

    raw_dict = {}

    for file in file_paths:
        anon_id = file.stem

        lines = linecache.getlines(str(file))

        last_in = 0
        last_out = 0

        zeroth_time = parse_time('00:00:00.0')

        for line in lines:

            timestamp, data_size, direction = line.strip().split(" ")

            timestamp = (parse_time(timestamp) - zeroth_time).total_seconds()
            data_size = int(data_size)

            if direction == "in":
                in_dur = timestamp - last_in
                last_in = timestamp

                if anon_id not in raw_dict:
                    raw_dict[anon_id] = {"in": 1, "out": 0, "in_dur": [in_dur], "out_dur": [],
                                        "in_size": [data_size], "out_size": []}
                else:
                    raw_dict[anon_id]["in"] += 1
                    raw_dict[anon_id]["in_dur"].append(in_dur)
                    raw_dict[anon_id]["in_size"].append(data_size)
            else:
                out_dur = timestamp - last_out
                last_out = timestamp

                if anon_id not in raw_dict:
                    raw_dict[anon_id] = {"out": 1, "in": 0, "in_dur": [], "out_dur": [out_dur],
                                        "in_size": [], "out_size": [data_size]}
                else:
                    raw_dict[anon_id]["out"] += 1
                    raw_dict[anon_id]["out_dur"].append(out_dur)
                    raw_dict[anon_id]["out_size"].append(data_size)

    for anon_id in raw_dict:
        process_result[anon_id] = {}

        process_result[anon_id]["ratio"] = '%.3f'%(raw_dict[anon_id]["in"]/raw_dict[anon_id]["out"])

        list_in_dur = raw_dict[anon_id]["in_dur"]
        process_result[anon_id]["in_dur"] = statistics.mean(list_in_dur) # only store mean

        list_out_dur = raw_dict[anon_id]["out_dur"]
        process_result[anon_id]["out_dur"] = statistics.mean(list_out_dur)

        list_in_size = raw_dict[anon_id]["in_size"]
        process_result[anon_id]["in_size"] = statistics.mean(list_in_size)

        list_out_size = raw_dict[anon_id]["out_size"]
        process_result[anon_id]["out_size"] = statistics.mean(list_out_size)

    return process_result

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

    print(f"Accuracy: {accuracy}")

def search(dictionary_file, observation_1, observation_2):
    print('\nStarting search\n')
    start_time = time.time()  # clock the run

    with open(dictionary_file, 'rb') as dict_file:
        dictionary = pickle.load(dict_file)

    print("Processing observation1\n")
    process_result_1 = process_observation(observation_1)

    print("Comparing observation1 against profiles\n")
    res1 = compare_observation(dictionary, process_result_1) # {anon_id: url_id}
    items_1 = list(res1.items())
    items_1.sort(key=lambda x: x[1])
    assert(len(set(items_1)) == len(items_1))

    # TODO: adapt for actual naming system: [n]-anon
    corresponding_anon_id_1 = list(map(lambda x: x[0], items_1))
    accuracy_check(corresponding_anon_id_1)

    print("Processing observation2\n")
    process_result_2 = process_observation(observation_2)

    print("Comparing observation2 against profiles\n")
    res2 = compare_observation(dictionary, process_result_2)
    items_2 = list(res2.items())
    items_2.sort(key=lambda x: x[1])
    assert (len(set(items_2)) == len(items_2))
    corresponding_anon_id_2 = list(map(lambda x: x[0], items_2))
    accuracy_check(corresponding_anon_id_2)

    results_file = "output.txt"
    # parse and evaluate each query and write results to disk one by one

    assert(len(corresponding_anon_id_1) == len(corresponding_anon_id_2))

    with open(results_file, 'w') as r:
        print("Sending to output\n")
        for i in range (len(corresponding_anon_id_1)):
            result_string = str(corresponding_anon_id_1[i]) + " " + str(corresponding_anon_id_2[i])
            r.write(result_string + '\n')

    end_time = time.time()
    print('Matching completed in ' + str(round(end_time - start_time, 2)) + 's')

def usage():
    print("usage: " + "python3 search.py -d dictionary-output-file -ob1 observation-1 -ob2 observation-2")

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
