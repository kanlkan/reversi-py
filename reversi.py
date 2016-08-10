#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 
# Reversi.py - Reversi by wxPython
#
# Board       : green
# Play first  : black
# Play second : white
# Out of Range: none
#
# Man      : man
# Computer : computer
#
import wx
import random
import os
import sys
import numpy as np
import chainer
from chainer import cuda, Function, gradient_check, report, training, utils, Variable
from chainer import datasets, iterators, optimizers, serializers
from chainer import Link, Chain, ChainList
import chainer.functions as F
import chainer.links as L
from chainer.training import extensions

gVersion = "1.2.0"
gVec = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
gMaxDepth = 10
gGain = [( 30, -12,  0, -1, -1,  0, -12,  30), \
         (-12, -15, -3, -3, -3, -3, -15, -12), \
         (  0,  -3,  0, -1, -1,  0,  -3,   0), \
         ( -1,  -3, -1, -1, -1, -1,  -3,  -1), \
         ( -1,  -3, -1, -1, -1, -1,  -3,  -1), \
         (  0,  -3,  0, -1, -1,  0,  -3,   0), \
         (-12, -15, -3, -3, -3, -3, -15, -12), \
         ( 30, -12,  0, -1, -1,  0, -12,  30)]

#gGain = [(120, -20, 20,  5,  5, 20, -20, 120), \
#         (-20, -40, -5, -5, -5, -5, -40, -20), \
#         ( 20,  -5, 15,  3,  3, 15,  -5,  20), \
#         (  5,  -5,  3,  3,  3,  3,  -5,   5), \
#         (  5,  -5,  3,  3,  3,  3,  -5,   5), \
#         ( 20,  -5, 15,  3,  3, 15,  -5,  20), \
#         (-20, -40, -5, -5, -5, -5, -40, -20), \
#         (120, -20, 20,  5,  5, 20, -20, 120)]

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


gMlpModelBlack = Classifier(MLP())
gMlpModelWhite = Classifier(MLP())

class MainFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, wx.ID_ANY, 'Revresi :' + gVersion, size=(1250, 648+30))

        main_panel = wx.Panel(self, wx.ID_ANY, pos=(0,0), size=(648,648))
        self.main_panel = main_panel
        sub_panel_top = SubPanel(self, pos=(648,0), size=(400,445))
        self.sub_panel_top = sub_panel_top
        sub_panel_btm_left1 = SubPanel(self, pos=(648,450), size=(200,120))
        self.sub_panel_btm_left1 = sub_panel_btm_left1
        sub_panel_btm_left2 = SubPanel(self, pos=(648,570), size=(200,80))
        self.sub_panel_btm_left2 = sub_panel_btm_left2
        sub_panel_btm_right01 = SubPanel(self, pos=(848,450), size=(200,40))
        self.sub_panel_btm_right01 = sub_panel_btm_right01
        sub_panel_btm_right02 = SubPanel(self, pos=(848,490), size=(95,50))
        self.sub_panel_btm_right02 = sub_panel_btm_right02
        sub_panel_btm_right03 = SubPanel(self, pos=(948,490), size=(95,50))
        self.sub_panel_btm_right03 = sub_panel_btm_right03
        sub_panel_btm_right04 = SubPanel(self, pos=(848,550), size=(60,30))
        self.sub_panel_btm_right04 = sub_panel_btm_right04
        sub_panel_btm_right05 = SubPanel(self, pos=(908,550), size=(140,30))
        self.sub_panel_btm_right05 = sub_panel_btm_right05
        sub_panel_btm_right06 = SubPanel(self, pos=(848,585), size=(60,30))
        self.sub_panel_btm_right06 = sub_panel_btm_right06
        sub_panel_btm_right07 = SubPanel(self, pos=(908,585), size=(60,30))
        self.sub_panel_btm_right07 = sub_panel_btm_right07
        sub_panel_btm_right08 = SubPanel(self, pos=(968,585), size=(60,30))
        self.sub_panel_btm_right08 = sub_panel_btm_right08
        sub_panel_btm_right09 = SubPanel(self, pos=(848,615), size=(60,35))
        self.sub_panel_btm_right09 = sub_panel_btm_right09
        sub_panel_btm_right10 = SubPanel(self, pos=(908,615), size=(60,35))
        self.sub_panel_btm_right10 = sub_panel_btm_right10
        sub_panel_btm_right11 = SubPanel(self, pos=(968,615), size=(60,35))
        self.sub_panel_btm_right11 = sub_panel_btm_right11

        sub2_panel01 = SubPanel(self, pos=(1050,0), size=(200,15))
        self.sub2_panel01 = sub2_panel01
        sub2_panel02 = SubPanel(self, pos=(1050,20), size=(200,15))
        self.sub2_panel02 = sub2_panel02
        sub2_panel03 = SubPanel(self, pos=(1050,40), size=(200,35))
        self.sub2_panel03 = sub2_panel03
        sub2_panel04 = SubPanel(self, pos=(1050,80), size=(200,15))
        self.sub2_panel04 = sub2_panel04
        sub2_panel05 = SubPanel(self, pos=(1050,100), size=(200,35))
        self.sub2_panel05 = sub2_panel05
        sub2_panel06 = SubPanel(self, pos=(1050,160), size=(200,15))
        self.sub2_panel06 = sub2_panel06
        sub2_panel07 = SubPanel(self, pos=(1050,180), size=(200,15))
        self.sub2_panel07 = sub2_panel07
        sub2_panel08 = SubPanel(self, pos=(1050,200), size=(200,35))
        self.sub2_panel08 = sub2_panel08
        sub2_panel09 = SubPanel(self, pos=(1050,240), size=(200,15))
        self.sub2_panel09 = sub2_panel09
        sub2_panel10 = SubPanel(self, pos=(1050,260), size=(200,35))
        self.sub2_panel10 = sub2_panel10
        
        
        # Cells arrangement in main_panel
        cell_array = [[0 for i in range(8)] for j in range(8)]
        self.cell_array = cell_array
        cell_layout = [[0 for i in range(8)] for j in range(8)]
        self.cell_layout = cell_layout
        cell_state = [[0 for i in range(8)] for j in range(8)]
        self.cell_state = cell_state
        for i in range(0, 8):
            for j in range(0, 8):
                cell_array[i][j] = CellPanel(main_panel, (81*i, 81*j), (i,j))
                self.setCellState((i,j), (0,0), "green")
                stext = wx.StaticText(cell_array[i][j], wx.ID_ANY, "(" + str(i) + ", " + str(j) + ")")
                stext.SetForegroundColour("#999999")
                cell_layout[i][j] = wx.BoxSizer(wx.VERTICAL)
                cell_layout[i][j].Add(stext)
                cell_array[i][j].SetSizer(cell_layout[i][j])

        # Components in sub_panels
        log_textctrl = wx.TextCtrl(sub_panel_top, wx.ID_ANY, size=(400,450), style=wx.TE_MULTILINE)
        self.log_textctrl = log_textctrl
        radio_button_array = ("Man vs Man", "Man vs Computer A", "Computer A vs Man", "Computer A vs Computer B")
        radio_box = wx.RadioBox(sub_panel_btm_left1, wx.ID_ANY, "Game mode", choices=radio_button_array, style=wx.RA_VERTICAL)
        self.radio_box = radio_box
        start_game_button = wx.Button(sub_panel_btm_left2, wx.ID_ANY, "START", size=(200,80))
        label_font = wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        score_label = wx.StaticText(sub_panel_btm_right01, wx.ID_ANY, "SCORE", style=wx.TE_CENTER)
        score_black_label = wx.TextCtrl(sub_panel_btm_right02, wx.ID_ANY, "", size=(90,45), style=wx.TE_CENTER)
        score_white_label = wx.TextCtrl(sub_panel_btm_right03, wx.ID_ANY, "", size=(90,45), style=wx.TE_CENTER)
        self.score_black_label = score_black_label
        self.score_white_label = score_white_label
        score_label.SetFont(label_font)
        score_black_label.SetFont(label_font)
        score_black_label.SetBackgroundColour("#999999")
        score_white_label.SetFont(label_font)
        score_white_label.SetForegroundColour("white")
        score_white_label.SetBackgroundColour("#999999")
        auto_loop_textctrl = wx.TextCtrl(sub_panel_btm_right04, wx.ID_ANY, size=(60,30))
        self.auto_loop_textctrl = auto_loop_textctrl
        loop_exe_button = wx.Button(sub_panel_btm_right05, wx.ID_ANY, "Comp vs Comp Loop", size=(135,30))
        self.loop_exe_button = loop_exe_button
        comp_a_win_label = wx.TextCtrl(sub_panel_btm_right06, wx.ID_ANY, "COMP-A", pos=(0,5), size=(60,20), style=wx.TE_CENTER)
        comp_b_win_label = wx.TextCtrl(sub_panel_btm_right07, wx.ID_ANY,  "COMP-B", pos=(0,5), size=(60,20), style=wx.TE_CENTER)
        draw_label = wx.TextCtrl(sub_panel_btm_right08, wx.ID_ANY, "DRAW", pos=(0,5), size=(60,20), style=wx.TE_CENTER)
        comp_a_win_label.SetBackgroundColour("#999999")
        comp_b_win_label.SetBackgroundColour("#999999")
        draw_label.SetBackgroundColour("#999999")
        comp_a_win_num_label = wx.TextCtrl(sub_panel_btm_right09, wx.ID_ANY, "", pos=(0,5), size=(60,20), style=wx.TE_CENTER)
        comp_b_win_num_label = wx.TextCtrl(sub_panel_btm_right10, wx.ID_ANY,  "", pos=(0,5), size=(60,20), style=wx.TE_CENTER)
        draw_num_label = wx.TextCtrl(sub_panel_btm_right11, wx.ID_ANY, "", pos=(0,5), size=(60,20), style=wx.TE_CENTER)
        self.comp_a_win_num_label = comp_a_win_num_label
        self.comp_b_win_num_label = comp_b_win_num_label
        self.draw_num_label = draw_num_label
        comp_a_win_num_label.SetBackgroundColour("#999999")
        comp_b_win_num_label.SetBackgroundColour("#999999")
        draw_num_label.SetBackgroundColour("#999999")

        # Components in sub2_panels
        label_font = wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        mlp_model_label = wx.StaticText(sub2_panel01, wx.ID_ANY, "MLP model setting")
        mlp_model_label.SetFont(label_font)
        mlp_for_black_label = wx.StaticText(sub2_panel02, wx.ID_ANY, "for black")
        mlp_for_black_label.SetFont(label_font)
        mlp_for_black_text = wx.TextCtrl(sub2_panel03, wx.ID_ANY, "model_black_win.npz", size=(180,30))
        self.mlp_for_black_text = mlp_for_black_text
        mlp_for_white_label = wx.StaticText(sub2_panel04, wx.ID_ANY, "for white")
        mlp_for_white_label.SetFont(label_font)
        mlp_for_white_text = wx.TextCtrl(sub2_panel05, wx.ID_ANY, "model_white_win.npz", size=(180,30))
        self.mlp_for_white_text = mlp_for_white_text
        comp_ai_label = wx.StaticText(sub2_panel06, wx.ID_ANY, "Computer AI setting")
        comp_ai_label.SetFont(label_font)
        comp_ai_a_label = wx.StaticText(sub2_panel07, wx.ID_ANY, "Computer A")
        comp_ai_a_label.SetFont(label_font)
        comp_ai_elem = ("MLP", "1st Gain Max", "Min Max 3", "Random")
        comp_ai_a_cb = wx.ComboBox(sub2_panel08, wx.ID_ANY, "MLP", choices=comp_ai_elem, style=wx.CB_READONLY)
        self.comp_ai_a_cb = comp_ai_a_cb
        comp_ai_b_label = wx.StaticText(sub2_panel09, wx.ID_ANY, "Computer B")
        comp_ai_b_label.SetFont(label_font)
        comp_ai_b_cb = wx.ComboBox(sub2_panel10, wx.ID_ANY, "MLP", choices=comp_ai_elem, style=wx.CB_READONLY)
        self.comp_ai_b_cb = comp_ai_b_cb
        
        # Game mode 
        first_player  = "man"
        second_player = "man"
        self.first_player = first_player
        self.second_player = second_player
 
        # Set initial state
        pass_flag = [0, 0]
        self.pass_flag = pass_flag
        player_score = [2 ,2]
        self.player_score = player_score
        now_color = "black"    # first palyer color is black
        self.now_color = now_color
        comp_ai = 0 
        self.comp_ai = comp_ai
        match_record = ""
        self.match_record = match_record
        
        self.setInitialState()
        black_pos_list = [(3,3),(4,4)]
        white_pos_list = [(3,4),(4,3)]
        log_on = True
        self.log_on = log_on
        state_storage_list = []
        self.state_storage_list = state_storage_list
        for i in range(0, gMaxDepth):
            state_storage_list.append(StateStorage(self.pass_flag, self.player_score, self.now_color, self.comp_ai, black_pos_list, white_pos_list))

        # Bind main_panel event
        for i in range(0, 8):
            for j in range(0, 8):
                cell_array[i][j].Bind(wx.EVT_LEFT_UP, self.onLeftClick)
                cell_array[i][j].Bind(wx.EVT_MIDDLE_UP, self.onMiddleClick)
        
        # Bind sub_panels event
        radio_box.Bind(wx.EVT_RADIOBOX, self.onSelectGameMode)
        start_game_button.Bind(wx.EVT_BUTTON, self.onGameStart)
        loop_exe_button.Bind(wx.EVT_BUTTON, self.onCompVsCompLoop)

    def setCellState(self, pos, ofst, state):
        self.cell_array[pos[0]+ofst[0]][pos[1]+ofst[1]].state = state
        self.cell_array[pos[0]+ofst[0]][pos[1]+ofst[1]].SetBackgroundColour(state)
        self.Refresh()

    def getCellState(self, pos, ofst):
        if (pos[0]+ofst[0]) < 8 and (pos[0]+ofst[0]) >= 0 and (pos[1]+ofst[1]) < 8 and (pos[1]+ofst[1]) >= 0:
            state = self.cell_array[pos[0]+ofst[0]][pos[1]+ofst[1]].state
        else:
            state = "none "

        return state

    def updateScoreLabel(self):
        self.score_black_label.SetValue(str(self.player_score[0]))
        self.score_white_label.SetValue(str(self.player_score[1]))
        self.Refresh

    # computer's turn
    def doComputer(self, go_next_computer):
        pos_list = []
        gain_list = []
        self.comp_ai *= -1
        pos_list, gain_list = self.scanPuttableCell()
        put_pos = self.decideComputerNext(pos_list, gain_list)
        print "put_pos = " + str(put_pos)
        if len(put_pos) == 0:
            self.log_textctrl.AppendText("Pass the " + self.now_color + " stone computer's turn.\n")
            if self.now_color == "black":
                self.match_record += "B[pass//]"
                self.pass_flag[0] = 1
                self.now_color = "white"
            else:
                self.match_record += "W[pass//]"
                self.pass_flag[1] = 1
                self.now_color = "black"
            
            if self.pass_flag[0] == self.pass_flag[1]:
                self.gameEnd()
                return
            elif self.first_player == "computer" and self.second_player == "computer":
                self.doComputer(go_next_computer)
                return
            else:
                return

        if self.now_color == "black":
            self.pass_flag[0] = 0
        else:
            self.pass_flag[1] = 0
 
        self.putComputerStone(put_pos, go_next_computer)

    def putComputerStone(self, put_pos, go_next_computer):
        ret = self.putStone(put_pos)
        if ret == 0:
            self.vecScan(put_pos, True)
            str_put_pos = self.posToStrPos(put_pos)
            if self.now_color == "black":
                self.match_record += ("B[" + str_put_pos + "//]")
                self.pass_flag[0] = 0
                self.now_color = "white"
            else:
                self.match_record += ("W[" + str_put_pos + "//]")
                self.pass_flag[1] = 0
                self.now_color = "black"
            
            if self.player_score[0] + self.player_score[1] == 64:
                if go_next_computer == True:
                    self.gameEnd()
                return 1

            if self.first_player == "computer" and self.second_player == "computer" and go_next_computer == True:
                self.doComputer(go_next_computer)
                
            return 0
        else:
            print ("error! illegal path.")
            return 2

    def posToStrPos(self, pos):
        ret = ""
        for i, c in enumerate (['A','B','C','D','E','F','G','H']):
            if i == pos[0]:
                ret += c
                break

        for i in range(1,9):
            if i == (pos[1] + 1):
                ret += str(i)
                break

        return ret

    def decideComputerNext(self, pos_list, gain_list):
        print ("pos_list :" + str(pos_list))
        print ("gain_list:" + str(gain_list))
        print "thinking ..."
        # Insert a computer's AI here
        if self.comp_ai >= 0:    # comp_ai == 0 => vs Man mode
            comp_ai_a_str = self.comp_ai_a_cb.GetValue()
            if comp_ai_a_str == "MLP":
                next_pos = self.computerAi_Mlp(pos_list, gain_list)
            elif comp_ai_a_str == "1st Gain Max":
                next_pos = self.computerAi_1stGainMax(pos_list, gain_list)
            elif comp_ai_a_str == "Min Max 3":
                next_pos = self.computerAi_MinMax_3(pos_list, gain_list)
            elif comp_ai_a_str == "Random":
                next_pos = self.computerAi_Random(pos_list, gain_list)
            
            self.log_textctrl.AppendText("debug : AI = A turn.\n")
        else:
            comp_ai_b_str = self.comp_ai_b_cb.GetValue()
            if comp_ai_b_str == "MLP":
                next_pos = self.computerAi_Mlp(pos_list, gain_list)
            elif comp_ai_b_str == "1st Gain Max":
                next_pos = self.computerAi_1stGainMax(pos_list, gain_list)
            elif comp_ai_b_str == "Min Max 3":
                next_pos = self.computerAi_MinMax_3(pos_list, gain_list)
            elif comp_ai_b_str == "Random":
                next_pos = self.computerAi_Random(pos_list, gain_list)
 
            self.log_textctrl.AppendText("debug : AI = B turn.\n")
        
        print "thinking finised."
        return next_pos

    def computerAi_Random(self, pos_list, gain_list):
        if len(pos_list) == 0:
            return []

        index = random.randint(0, len(pos_list)-1)
        return pos_list[index]

    def computerAi_1stGainMax(self, pos_list, gain_list):
        if len(pos_list) == 0:
            return []

        index_list = []
        max_gain = max(gain_list)
        for i, val in enumerate(gain_list):
            if max_gain == val:
                index_list.append(i)

        tgt = random.randint(0, len(index_list)-1)
        return pos_list[index_list[tgt]]

    def computerAi_MinMax_3(self, pos_list, gain_list):
        if len(pos_list) == 0:
            return []

        value = []
        update_pos_list = []
        
        self.log_on = False 
        value = self.minMax(2, 2, pos_list, gain_list)
        for i, pos in enumerate(pos_list):
            if max(value) == value[i]:
                update_pos_list.append(pos)

        self.log_on = True
        tgt = random.randint(0, len(update_pos_list)-1)
        return update_pos_list[tgt]

    def minMax(self, depth, max_depth, pos_list, gain_list):  # depth > 0
        value = []
        next_value = []
        next_pos_list = []
        next_gain_list = []
        self.backUpAllState(self.state_storage_list[depth])
        for pos in pos_list:
            ret =  self.putComputerStone(pos, False)
            next_pos_list, next_gain_list = self.scanPuttableCell()
            #print str(depth) + str(", ") + str(next_gain_list)
            if (depth > 1):
                next_value = self.minMax(depth-1, max_depth, next_pos_list, next_gain_list)
                if len(next_value) == 0:
                    value.append(0)
                elif (max_depth - depth) % 2 == 0:
                    value.append(min(next_value))
                else:
                    value.append(max(next_value))
            else:
                if len(next_gain_list) == 0:
                    value.append(0)
                elif (max_depth - depth) % 2 == 0:
                    value.append(min(next_gain_list))
                else:
                    value.append(max(next_gain_list))

            self.restoreAllState(self.state_storage_list[depth])

        #print "depth, value = " + str(depth) + ", " + str(value)
        return value

    def computerAi_Mlp(self, pos_list, gain_list):
        # make input(board state)
        board = []
        row = []
        for i in range(0,8):
            for j in range(0,8):
                if self.getCellState([j,i], (0,0)) == "green":
                    row.append(0)
                elif self.getCellState([j,i], (0,0)) == "black":
                    row.append(1)
                elif self.getCellState([j,i], (0,0)) == "white":
                    row.append(2)

            board.append(row)
            row = []

        X = np.array([board], dtype=np.float32)

        # get output
        if self.now_color == "black":
            y = F.softmax(gMlpModelBlack.predictor(X))
        else:
            y = F.softmax(gMlpModelWhite.predictor(X))
        
        put_pos_flat = y.data.argmax(1)
        print "put_pos_flat = " + str(put_pos_flat)

        # convert pos index
        if put_pos_flat[0] == 64:  # pass
            put_pos = []
        else:
            put_pos_col = put_pos_flat[0] % 8
            put_pos_row = put_pos_flat[0] / 8
            put_pos = (put_pos_col, put_pos_row)

        # judge illegal move or not
        if len(pos_list) == 0 and len(put_pos) == 0: # 'PASS' successful.
            put_pos = []
        elif len(pos_list) == 0 and len(put_pos) != 0:
            sys.stderr.write("Illegal move! : Cannot put stone but AI cannot select 'PASS'.\n")
            put_pos = []
        elif len(pos_list) != 0 and len(put_pos) == 0:
            sys.stderr.write("Illegal move! : Cannot 'PASS' this turn but AI selected it.\n")
            put_pos = pos_list[0]
        elif not(put_pos in pos_list):
            sys.stderr.write("Illegal move! : Cannot put stone at AI selected position.\n")
            put_pos = pos_list[0]

        return put_pos

    def backUpAllState(self, storage):
        storage.black_pos_list = []
        storage.white_pos_list = []
        storage.pass_flag    = [self.pass_flag[0], self.pass_flag[1]]
        storage.player_score = [self.player_score[0], self.player_score[1]]
        storage.now_color    = self.now_color
        storage.comp_ai      = self.comp_ai * 1
        for i in range(0,8):
            for j in range(0,8):
                if self.cell_array[i][j].state == "black":
                    storage.black_pos_list.append((i,j))
                elif self.cell_array[i][j].state == "white":
                    storage.white_pos_list.append((i,j))

    def restoreAllState(self, storage):
        self.pass_flag    = [storage.pass_flag[0], storage.pass_flag[1]]
        self.player_score = [storage.player_score[0], storage.player_score[1]]
        self.now_color    = storage.now_color
        self.comp_ai      = storage.comp_ai * 1
        self.updateScoreLabel()
        
        for i in range(0,8):
            for j in range(0,8):
                self.setCellState((i,j), (0,0), "green")
        
        for pos in storage.black_pos_list:
            self.setCellState(pos, (0,0), "black")
        for pos in storage.white_pos_list:
            self.setCellState(pos, (0,0), "white")

    def putStone(self, put_pos):
        pos_list, gain_list = self.scanPuttableCell()
        hit = 0
        print "pos_list(putStone) = " + str(pos_list)
        print "put_pos(putStone) = " + str(put_pos)
        for pos in pos_list:
            if pos == put_pos:
                hit = 1
                break

        if len(pos_list) == 0:
            return 1    # cannot put at all
        elif hit == 0:
            return 2    # cannot put a stone at put_pos.

        # put a stone at put_pos
        self.setCellState(put_pos, (0,0), self.now_color)
        if self.now_color == "black":
            self.player_score[0] += 1
        else:
            self.player_score[1] += 1
        self.updateScoreLabel()
        return 0

    def scanPuttableCell(self):
        pos_list = []
        gain_list = []
        for i in range(0, 8):
            for j in range(0, 8):
                ret = self.vecScan((i,j), False)
                
                # ret => (is_hit, gain)
                if ret[0] == 1:
                    pos_list.append((i,j))
                    gain_list.append(ret[1])
        
        return pos_list, gain_list

    def vecScan(self, pos, reverse_on):
        rev_list = []
        temp_list = []
        gain = 0
        is_hit = 0
        if reverse_on == 0 and self.getCellState(pos,(0,0)) != "green":
            return 0, gain

        if self.now_color == "black":
            rev_color = "white"
        else:
            rev_color = "black"
            
        for v in gVec:
            temp_list = []
            for i in range(1, 8):
                if self.getCellState(pos,(v[0]*i,v[1]*i)) == rev_color:
                    temp_list.append(self.movePos(pos,(v[0]*i, v[1]*i)))
                    if self.getCellState(pos,(v[0]*i+v[0], v[1]*i+v[1])) == self.now_color:
                        is_hit = 1
                        for j in temp_list:
                            rev_list.append(j)
                        break
                else:
                    break
        
        if reverse_on == True:
            if self.log_on == True:
                self.log_textctrl.AppendText("put:" + str(pos) + ", "  + str(rev_list) + " to " + str(self.now_color) + "\n")
            for rev_pos in rev_list:
                self.setCellState(rev_pos, (0,0), self.now_color)
                if self.now_color == "black":
                    self.player_score[0] += 1
                    self.player_score[1] -= 1
                else:
                    self.player_score[1] += 1
                    self.player_score[0] -= 1
                self.updateScoreLabel()
        
        gain = self.calcGain(pos, rev_list)
        return is_hit, gain

    def calcGain(self, pos, rev_list):
        ret_gain = 0
        ret_gain += gGain[pos[0]][pos[1]]

        for rev_pos in rev_list:
            ret_gain += gGain[rev_pos[0]][rev_pos[1]]

        return ret_gain

    def movePos(self, pos, move):
        newpos = (pos[0]+move[0], pos[1]+move[1])
        return newpos

    def showWarnDlg(self, message):
        wx.MessageBox(message, "Warn", wx.OK)

    ## Events
    # Man
    def onLeftClick(self, event):
        obj = event.GetEventObject()
        pos= obj.pos_index
        print ("")
        print ("pos  = " + str(pos))
        print (self.getCellState(pos,(-1,-1))+" "+self.getCellState(pos,(0,-1))+" "+ self.getCellState(pos,(1,-1)))
        print (self.getCellState(pos,(-1,0))+" "+self.getCellState(pos,(0,0))+" "+ self.getCellState(pos,(1,0)))
        print (self.getCellState(pos,(-1,1))+" "+self.getCellState(pos,(0,1))+" "+ self.getCellState(pos,(1,1)))
        print ("")

        ret = self.putStone(pos)
        if ret == 0:
            self.vecScan(pos, True)
            if self.now_color == "black":
                self.pass_flag[0] = 0
                self.now_color = "white"
            else:
                self.pass_flag[1] = 0
                self.now_color = "black"
        elif ret == 1:
            self.showWarnDlg("Cannot put. Pass this turn.")
            self.log_textctrl.AppendText("Pass the " + self.now_color + " stone player.\n")
            
            if self.now_color == "black":
                self.pass_flag[0] = 1
                self.now_color = "white"
            else:
                self.pass_flag[1] = 1
                self.now_color = "black"
            
            if self.pass_flag[0] == self.pass_flag[1]:
                self.gameEnd()
                return
        else:
            return

        if self.player_score[0] + self.player_score[1] == 64:
            self.gameEnd()
            return
        
        if self.first_player == "computer" or self.second_player == "computer":
            self.doComputer(True)

    # for debug - toggle cell state manually
    def onMiddleClick(self, event):
        obj = event.GetEventObject()
        pos = obj.pos_index
        if self.cell_array[pos[0]][pos[1]].state == "green":
            self.cell_array[pos[0]][pos[1]].state = "black"
            self.cell_array[pos[0]][pos[1]].SetBackgroundColour("black")
        elif self.cell_array[pos[0]][pos[1]].state == "black":
            self.cell_array[pos[0]][pos[1]].state = "white"
            self.cell_array[pos[0]][pos[1]].SetBackgroundColour("white")
        else: 
            self.cell_array[pos[0]][pos[1]].state = "green"
            self.cell_array[pos[0]][pos[1]].SetBackgroundColour("green")

        self.Refresh()

    def onRightClick(self, event):
        pass

    def onSelectGameMode(self, event):
        obj = event.GetEventObject()
        if self.radio_box.GetSelection() == 0:
            self.first_player = "man"
            self.second_player = "man"
        elif self.radio_box.GetSelection() == 1:
            self.first_player = "man"
            self.second_player = "computer"
        elif self.radio_box.GetSelection() == 2:
            self.first_player = "computer"
            self.second_player = "man"
        else:
            self.first_player = "computer"
            self.second_player = "computer"

    def onGameStart(self, event):
        global gMlpModelBlack
        global gMlpModelWhite

        self.setInitialState()
        for i in range(0,4):
            self.radio_box.EnableItem(i, False)
        
        if self.comp_ai_a_cb.GetValue() == "MLP" or self.comp_ai_b_cb.GetValue() == "MLP":
            serializers.load_npz(self.mlp_for_black_text.GetValue(), gMlpModelBlack)
            serializers.load_npz(self.mlp_for_white_text.GetValue(), gMlpModelWhite)

        if self.first_player == "computer":
            self.doComputer(True)

    def onCompVsCompLoop(self, event):
        loop_max = self.auto_loop_textctrl.GetValue()
        if loop_max == "":
            self.showWarnDlg("Set loop count.")
            return
        
        if self.radio_box.GetSelection() != 3:
            self.showWarnDlg("Select \"Computer vs Computer\".")
            return

        
        loop_max = int(loop_max)
        print loop_max
        comp_a_win_num = 0
        comp_b_win_num = 0
        draw_num = 0
        self.comp_a_win_num_label.SetValue("0")
        self.comp_b_win_num_label.SetValue("0")
        self.draw_num_label.SetValue("0")
        
        # match record file check
        if os.path.exists("./record.log"):
            os.remove("./record.log")

        for loop_cnt in range(0,loop_max):
            if self.comp_ai_a_cb.GetValue() == "MLP" or self.comp_ai_b_cb.GetValue() == "MLP":
                serializers.load_npz(self.mlp_for_black_text.GetValue(), gMlpModelBlack)
                serializers.load_npz(self.mlp_for_white_text.GetValue(), gMlpModelWhite)

            self.setInitialState()
            if self.comp_ai < 0:
                black_computer = "A"
            else:
                black_computer = "B"

            for i in range(0,4):
                self.radio_box.EnableItem(i, False)
            
            self.doComputer(True)
            
            score_black = self.score_black_label.GetValue()
            score_white = self.score_white_label.GetValue()
            if int(score_black) == int(score_white):
                draw_num += 1
            elif (int(score_black) > int(score_white) and black_computer == "A") or \
                 (int(score_black) < int(score_white) and black_computer == "B"):
                comp_a_win_num += 1
            else:
                comp_b_win_num += 1

            self.outputRecord()

        self.comp_a_win_num_label.SetValue(str(comp_a_win_num))
        self.comp_b_win_num_label.SetValue(str(comp_b_win_num))
        self.draw_num_label.SetValue(str(draw_num))
        
    def setInitialState(self):
        for i in range(0,8):
            for j in range(0,8):
                self.setCellState((i,j), (0,0), "green")

        self.setCellState((3,3), (0,0), "white")
        self.setCellState((3,4), (0,0), "black")
        self.setCellState((4,3), (0,0), "black")
        self.setCellState((4,4), (0,0), "white")
        self.pass_flag = [0, 0]
        self.player_score = [2, 2]
        self.updateScoreLabel()
        self.now_color = "black"
        self.log_textctrl.Clear()
        self.match_record = "(;[]BO[8 -------- -------- -------- ---O*--- ---*O--- -------- -------- -------- *]"
        if self.first_player == "computer" and self.second_player == "computer":
            self.comp_ai = random.choice([-1,1])
        else:
            self.comp_ai = 0

    def gameEnd(self):
        self.log_textctrl.AppendText("Game is end.\n")
        self.log_textctrl.AppendText("")
        for i in range(0,4):
            self.radio_box.EnableItem(i, True)

    def outputRecord(self):
        f = open('./record.log', 'a')
        f.write(self.match_record + ';)\n')


class StateStorage():
    def __init__(self, pass_flag, player_score, now_color, comp_ai, black_pos_list, white_pos_list):
        self.pass_flag = pass_flag
        self.player_score = player_score
        self.now_color = now_color
        self.black_pos_list = black_pos_list
        self.white_pos_list = white_pos_list
        self.comp_ai = comp_ai


class SubPanel(wx.Panel):
    def __init__(self, parent, pos, size):
        wx.Panel.__init__(self, parent, pos=pos, size=size)


class CellPanel(wx.Panel):
    def __init__(self, parent, pos, pos_index):
        wx.Panel.__init__(self, parent, pos=pos, size=(80,80))
        self.pos_index = pos_index
        state = "green"
        self.state = state


if __name__ == "__main__":
    app = wx.App()
    frame = MainFrame().Show()
    app.MainLoop()

