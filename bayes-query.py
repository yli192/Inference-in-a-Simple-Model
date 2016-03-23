#! /usr/bin/python
import numpy as np
import itertools
from operator import mul
import re
from sys import argv, exit, stdout

if len(argv) < 4:
    print "usage: bayes_query.py network_filename cpd_filename lefthand_side righthand_side"
    exit(1)

if len(argv) == 5:
    network_file,cpd_file,lefthand_side,righthand_side=argv[1:]
else:
    network_file,cpd_file,lefthand_side=argv[1:]
    righthand_side=None

def findJointProb (rv_tuple,joint_dict): #dynamic marginalization over r.vs 1,2 and 3 rvs, there no is rhs!!
    jointP=0
    key_list=[]
    key_list_init=joint_dict.keys()
    for i in range(len(rv_tuple)):
                #print i
        if i != 0:
            key_list_init=key_list
        key_list=[]
        for key in key_list_init:
            if rv_tuple[i] in key: #i=0, the 1st atom
                key_list.append(key)
                #print key_list
    #print key_list
    if len(key_list) != 1: # a partial joint probability P(10,21)=P(MY,RN)
        for i in key_list:
            jointP += joint_dict[i]
            #print joint_dict[i]
    else:
        jointP = joint_dict[key_list[0]]
    return jointP

def productOfList(num_list, index=0, value=1):
    if index == len(num_list):
        return value
    else:
        return productOfList(num_list, index+1, value*num_list[index])

############################
#####input the network######
############################
network_file = open (network_file,'r')
totalNumofRVs = int(network_file.readline())
rv_names=[]
rv_values=[]
cardinality=[None] * totalNumofRVs #if there are 3 r.v.s, cardinality table is a 1xN array that encodes the number of possible values each node can take
for i in range(totalNumofRVs):
 line = network_file.readline()
 rv_names.append(line.split()[0])
 rv_values.append(line.split()[1]) #the possible values that a random variable can take
 cardinality[i] = rv_values[i].count(',') + 1 # the total number of possible values that a random variable can take
#print "Random Variable names:", rv_names
#print "Random Variable values:", rv_values
#print "num of possible values each r.v. can take:",cardinality
#create a table that encodes the dependencies of the nodes
dependency_table = np.zeros((totalNumofRVs,totalNumofRVs))
dependencies=network_file.readlines() # dependencies in plain text, e.g.,FluRate -> RoommateHasFlu
if dependencies[0].count('->') != 0:
    for line in dependencies:
        parent = line.split()[0]
        child = line.split()[2]
        dependency_table[rv_names.index(child),rv_names.index(parent)]=1
    network_file.close()
else:
    network_file.close()
#print "Dependency table:", "\n", dependency_table

# convert input text to tuples in the form ('rvnamervvalue','rvnamervvalue'),e.g.('00','10')
if lefthand_side.count(',') != 0:
    lefthand_side_list=lefthand_side.split(',')
else:
    lefthand_side_list=[lefthand_side]
#print "Left hand side=",lefthand_side_list

if righthand_side != None:

    if righthand_side.count(',') != 0:
        righthand_side_list=righthand_side.split(',')
    else:
        righthand_side_list=[righthand_side]
        #print "Right hand side=",righthand_side_list
#form inout_lhs from lefthand_side_list; convert input list to ('00','10') tuples
    Input_rhs = [None] * len(righthand_side_list)
    for i in range(len(righthand_side_list)):
        Input_rhs[i] = righthand_side_list[i].split('=')
        Rhs_rv_idx=rv_names.index(Input_rhs[i][0])
        Rhs_rv_value_list=rv_values[Rhs_rv_idx].split(',')
        #print Rhs_rv_value_list
        Rhs_value_idx=Rhs_rv_value_list.index(Input_rhs[i][1])
        Input_rhs[i]=str(Rhs_rv_idx)+str(Rhs_value_idx)

    input_rhs=tuple(atom for atom in Input_rhs)
    #print "RHS in number:",input_rhs

Input_lhs = [None] * len(lefthand_side_list)
for i in range(len(lefthand_side_list)):
    Input_lhs[i] = lefthand_side_list[i].split('=')
    Lhs_rv_idx=rv_names.index(Input_lhs[i][0])
    Lhs_rv_value_list=rv_values[Lhs_rv_idx].split(',')
    Lhs_value_idx=Lhs_rv_value_list.index(Input_lhs[i][1])
    Input_lhs[i]=str(Lhs_rv_idx)+str(Lhs_value_idx)

input_lhs=tuple(atom for atom in Input_lhs)
#print "LHS in number:",input_lhs

############################
#####input the cpds#########
############################
cpd_file = open (cpd_file, 'r')
cpd_dict={}
for line in cpd_file:
    cpd_line=line.split()
    LHS = cpd_line[0].split('=')
    LHSRvNameIdx = rv_names.index(LHS[0])
    lhs_rv_value_list=rv_values[LHSRvNameIdx].split(',')
    LHSRvValueIdx = lhs_rv_value_list.index(LHS[1])
    lhs_idx = [LHSRvNameIdx,LHSRvValueIdx]
    LHS_IDX = ''.join(str(x) for x in lhs_idx)

    if cpd_line[1].count(',') !=0 :
        RHS = cpd_line[1].split(',')
        RHSRvNameIdx = [None] * len(RHS)
        RHSRvValueIdx = [None] * len(RHS)
        rhs_idx = []
        rhs_rv_value_list = [] * len(RHS)
        for i in range(len(RHS)):
            RHSRvNameIdx[i] = rv_names.index(RHS[i].split('=')[0])
            rhs_rv_value_list=rv_values[RHSRvNameIdx[i]].split(',')
            RHSRvValueIdx[i] = rhs_rv_value_list.index(RHS[i].split('=')[1])
            rhs_idx.append(RHSRvNameIdx[i])
            rhs_idx.append(RHSRvValueIdx[i])
    else:
        RHS = cpd_line[1]
        RHSRvNameIdx = rv_names.index(RHS.split('=')[0])
        rhs_rv_value_list=rv_values[RHSRvNameIdx].split(',')
        RHSRvValueIdx = rhs_rv_value_list.index(RHS.split('=')[1])
        rhs_idx = [RHSRvNameIdx,RHSRvValueIdx]

    RHS_IDX=''.join(str(x) for x in rhs_idx)
    key=[LHS_IDX,'|',RHS_IDX]  #here encodes conditional sign
    KEY=''.join(str(x) for x in key)
    #print KEY,cpd_line[2]
    cpd_dict.update({KEY:cpd_line[2]})

#########################################################
#####multiply the cpds to get joint distribution#########
#########################################################

L=[] # a list of rv names and their possible values, each rv is followed by its possible value
for i in range(len(rv_names)):
    for j in range(len(rv_values[i].split(','))):
        L.append(str(i)+str(j))

allCombinations = itertools.combinations(L,totalNumofRVs)
#find the parent(s) of the child
parent_idx =[]
for j in range(totalNumofRVs):
    rowChild=dependency_table[j,:].tolist() #the corresponding row of the child
    parent_idx.append([i for i, x in enumerate(rowChild) if x == 1])
for i in range(totalNumofRVs):
    if parent_idx[i]==[]:
        for j in range(cardinality[i]):
            cpd_dict.update({str(i)+str(j):1.0/cardinality[i]})

cpd = []
joint_dict={}
#generate combinations for rvs and their corresponding values
comb_list_init=list(allCombinations)
final_list=[]
current_list=comb_list_init
for i in range(totalNumofRVs):
    if i !=0:
        current_list=final_list
    final_list=[]
    for combination in current_list:
        if combination[i][0] == str(i):
            final_list.append(combination)

joint_prob_list=[None]*totalNumofRVs
#print joint_prob_list
for combination in final_list:
    prob_key=list(combination)
    for i in combination:
        for k in range(totalNumofRVs):
            LHS=[combination[k]]
            RHS=[]
            for j in range(len(parent_idx[k])):
                key=[item for item in combination if int(item[0]) == parent_idx[k][j] ]
                RHS.append(key)
                RHS= list(itertools.chain(*RHS))
                LHS= list(itertools.chain(*LHS))
                rhs=''.join(str(e) for e in RHS)
                lhs=''.join(str(e) for e in LHS)
                if not rhs:
                    a=[lhs]
                    a=''.join(a)
                else:
                    a=[lhs,'|',rhs]
                    a=''.join(a)
                prob_key[k]=a
            joint_prob_list[k]=cpd_dict[prob_key[k]]
    joint_prob=reduce(lambda x, y: float(x)*float(y), joint_prob_list)
    joint_dict.update({combination:joint_prob})
#########################################################
######marginalize and conditionalize based on input query
#########################################################
if righthand_side != None:
    joint=input_lhs+input_rhs
else:
    joint=input_lhs
numerator=0
denominator=1
#######calculate the joint probabiltiy first (lhs+rhs), assign it to the numerator######
numerator=findJointProb(joint,joint_dict)
if righthand_side == None:
    finalProb=numerator
else:
    denominator=findJointProb(input_rhs,joint_dict)
    finalProb=numerator/denominator
print '%.13e'% finalProb
