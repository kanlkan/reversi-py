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

gVersion = "1.0.0"
gVec = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

class MainFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, wx.ID_ANY, 'Revresi :' + gVersion, size=(1050, 648+30))

        main_panel = wx.Panel(self, wx.ID_ANY, pos=(0,0), size=(648,648))
        self.main_panel = main_panel
        sub_panel_top = SubPanel(self, pos=(648,0), size=(400,445))
        self.sub_panel_top = sub_panel_top
        sub_panel_btm_left = SubPanel(self, pos=(648,450), size=(200,200))
        self.sub_panel_btm_left = sub_panel_btm_left
        sub_panel_btm_right = SubPanel(self, pos=(848,450), size=(200,200))
        self.sub_panel_btm_right = sub_panel_btm_right

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
        log_textctrl = wx.TextCtrl(sub_panel_top, wx.ID_ANY, size=(400,500), style=wx.TE_MULTILINE)
        self.log_textctrl = log_textctrl
        radio_button_array = ("Man vs Man", "Man vs Computer", "Computer vs Man", "Computer vs Computer")
        radio_box = wx.RadioBox(sub_panel_btm_left, wx.ID_ANY, "Game mode", choices=radio_button_array, style=wx.RA_VERTICAL)
        self.radio_box = radio_box
        start_game_button = wx.Button(sub_panel_btm_left, wx.ID_ANY, "START", size=(200,200))
        label_font = wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        score_label = wx.StaticText(sub_panel_btm_right, wx.ID_ANY, "SCORE", style=wx.TE_CENTER)
        score_black_label = wx.TextCtrl(sub_panel_btm_right, wx.ID_ANY, "", style=wx.TE_CENTER)
        score_white_label = wx.TextCtrl(sub_panel_btm_right, wx.ID_ANY, "", style=wx.TE_CENTER)
        self.score_black_label = score_black_label
        self.score_white_label = score_white_label
        score_label.SetFont(label_font)
        score_black_label.SetFont(label_font)
        score_black_label.SetBackgroundColour("#999999")
        score_white_label.SetFont(label_font)
        score_white_label.SetForegroundColour("white")
        score_white_label.SetBackgroundColour("#999999")

        sub_top_layout = wx.BoxSizer(wx.VERTICAL)
        sub_top_layout.Add(log_textctrl)
        sub_btm_left_layout = wx.BoxSizer(wx.VERTICAL)
        sub_btm_left_layout.Add(radio_box, flag=wx.GROW)
        sub_btm_left_layout.Add(start_game_button)
        sub_btm_right_layout = wx.BoxSizer(wx.VERTICAL)
        sub_btm_right_layout.Add(score_label)
        sub_btm_right_layout.Add(score_black_label)
        sub_btm_right_layout.Add(score_white_label)

        sub_panel_top.SetSizer(sub_top_layout)
        sub_panel_btm_left.SetSizer(sub_btm_left_layout)
        sub_panel_btm_right.SetSizer(sub_btm_right_layout)

        # Set initial state
        pass_flag = [0, 0]
        self.pass_flag = pass_flag
        player_score = [2 ,2]
        self.player_score = player_score
        rest = 64 - (player_score[0] + player_score[1])
        self.rest = rest
        now_color = "black"    # first palyer color is black
        self.now_color = now_color

        self.setInitialState()
       
        # Game mode 
        first_player  = "man"
        second_player = "man"
        self.first_player = first_player
        self.second_player = second_player
 
        # Bind main_panel event
        for i in range(0, 8):
            for j in range(0, 8):
                cell_array[i][j].Bind(wx.EVT_LEFT_UP, self.onLeftClick)
                cell_array[i][j].Bind(wx.EVT_MIDDLE_UP, self.onMiddleClick)
        
        # Bind sub_panels event
        radio_box.Bind(wx.EVT_RADIOBOX, self.onSelectGameMode)
        start_game_button.Bind(wx.EVT_BUTTON, self.onGameStart)

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
    def doComputer(self, my_color):
        pos_list = []
        gain_list = []
        pos_list, gain_list = self.scanPuttableCell(my_color)
        if len(pos_list) == 0:
            self.log_textctrl.AppendText("Pass the " + my_color + " stone computer's turn.\n")
            if my_color == "black":
                self.pass_flag[0] = 1
                self.now_color = "white"
            else:
                self.pass_flag[1] = 1
                self.now_color = "black"
            
            if self.pass_flag[0] == self.pass_flag[1]:
                self.gameEnd()
                return
            elif self.first_player == "computer" and self.second_player == "computer":
                self.doComputer(self.now_color)
            else:
                return

        if my_color == "black":
            self.pass_flag[0] = 0
        else:
            self.pass_flag[1] = 0
 
        put_pos = self.decideComputerNext(pos_list, gain_list)
        
        ret = self.putStone(put_pos, my_color)
        if ret == 0:
            if my_color == "black":
                self.pass_flag[0] = 0
                self.now_color = "white"
            else:
                self.pass_flag[1] = 0
                self.now_color = "black"
            self.vecScan(put_pos, my_color, 1)
            if self.rest == 0:
                self.gameEnd()
                return

            if self.first_player == "computer" and self.second_player == "computer":
                self.doComputer(self.now_color)
        else:
            print ("error! illegal path.")

    def decideComputerNext(self, pos_list, gain_list):
        print ("pos_list :" + str(pos_list))
        print ("gain_list:" + str(gain_list))
        
        # Insert a computer's AI here
        next_pos = pos_list[0]
        
        return next_pos

    def putStone(self, put_pos, my_color):
        pos_list, gain_list = self.scanPuttableCell(my_color)
        hit = 0
        for pos in pos_list:
            if pos == put_pos:
                hit = 1
                break

        if len(pos_list) == 0:
            return 1    # cannot put at all
        elif hit == 0:
            return 2    # cannot put a stone at put_pos.

        # put a stone at put_pos
        self.setCellState(put_pos, (0,0), my_color)
        self.rest -= 1
        if my_color == "black":
            self.player_score[0] += 1
        else:
            self.player_score[1] += 1
        self.updateScoreLabel()
        return 0

    def scanPuttableCell(self, my_color):
        pos_list = []
        gain_list = []
        for i in range(0, 8):
            for j in range(0, 8):
                ret = self.vecScan((i,j), my_color, 0)
                
                # ret => (is_hit, gain)
                if ret[0] == 1:
                    pos_list.append((i,j))
                    gain_list.append(ret[1])
        
        return pos_list, gain_list

    def vecScan(self, pos, my_color, reverse_on):
        rev_list = []
        temp_list = []
        gain = 0
        is_hit = 0
        if reverse_on == 0 and self.getCellState(pos,(0,0)) != "green":
            return 0, gain

        if my_color == "black":
            rev_color = "white"
        else:
            rev_color = "black"
            
        for v in gVec:
            temp_list = []
            for i in range(1, 8):
                if self.getCellState(pos,(v[0]*i,v[1]*i)) == rev_color:
                    temp_list.append(self.movePos(pos,(v[0]*i, v[1]*i)))
                    if self.getCellState(pos,(v[0]*i+v[0], v[1]*i+v[1])) == my_color:
                        is_hit = 1
                        for j in temp_list:
                            rev_list.append(j)
                        break
                else:
                    break
        
        if reverse_on == 1:
            self.log_textctrl.AppendText("put:" + str(pos) + ", "  + str(rev_list) + " to " + str(my_color) + "\n")
            for rev_pos in rev_list:
                self.setCellState(rev_pos, (0,0), my_color)
                if my_color == "black":
                    self.player_score[0] += 1
                    self.player_score[1] -= 1
                else:
                    self.player_score[1] += 1
                    self.player_score[0] -= 1
                self.updateScoreLabel()
        
        gain = len(rev_list)
        return is_hit, gain


    def movePos(self, pos, move):
        newpos = (pos[0]+move[0], pos[1]+move[1])
        return newpos

    def showCannotPutDlg(self):
        wx.MessageBox("Cannot put. Pass this turn.", "Warn", wx.OK)

    ## Events
    # Man
    def onLeftClick(self, event):
        obj = event.GetEventObject()
        pos= obj.pos_index
        print ("pos  = " + str(pos))
        print (self.getCellState(pos,(-1,-1))+" "+self.getCellState(pos,(0,-1))+" "+ self.getCellState(pos,(1,-1)))
        print (self.getCellState(pos,(-1,0))+" "+self.getCellState(pos,(0,0))+" "+ self.getCellState(pos,(1,0)))
        print (self.getCellState(pos,(-1,1))+" "+self.getCellState(pos,(0,1))+" "+ self.getCellState(pos,(1,1)))
        print ("")

        ret = self.putStone(pos, self.now_color)
        if ret == 0:
            self.vecScan(pos, self.now_color, 1)
            if self.now_color == "black":
                self.pass_flag[0] = 0
                self.now_color = "white"
            else:
                self.pass_flag[1] = 0
                self.now_color = "black"
            
        elif ret == 1:
            self.showCannotPutDlg()
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

        if self.rest == 0:
            self.gameEnd()
            return
        
        if self.first_player == "computer" or self.second_player == "computer":
            self.doComputer(self.now_color)

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
        self.setInitialState()
        for i in range(0,4):
            self.radio_box.EnableItem(i, False)
        if self.first_player == "computer":
            self.doComputer("black")

    def setInitialState(self):
        for i in range(0,8):
            for j in range(0,8):
                self.setCellState((i,j), (0,0), "green")

        self.setCellState((3,3), (0,0), "black")
        self.setCellState((3,4), (0,0), "white")
        self.setCellState((4,3), (0,0), "white")
        self.setCellState((4,4), (0,0), "black")
        self.pass_flag = [0, 0]
        self.player_score = [2, 2]
        self.rest = 64 - (self.player_score[0] + self.player_score[1])
        self.updateScoreLabel()
        self.now_color = "black"
        self.log_textctrl.Clear()

    def gameEnd(self):
        self.log_textctrl.AppendText("Game is end.\n")
        for i in range(0,4):
            self.radio_box.EnableItem(i, True)

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

