from spatiotemporal.temporal_events.formulas import TemporalRelation
from spatiotemporal.temporal_events.trapezium import generate_random_events
import os
import csv
import numpy as np
import ffx

__author__ = 'keyvan'


def create_sample_file(number_of_events=100):
    csv_writer = csv.writer(open(os.path.dirname(os.path.abspath(__file__)) + '/data.csv~', 'w+'))

    temporal_events = generate_random_events(number_of_events)

    for i in xrange(10):
        for A in temporal_events:
            for B in temporal_events:
                for C in temporal_events:
                    csv_writer.writerow((A * B).to_list() + (B * C).to_list() + (A * C).to_list())


def learn_ffx(predicate='p', size=None):
    train_x = []
    for i in xrange(26):
        train_x.append([])
    train_y = []
    test_x = []
    for i in xrange(26):
        test_x.append([])
    test_y = []
    csv_reader = csv.reader(open(os.path.dirname(os.path.abspath(__file__)) + '/data.csv~'))

    if size is None:
        size = -1

    row_number = 0
    for row in csv_reader:

        if row_number == size:
            break
        for i, element in enumerate(row):
            row[i] = np.float64(element)

        x, y = None, None
        if row_number < size / 2:
            x, y = train_x, train_y
        else:
            x, y = test_x, test_y

        for i in xrange(26):
            x[i].append(row[i])

        y.append(row[26 + TemporalRelation.all_relations.index(predicate)])
        row_number += 1

    train_x = np.array(train_x).T
    test_x = np.array(test_x).T
    train_y = np.array(train_y)
    test_y = np.array(test_y)

    models = ffx.run(train_x, train_y, test_x, test_y, list(TemporalRelation.all_relations))
    for model in models:
        print model

if __name__ == '__main__':
    import time

    start = time.time()

    learn_ffx(size=10)

    print 'Performance:', time.time() - start, 'seconds'
