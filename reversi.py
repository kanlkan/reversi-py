#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wx
import sys

# Computer : white
# Man      : black

gVec = ((-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1))
gCellState = ("green", "black", "white")
gOutOfRange = 1000

class MainFrame(wx.Frame):
	def __init__(self):
		wx.Frame.__init__(self, None, wx.ID_ANY, 'Revrese', size=(648,648))

		main_panel = wx.Panel(self, wx.ID_ANY)

		# Panels arrangement
		cell_array = []
		self.cell_array = cell_array
		for i in range(7, -1, -1):
			for j in range(0, 8, 1):
				cell_array.append(CellPanel(main_panel, (81 * j, 81 * i), j+(7-i)*8 ))

		for i in range(0, 64):
			cell_array[i].Bind(wx.EVT_LEFT_UP, self.onLeftClick)
			cell_array[i].Bind(wx.EVT_RIGHT_UP, self.onRightClick)
			cell_array[i].Bind(wx.EVT_MIDDLE_UP, self.onMiddleClick)
			cell_array[i].Bind(wx.EVT_LEFT_DCLICK, self.onMiddleClick)

		# Set initial state
		cell_array[self.posToIdx((3,3))].state = gCellState[1]
		cell_array[self.posToIdx((3,3))].SetBackgroundColour(gCellState[1])
		cell_array[self.posToIdx((3,4))].state = gCellState[2]
		cell_array[self.posToIdx((3,4))].SetBackgroundColour(gCellState[2])
		cell_array[self.posToIdx((4,3))].state = gCellState[2]
		cell_array[self.posToIdx((4,3))].SetBackgroundColour(gCellState[2])
		cell_array[self.posToIdx((4,4))].state = gCellState[1]
		cell_array[self.posToIdx((4,4))].SetBackgroundColour(gCellState[1])

		pass_flag = 0
		self.pass_flag = pass_flag

		rest = 56
		self.rest = rest

	# man
	def onLeftClick(self, event):
		obj = event.GetEventObject()
		idx = obj.obj_id
		pos = self.idxToPos(idx)
		print "idx  = " + str(idx)
		print "pos  = " + str(pos)
		print self.getState(pos,(-1,1))+" "+self.getState(pos,(0,1))+" "+ self.getState(pos,(1,1))
		print self.getState(pos,(-1,0))+" "+self.getState(pos,(0,0))+" "+ self.getState(pos,(1,0))
		print self.getState(pos,(-1,-1))+" "+self.getState(pos,(0,-1))+" "+ self.getState(pos,(1,-1))
		print ""

		ret = self.doPut(0, idx)
		if ret == 0:
			self.pass_flag = 0
			self.doVecScan(self.idxToPos(idx), 0, 1)
			self.doComputer(1)
		elif ret == 1:
			if self.pass_flag == 0:
				self.ShowCannotPutDlg()
				print "Pass the player's turn."
				self.doComputer(1)
				self.pass_flag = 1
			else:
				print "Game is end."


	# for_debug
	def onRightClick(self, event):
		mode = 1
		while self.rest != 0:
			ret = self.doComputer(mode)
			if ret == 1:
				break
			else:
				mode += 1
				mode = mode % 2

	# for debug
	def onMiddleClick(self, event):
		obj = event.GetEventObject()
		idx = obj.obj_id
		if self.cell_array[idx].state == "green":
			self.cell_array[idx].state = "black"
			self.cell_array[idx].SetBackgroundColour("black")
		elif self.cell_array[idx].state == "black":
			self.cell_array[idx].state = "white"
			self.cell_array[idx].SetBackgroundColour("white")
		else:
			self.cell_array[idx].state = "green"
			self.cell_array[idx].SetBackgroundColour("green")

	# computer
	def doComputer(self, mode):
		pos_list = []
		gain_list = []
		pos_list, gain_list = self.doScan(mode)
		if len(pos_list) == 0:
			print "Pass the computer's turn."
			if self.pass_flag == 1:
				print "Game is end."
				return 1
			
			self.pass_flag = 1
			return 2 # Pass this turn

		self.pass_flag = 0
		idx = self.decideNextIdx(pos_list, gain_list)
		
		ret = self.doPut(mode, idx)
		if ret == 0:
			self.pass_flag = 0
			self.doVecScan(self.idxToPos(idx), mode, 1)
		elif ret == 1:
			if self.pass_flag == 0:
				self.ShowCannotPutDlg()
				print "Pass the computer's turn."
				self.pass_flag = 1
				return 2
			else:
				print "Game is end."
				return 1

		return 0

	def decideNextIdx(self, pos_list, gain_list):
		print "pos_list :" + str(pos_list)
		print "gain_list:" + str(gain_list)
		#idx = self.posToIdx(pos_list[0])
	
		tgt_gain = min(gain_list)
		#tgt_gain = max(gain_list)
		
		hitind = 0
		for p in pos_list:
			if p == (0,0) or p == (7,0) or p == (0,7) or p == (7,7):
				idx = self.posToIdx(p)
				return idx
			
		for p in pos_list:
			if p[0] == 0 or p[0] == 7 or p[1] == 0 or p[1] == 7:
				idx = self.posToIdx(p)
				return idx

		for p in pos_list:
			if tgt_gain == gain_list[hitind]:
				idx = self.posToIdx(p)
				break

			hitind += 1

		return idx

	def doPut(self, is_com, idx):
		pos_list, gain_list = self.doScan(is_com)
		hit = 0
		for pos in pos_list:
			if self.posToIdx(pos) == idx:
				hit = 1
				break

		if len(pos_list) == 0:
			return 1
		elif hit == 0:
			return 2

		self.cell_array[idx].state = gCellState[is_com + 1]
		self.cell_array[idx].SetBackgroundColour(gCellState[is_com + 1])
		self.rest -= 1
		return 0

	def doScan(self, is_com):
		pos_list = []
		gain_list = []
		for i in range(0, 64):
			nowpos = self.idxToPos(i)
			retval = self.doVecScan(nowpos, is_com, 0)
			if retval[0] == 1:
				pos_list.append(nowpos)
				gain_list.append(retval[1])
		
		return pos_list, gain_list

	def doVecScan(self, pos, is_com, reverse_on):
		rev_list = []
		temp_list = []
		gain = 0
		end = 0
		#print str(pos) + "," + self.getState(pos,(0,0))
		if reverse_on == 0 and self.getState(pos,(0,0)) != "green":
			return 0, gain

		if is_com == 0:
			hit_clr = "white"
			end_clr = "black"
			rev_clr = "black"
		else:
			hit_clr = "black"
			end_clr = "white"
			rev_clr = "white"
			
		for v in gVec:
			temp_list = []
			for i in range(1, 8):
				if self.getState(pos,(v[0]*i,v[1]*i)) == hit_clr:
					temp_list.append(self.posToIdx(self.movePos(pos,(v[0]*i, v[1]*i))))
					if self.getState(pos,(v[0]*i+v[0], v[1]*i+v[1])) == end_clr:
						end = 1
						for j in temp_list:
							rev_list.append(j)
						break
				else:
					break
		
		if reverse_on == 1:
			print "put:" + str(self.posToIdx(pos)) + ","  + str(rev_list) + "to " + str(rev_clr)
			for idx in rev_list:
				self.cell_array[idx].state = rev_clr
				self.cell_array[idx].BackgroundColour = rev_clr
				self.rest -= 1
		
		gain = len(rev_list)
		return end, gain


	def movePos(self, pos, move):
		newpos = (pos[0]+move[0], pos[1]+move[1])
		return newpos

	def getState(self, pos, offset):
		try:
			state = self.cell_array[self.posToIdx(self.movePos(pos, offset))].state
		except IndexError:
			state = "none "

		return state

	def posToIdx(self, pos):
		if pos[0] >= 0 and pos[0] < 8 and pos[1] >= 0 and pos[1] < 8:
			idx = pos[0] +  pos[1] * 8
		else:
			idx = gOutOfRange
		
		return idx

	def idxToPos(self, idx):
		if idx >= 0 and idx < 64:
			pos = (idx % 8, idx / 8)
		else:
			pos = (gOutOfRange, gOutOfRange)
		
		return pos

	def ShowCannotPutDlg(self):
		wx.MessageBox("Cannot put. Pass this turn.", "Warn", wx.OK)


class CellPanel(wx.Panel):
	def __init__(self, parent, pos, obj_id):
		wx.Panel.__init__(self, parent, pos=pos, size=(80,80))
		state = gCellState[0]
		self.state = state
		self.obj_id = obj_id
		self.SetBackgroundColour(gCellState[0])


if __name__ == "__main__":
	app = wx.App()
	frame = MainFrame().Show()
	app.MainLoop()

