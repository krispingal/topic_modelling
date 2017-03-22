from __future__ import print_function
import os
import logging
from argparse import ArgumentParser
from itertools import product
from gensim import corpora, models
from memory_profiler import profile
from time import clock

""" Code to benchmark gensim's LDA on enron email dataset """

#Test dataset
MODELS_DIR = "../../Data/models/mini_newsgroup"
#Actual dataset
#MODELS_DIR = "../../Data/models/enron"
OUT_DIR = "../../Data/out"

topic_out_file = "topic_enron.rst"
perf_out_file = "perf_enron.csv"
mem_out_file = "mem_enron.txt"

default_num_test_passes = 3
default_num_words = 20
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

mem_out = open(os.path.join(OUT_DIR, mem_out_file), 'w+')

def parse_args():
    parser = ArgumentParser(description="Benchmark Gensim's LDA on Enron dataset")
    parser.add_argument("--disable_timing", help="Don't measure timing", action="store_true")
    parser.add_argument("--disable_memory", help="Don't measure memory usage", action="store_true")
    parser.add_argument("--disable_topic_words", help="Don't write out top n words", action="store_true")
    parser.add_argument("-w", "--num_words", type=int, default=default_num_words, help="Number of top words to e displayed per topic")
    parser.add_argument("-p", "--num_passes", type=int, default=default_num_test_passes, help="Number of passes to measure timing")
    args = parser.parse_args()
    return args

def setup_output_files(args, OUT_DIR):
    perf_out = None
    topic_out = None
    if args.disable_timing == False:
        perf_out = open(os.path.join(OUT_DIR, perf_out_file), 'w+')
#    if args.disable_memory == False:
#        mem_out = open(os.path.join(OUT_DIR, mem_out_file), 'w+')
    if args.disable_topic_words == False:
        topic_out = open(os.path.join(OUT_DIR, topic_out_file), 'w+')
    return perf_out, mem_out, topic_out

""" Runs LDA with given params num_passes times to measure performance """
def runLDA_perf(params, num_passes, fout):
    print("\n{0}, {1}, {2}".format(params['num_topics'], params['iterations'], params['workers']), end='', file=fout)
    lda = None
    for i in xrange(num_passes):
        t0 = clock()
        lda = models.ldamulticore.LdaMulticore(**params)
        print(", {0:.3f}".format((clock() - t0)), end='', file=fout)
    print("Completed LDA with params; num_topics:{0}, num_iterations:{1}, num_workers:{2}".format(params['num_topics'], params['iterations'], params['workers']))
    return lda

@profile(stream=mem_out)      
def runLDA_mem(params):
    models.ldamulticore.LdaMulticore(**params)

""" """
def print_topics(topic_mat, params, num_words, fout):
    print("\nTop {0} words of LDA model with params; num_topics:{1}, num_iterations:{2}, num_workers:{3}\n".format(num_words, params['num_topics'], params['iterations'], params['workers']), file=fout)
    for topic_id, topic_words in topic_mat:
        print("{0}. Topic id # {1}".format(topic_id+1, topic_id), end=' ', file=fout)
        print([str(word) for i, (word, prob) in enumerate(topic_words)], file=fout)

def iterate_arguments(param_grid):
    # Sort the keys of a dict for reproducibility
    items = sorted(param_grid.items())
    if not items:
        yield {}
    else:
        keys, values = zip(*items)
        for v in product(*values):
            params = dict(zip(keys, v))
            yield params

""" Main function which will dispatch params to appropriate LDA benchmarking functions """
def run_benchmark():
    args = parse_args()
    #Test Dictionary
    dictionary = corpora.Dictionary.load(os.path.join(MODELS_DIR,'twentyNewsGroup.dict'))
    #Actual Dictionary
    #dictionary = corpora.Dictionary.load(os.path.join(MODELS_DIR,'enron.dict'))
    corpus = corpora.MmCorpus(os.path.join(MODELS_DIR, 'corpora.mm'))
    tfidf = models.TfidfModel(corpus)
    corpus_tfidf = tfidf[corpus]
    param_grid = {
    "num_topics" : [5, 10, 20, 30, 40],
    "iterations" : [50, 100, 300, 600, 1000],
    "workers" : [None, 1, 2, 3, 4]
    #TODO: set up for different implementations
#    "implementation" : ["gensim", "mallet"]
    }
    perf_out, mem_out, topic_out = setup_output_files(args, OUT_DIR)
    if (args.disable_timing == False) and (args.disable_memory == False):
        for params in iterate_arguments(param_grid):
            print("Starting with params {0}".format(params))
            params.update({'corpus' : corpus, 'id2word' : dictionary})
            lda = runLDA_perf(params, args.num_passes, perf_out)
            print("Mem testing LDA with params; num_topics:{0}, num_iterations:{1}, num_workers:{2}\n".format(params['num_topics'], params['iterations'], params['workers']), file=mem_out)
            runLDA_mem(params)
            print("Completed")
            topic_mat = lda.show_topics(formatted=False,num_words=args.num_words,num_topics=params['num_topics'])
            print_topics(topic_mat, params, args.num_words, topic_out)
    elif args.disable_memory == True:
        for params in iterate_arguments(param_grid):
            print("Starting with params {0}".format(params))
            params.update({'corpus' : corpus, 'id2word' : dictionary})
            lda = runLDA_perf(params, args.num_passes, perf_out)
            print("Completed")
            topic_mat = lda.show_topics(formatted=False,num_words=args.num_words,num_topics=params['num_topics'])
            print_topics(topic_mat, params, args.num_words, topic_out)
    
if __name__ == "__main__":
    run_benchmark()
