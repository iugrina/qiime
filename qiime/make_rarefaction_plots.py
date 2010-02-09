#!/usr/bin/env python
#file rarefaction_plots.py
from __future__ import division
__author__ = "Meg Pirrung"
__copyright__ = "Copyright 2009, QIIME"
__credits__ = ["Meg Pirrung"] 
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "Meg Pirrung"
__email__ = "meg.pirrung@colorado.edu"
__status__ = "Prototype"

"""
Author: Meg Pirrung (meg.pirrung@colorado.edu) 
Status: Prototype

Requirements:
Python 2.5
Matplotlib
Numpy
"""

from sys import argv, exit
from random import choice, randrange
from time import strftime
from qiime import parse, util
from numpy import array, transpose, random, mean, std, arange
from string import strip
from matplotlib.pylab import savefig, clf, gca, gcf, errorbar
import matplotlib.pyplot as plt
import os.path
from optparse import OptionParser
from os.path import exists, splitext, split
import shutil
from itertools import cycle

COLOUR_GRAD = ['#9933cc', #purple
        '#3333cc', #blue
        '#6699cc', #bluetint
        '#666666', #gray
        '#9966cc', #lilac
        '#009999', #cyan
        '#66cc99', #lightgreen
        '#3399cc', #skyblue
        '#00cc66', #sea green
        '#33cc33', #green
        '#99cc00', #yellowgreen
        '#cccc00', #yellow
        '#cc6600', #orange
        '#cc6633', #peach
        '#cc3300', #dark orange
        '#cc6666', #coral
        '#cc0066', #hot pink
        '#cc0000', #red
        ]

COLOUR = ['#9933cc', #purple
            '#99cc00', #yellowgreen
            '#3399cc', #skyblue
            '#66cc99', #lightgreen
            '#ffff00', #yellow
            '#cc0066', #hot pink
            '#cc6600', #orange
            '#00cc66', #sea green
            '#6699cc', #bluetint
            '#cc6633', #peach
            '#33cc33', #green
            '#9966cc', #lilac
            '#3333cc', #blue
            '#cccc00', #gold
            '#cc0000', #red
            '#cc6666', #coral
            '#666666', #gray
            '#009999', #cyan
]

MARKERS = ['*', 'D' , 'H' , 'd' , 'h' , 'o' , 'p' , 's' , 'x']
graphNames = []
sampleIDs = []

def parse_rarefaction(lines):
    """Function for parsing rarefaction files specifically for use in
    make_rarefaction_plots.py"""
    col_headers = None
    result = []
    row_headers = []
    for line in lines:
        if line[0] == '#': continue
        if line[0] == '\t': #is header
            col_headers = map(strip, line.split('\t')[1:])
        else:
            entries = line.split('\t')
            try:
                result.append(map(float, entries[1:]))
            except(ValueError):
                temp = []
                for x in entries[1:]:
                    if x.strip() != 'n/a':
                        temp.append(float(x.strip()))
                    else:
                        temp.append(0.0)
                result.append(temp)
                
            row_headers.append(entries[0])
    rare_mat_raw = array(result)
    rare_mat_min = [rare_mat_raw[x][2:] for x in range(0,len(rare_mat_raw))]
    seqs_per_samp = [rare_mat_raw[x][0] for x in range(0,len(rare_mat_raw))]
    sampleIDs = col_headers[2:]
    rare_mat_trans = transpose(array(rare_mat_min)).tolist()
    return rare_mat_trans, seqs_per_samp, sampleIDs
    
def ave_seqs_per_sample(matrix, seqs_per_samp, sampleIDs):
    """Calculate the average for each sampleID across each number of seqs/sample"""
    ave_ser = {}
    temp_dict = {}
    for i,sid in enumerate(sampleIDs):
        temp_dict[sid] = {}
        for j,seq in enumerate(seqs_per_samp):
            try:
                temp_dict[sid][seq].append(matrix[i][j])
            except(KeyError):
                temp_dict[sid][seq] = []
                temp_dict[sid][seq].append(matrix[i][j])

    for sid in sampleIDs:
        ave_ser[sid] = []
        keys = temp_dict[sid].keys()
        keys.sort()
        for k in keys:
            ave_ser[sid].append(mean(array(temp_dict[sid][k]),0))
    return ave_ser

def is_max_category_ops(mapping, mapping_category):
    """Count how many unique values there are for the supplied mapping category
    and return true if all values are unique"""
    header = mapping[0][0]
    map_min = mapping[0][1:]
    num_samples = len(map_min)
    index = header.index(mapping_category)
    seen = set()
    
    for m in map_min:
        seen.update([m[index]])
        
    return (len(seen) == num_samples), len(seen)

def make_error_series(rare_mat, sampleIDs, mapping, mapping_category):
    """Create mean and error bar series for the supplied mapping category"""
    err_ser = dict()
    collapsed_ser = dict()
    header = mapping[0][0]
    map_min = mapping[0][1:]
    mapping_dict = dict()
    for m in map_min:
        mapping_dict[m[0]] = m[1:]
        
    seen = set()
    pre_err = {}
    category_index = header.index(mapping_category)
    
    for k in mapping_dict:
        try:
            test = rare_mat[k]
        except(KeyError):
            #err.append("SampleID " + k + " found in mapping but not in rarefaction file.\n")
            continue
        op = mapping_dict[k][category_index-1]
        if op not in seen:
            seen.update([op])
            pre_err[op] = []
        pre_err[op].append(rare_mat[k])
    
    ops = list(seen)
    
    for o in ops:
        min_len = 1000 #1e10000
        for series in pre_err[o]:
            series = [float(v) for v in series if v != 0]
            if len(series) < min_len:
                min_len = len(series)
        
        pre_err[o] = [x[:min_len] for x in pre_err[o]]
    
    cols = {}
    syms = {}
    colcycle = cycle(COLOUR)
    markcycle = cycle(MARKERS)
    for o in ops:
        cols[o] = colcycle.next()
        syms[o] = markcycle.next()
        opsarray = array(pre_err[o])
        mn = mean(opsarray, 0)
        collapsed_ser[o] = mn.tolist()
        stddev = std(opsarray, 0)
        err_ser[o] = stddev.tolist()
        
    return collapsed_ser, err_ser, ops, cols, syms

def get_overall_averages(rare_mat, sampleIDs):
    """Make series of averages of all values of seqs/sample for each sampleID"""
    overall_ave = dict();
    for s in sampleIDs:
        overall_ave[s] = mean(array(rare_mat[s]))
    return overall_ave

def plot_rarefaction(rare_mat, xaxis, sampleIDs, mapping, mapping_category):
    plt.gcf().set_size_inches(10,6)   
    plt.grid(color='gray', linestyle='-')
    
    yaxis, err, ops, colors, syms = make_error_series(rare_mat, sampleIDs, mapping, mapping_category)
    ops.sort()
    
    for o in ops:
        try:
            yaxis[o] = [float(v) for v in yaxis[o] if v != 'NA' and v != 0]
            l = o
            if len(o) > 20:
                l = l[:20] + '...'
            plt.errorbar(xaxis[:len(yaxis[o])], yaxis[o], yerr=err[o][:len(yaxis[o])], color=colors[o], label=l, marker=syms[o], markersize=4)
            # test = errorbar(xaxis[:len(yaxis[o])], yaxis[o], yerr=err[o][:len(yaxis[o])], color=colors[o], label=l, marker=syms[o], markersize=4)
        except(ValueError):
            print mapping_category
            print o

    ax = plt.gca()
    ax.set_axisbelow(True)
    ax.set_xlabel('Sequences Per Sample')
    #leg = plt.legend(markerscale=.3, ncol=int(len(ops)/12))
    return plt, ops, colors, syms

def save_plot(plot, filenm, rtype, title, itype, res, xmax, ymax, ops, cols, syms):
    plot.title(title)
    ax = plot.gca()
    ax.set_xlim((0,xmax))
    ax.set_ylim((0,ymax))
    ax.set_ylabel("Rarefaction Type: " + splitext(split(rtype)[1])[0])
    plot.savefig(filenm +'.'+itype, format=itype, dpi=res)
    plt.clf()
    if ops != None:
        c = 1
        if len(ops) > 12:
            c = int(len(ops)/12)
        i = 0
        for o in ops:
            plt.plot([0,0], [0,0], cols[o], label=o, marker=syms[o])
            i += 1
        plt.legend(markerscale=.3, ncol=c)
    plot.savefig(filenm +'_legend.'+itype, format=itype, dpi=res)
    
def make_plots(prefs):
    rarelines = []

    for r in prefs['rarefactions']:
        file_path = os.path.join(prefs['output_path'],splitext(split(r)[1])[0])
        os.makedirs(file_path)
        rare_mat_trans, seqs_per_samp, sampleIDs = parse_rarefaction(prefs['rarefactions'][r])

        xaxisvals = [float(x) for x in set(seqs_per_samp)]
        xaxisvals.sort()

        rare_mat_ave = ave_seqs_per_sample(rare_mat_trans, seqs_per_samp, sampleIDs)
        xmax = max(xaxisvals) + (xaxisvals[len(xaxisvals)-1] - xaxisvals[len(xaxisvals)-2])
        yoffset = 5 #parameterize?
        ymax = max([max(s) for s in rare_mat_ave.values()]) + yoffset
        overall_average = get_overall_averages(rare_mat_ave, sampleIDs)

        rarelines.append("#" + r + '\n')
        for s in sampleIDs:
            rarelines.append('%f'%overall_average[s] + '\n')
            
        for p in prefs['categories']:
            pr,ops,cols,syms = plot_rarefaction(rare_mat_ave, xaxisvals, sampleIDs, prefs['map'], p)
            filenm = file_path + '/'+ p
            graphNames.append(splitext(split(r)[1])[0] + '/'+p+"."+prefs['imagetype'])
            save_plot(pr, filenm, r, splitext(split(r)[1])[0] +': '+ p, prefs['imagetype'], prefs['resolution'], xmax, ymax, ops, cols, syms)
            plt.clf()

    tablelines = ['#SampleIDs\n']
    tablelines.extend([s + '\n' for s in sampleIDs])
    tablelines.extend(rarelines)
    return tablelines
    
def make_output_files(prefs, lines, qiime_dir):
    open(prefs['output_path'] + "/graphNames.txt",'w').writelines([f +'\n' for f in graphNames])
    open(prefs['output_path'] + "/rarefactionTable.txt",'w').writelines(lines)

    os.makedirs(prefs['output_path']+"/js")
    os.makedirs(prefs['output_path']+"/css")
    shutil.copyfile(qiime_dir+"/support_files/rarefaction_plots.html", prefs['output_path']+"/rarefaction_plots.html")
    shutil.copyfile(qiime_dir+"/support_files/js/rarefaction_plots.js", prefs['output_path']+"/js/rarefaction_plots.js")
    shutil.copyfile(qiime_dir+"/support_files/js/jquery.js", prefs['output_path']+"/js/jquery.js")
    shutil.copyfile(qiime_dir+"/support_files/js/jquery.dataTables.min.js", prefs['output_path']+"/js/jquery.dataTables.min.js")
    shutil.copyfile(qiime_dir+"/support_files/css/rarefaction_plots.css", prefs['output_path']+"/css/rarefaction_plots.css")
    shutil.copyfile(qiime_dir+"/support_files/qiime_header.png", prefs['output_path']+"/qiime_header.png")