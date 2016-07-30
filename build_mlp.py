#!/usr/bin/env python
# coding=utf-8
# 
# 0 : none
# 1 : black
# 2 : white
# 

import sys
import numpy as np
import chainer
from chainer import cuda, Function, gradient_check, report, training, utils, Variable
from chainer import datasets, iterators, optimizers, serializers
from chainer import Link, Chain, ChainList
import chainer.functions as F
import chainer.links as L
from chainer.training import extensions

gVec = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
gCol = ('A','B','C','D','E','F','G','H')
gRow = ('1','2','3','4','5','6','7','8')

class MLP(Chain):
    def __init__(self):
        super(MLP, self).__init__(
                l1=L.Linear(64, 100),
                l2=L.Linear(100, 100),
                l3=L.Linear(100, 65),
        )

    def __call__(self, x):
        h1 = F.relu(self.l1(x))
        h2 = F.relu(self.l2(h1))
        y = self.l3(h2)
        return y

class Classifier(Chain):
    def __init__(self, predictor):
        super(Classifier, self).__init__(predictor=predictor)

    def __call__(self, x, t):
        y = self.predictor(x)
        loss = F.softmax_cross_entropy(y, t)
        accuracy = F.accuracy(y, t)
        report({'loss': loss, 'accuracy': accuracy}, self)
        return loss


def print_board(board):
    for i in range(8):
        print board[i]

    print ""

def update_board(board, pos_str, clr):
    assert clr!=0, "stone color is not black or white."
    updated_board = [[0 for col in range(8)] for row in range(8)]
    rev_list = []
    pos = pos_str2pos_index(pos_str)
    for v in gVec:
        temp_list = []
        for i in range(1, 8):
            # out of board
            if pos[0]+v[0]*(i+1) > 7 or pos[1]+v[1]*(i+1) > 7 or\
               pos[0]+v[0]*(i+1) < 0 or pos[1]+v[1]*(i+1) < 0:
                continue

            if board[pos[0]+v[0]*i][pos[1]+v[1]*i] == (clr % 2 + 1):
                temp_list.append([pos[0]+v[0]*i, pos[1]+v[1]*i])

                if board[pos[0]+v[0]*(i+1)][pos[1]+v[1]*(i+1)] == clr:
                    for j in temp_list:
                        rev_list.append(j)

                    break
            else:
                break

    rev_list.append(pos)  # put stone at pos
    assert board[pos[0]][pos[1]] == 0, "put position is not empty."
    print "rev_list = " + str(rev_list)
    for i in range(0, 8):
        for j in range(0, 8):
            if [i, j] in rev_list:
                updated_board[i][j] = clr
            else:
                updated_board[i][j] = board[i][j]

    return updated_board

def who_is_winner(board):
    # ret : 0  draw
    #       1  black win
    #       2  white win
    ret = 0
    score_b = 0
    score_w = 0
    for i in range(0, 8):
        for j in range(0, 8):
            if board[i][j] == 1:
                score_b += 1
            elif board[i][j] == 2:
                score_w += 1

    if score_b > score_w:
        ret = 1
    elif score_b < score_w:
        ret = 2

    print "Black vs White : " + str(score_b) + " vs " + str(score_w)
    return ret

def pos_str2pos_index(pos_str):
    pos_index = []
    #print pos_str[0]
    #print pos_str[1]
    for i, c in enumerate(gRow):
        if pos_str[1] == c:
            pos_index.append(i)
    
    for i, c in enumerate(gCol):
        if pos_str[0] == c:
            pos_index.append(i)


    return pos_index

def pos_str2pos_index_flat(pos_str):
    pos_index = pos_str2pos_index(pos_str)
    index = pos_index[0] * 8 + pos_index[1]
    return index


#==== Main ====#
record_X = []    # MLP input (board list)
record_y = []    # MLP output(class(0-64) list)
temp_X = []
temp_y = []
temp2_X = []
temp2_y = []
board = []
row = []

argv = sys.argv
argc = len(argv)

if argc != 3:
    print 'Usage'
    print '    python ' + str(argv[0]) + ' <record_filename> <type>'
    print '        type : black'
    print '               black_win'
    print '               white'
    print '               white_win'
    quit()

# check type
build_type = ''
for t in ['black', 'black_win', 'white', 'white_win']:
    if argv[2] == t:
        build_type = t

if build_type == '':
    print 'record type is illegal.'
    quit()

#-- load record --#
f = open(argv[1], "r")
line_cnt = 1
for line in f:
    print 'Line Count = ' + str(line_cnt)
    idx = line.find("BO[8")
    if idx == -1:
        continue

    idx += 5
    # make board initial state
    for i in range(idx, idx+9*8):
        #print "i = " + str(i)
        if line[i] == '-':
            row.append(0)
        elif line[i] == 'O':
            row.append(2)
        elif line[i] == '*':
            row.append(1)

        if (i-idx)%9 == 8:
            board.append(row)
            row = []
            if len(board) == 8:
                break

    row = []
    print_board(board)
    # record progress of game
    i = idx+9*8+2
    while line[i] != ';':
        if (line[i] == 'B' or line[i] == 'W') and line[i+1] == '[':
            temp_X.append(board)
            pos_str = line[i+2] + line[i+3]
            #print pos_str
            if pos_str == "pa":    # pass
                temp_y.append(64)
                # board state is not change
                print_board(board)
                #print "y = 64"
                #print ""
            else:
                if line[i] == 'B':
                    clr = 1
                elif line[i] == 'W':
                    clr = 2
                else:
                    clr = 0
                    assert False, "Stone Color is illegal."

                pos_index_flat = pos_str2pos_index_flat(pos_str)
                temp_y.append(pos_index_flat)
                board = update_board(board, pos_str, clr)

            if (line[i] == 'B' and (build_type == 'black' or build_type == 'black_win')) or \
               (line[i] == 'W' and (build_type == 'white' or build_type == 'white_win')):
                temp2_X.append(temp_X[0])
                temp2_y.append(temp_y[0])
                print 'X = '
                print_board(temp_X[0])
                print 'y = ' + str(temp_y[0]) + ' (' + \
                               str(pos_str2pos_index(pos_str)) + ') ' + \
                               '(' + pos_str + ')'
                print ''

            temp_X = []
            temp_y = []
        
        i += 1

    print "End of game"
    print_board(board)

    winner = who_is_winner(board)
    if (winner == 1 and build_type == 'black_win') or \
       (winner == 2 and build_type == 'white_win') or \
       build_type == 'black' or build_type == 'white':
        record_X.extend(temp2_X)
        record_y.extend(temp2_y)

    #print record_X
    #print record_y
    board = []
    temp2_X = []
    temp2_y = []
    line_cnt += 1


#-- MLP model and Training --#
X = np.array(record_X, dtype=np.float32)
y = np.array(record_y, dtype=np.int32)

train = datasets.TupleDataset(X, y)
train_iter = iterators.SerialIterator(train, batch_size=100)

model = Classifier(MLP())
optimizer = optimizers.SGD()
optimizer.setup(model)

updater = training.StandardUpdater(train_iter, optimizer)
trainer = training.Trainer(updater, (1000, 'epoch'), out='result')

trainer.extend(extensions.ProgressBar())
trainer.run()

#-- save model --#
serializers.save_npz('reversi_model.npz', model)


#-- prediction example --#
X1_ = [[[0,0,0,0,0,0,0,0],\
        [0,0,0,0,0,0,0,0],\
        [0,0,0,0,0,0,0,0],\
        [0,0,0,2,1,0,0,0],\
        [0,0,0,1,2,0,0,0],\
        [0,0,0,0,0,0,0,0],\
        [0,0,0,0,0,0,0,0],\
        [0,0,0,0,0,0,0,0]]]

X1 = np.array(X1_, dtype=np.float32)
y1 = F.softmax(model.predictor(X1))
print "X1 = "
print_board(X1[0])
print "y1 = " + str(y1.data.argmax(1)) + '\n' 

X2_ = [[[0,0,0,0,0,0,0,0],\
        [0,0,0,0,0,0,0,0],\
        [0,0,2,2,2,0,0,0],\
        [0,0,2,1,1,1,0,0],\
        [0,2,2,2,1,1,0,0],\
        [0,0,2,1,0,0,0,0],\
        [0,0,0,0,0,0,0,0],\
        [0,0,0,0,0,0,0,0]]]

X2 = np.array(X2_, dtype=np.float32)
y2 = F.softmax(model.predictor(X2))
print "X2 = "
print_board(X2[0])
print "y2 = " + str(y2.data.argmax(1)) + '\n'



