# -*- coding: utf-8 -*-
# @Author: Jie Yang from SUTD
# @Date:   2016-Jan-06 17:11:59
# @Last Modified by:   Jie Yang,     Contact: jieynlp@gmail.com
# @Last Modified time: 2018-03-05 17:41:03
#!/usr/bin/env python
# coding=utf-8

from Tkinter import *
from ttk import *  # Frame, Button, Label, Style, Scrollbar
import ttk
import codecs
import Tkinter as tk
import tkFileDialog
import tkFont
import re
import os, io
import yaml
from collections import deque
import pickle
import os.path
import platform
from utils.recommend import *
import tkMessageBox


class Example(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.Version = ""
        self.OS = platform.system().lower()
        self.parent = parent
        self.fileName = ""
        self.debug = True
        self.colorAllChunk = True
        self.recommendFlag = True
        self.history = deque(maxlen=20)
        self.remarkHistory = deque()
        self.currentContent = deque(maxlen=1)
        self.pressCommand = {
            'a': "Artifical",
            'b': "Event",
            'c': "Fin-Concept",
            'd': "Location",
            'e': "Organization",
            'f': "Person",
            'g': "Sector",
            'h': "Other"
        }
        self.allKey = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self.controlCommand = {'q': "unTag", 'ctrl+z': 'undo'}
        self.labelEntryList = []
        self.shortcutLabelList = []
        # default GUI display parameter
        if len(self.pressCommand) > 20:
            self.textRow = len(self.pressCommand)
        else:
            self.textRow = 20
        self.textColumn = 5
        self.tagScheme = "BMES"
        self.onlyNP = False  ## for exporting sequence
        self.keepRecommend = True
        '''
        self.seged: for exporting sequence, if True then split words with space, else split character without space
        for example, if your data is segmentated Chinese (or English) with words seperated by a space, you need to set this flag as true
        if your data is Chinese without segmentation, you need to set this flag as False
        '''
        self.seged = False  ## False for non-segmentated Chinese, True for English or Segmented Chinese
        self.configFile = "config"
        self.entityRe = r'\[\@.*?\#.*?\*\](?!\#)'
        self.insideNestEntityRe = r'\[\@\[\@(?!\[\@).*?\#.*?\*\]\#'
        self.recommendRe = r'\[\$.*?\#.*?\*\](?!\#)'
        self.goldAndrecomRe = r'\[\@.*?\#.*?\*\](?!\#)'
        if self.keepRecommend:
            self.goldAndrecomRe = r'\[[\@\$)].*?\#.*?\*\](?!\#)'

        self.combox_lst = []
        self.remark_file = "remark.yml"
        if os.path.exists(self.remark_file):
            with codecs.open(self.remark_file, "r", encoding="utf-8") as fd:
                self.flags = yaml.load(fd)

            self.crt_1_lst = self.flags.keys()
            self.crt_1_class = self.crt_1_lst[0]
            first_class_options = StringVar()
            first_class_options.set(tuple(self.crt_1_lst))
            self.first_class_options = first_class_options
            self.combox_lst.append({
                "idx": 0,
                "handler": None,
                "text": "大类",
                "cur": self.crt_1_class, # 当前值
                "lst": self.crt_1_lst,  # 当前完整序列
                "options": self.first_class_options  # 当前控件用数据源
            })
            
            self.crt_2_lst = self.flags[self.crt_1_class].keys()
            self.crt_2_class = self.crt_2_lst[0]
            second_class_options = StringVar()
            second_class_options.set(tuple(self.crt_2_lst))
            self.second_class_options = second_class_options
            self.combox_lst.append({
                "idx": 1,
                "handler": None,
                "text": "中类",
                "cur": self.crt_2_class,   # 当前值
                "lst": self.crt_2_lst,  # 当前完整序列
                "options": self.second_class_options  # 当前控件用数据源
            })

            self.crt_3_lst = self.flags[self.crt_1_class][self.crt_2_class].keys()
            self.crt_3_class = self.crt_3_lst[0]
            third_class_options = StringVar()
            third_class_options.set(tuple(self.crt_3_lst))
            self.third_class_options = third_class_options
            self.combox_lst.append({
                "idx": 2,
                "handler": None,
                "text": "小类",
                "cur": self.crt_3_class, # 当前值
                "lst": self.crt_3_lst,  # 当前完整序列
                "options": self.third_class_options  # 当前控件用数据源
            })

            self.crt_remark_orig = self.flags[self.crt_1_class][self.crt_2_class][self.crt_3_class]
            if self.crt_remark_orig is None:
                self.crt_remark_orig = []
            self.crt_remark = self.crt_remark_orig + ['添加', ]
        else:
            print "未找到标记文件"
            return

        self.crt_selected_area = []
        self.crt_mark = ""
        self.popup_widget = None
        ## configure color
        self.entityColor = "SkyBlue1"
        self.lastRemarkColor = "SkyBlue1"
        self.insideNestEntityColor = "light slate blue"
        self.recommendColor = 'lightgreen'
        self.remarkColor = 'lightgreen'
        self.selectColor = 'light salmon'
        self.textFontStyle = "Times"
        self.initUI()

    def initUI(self):

        self.parent.title(self.Version)
        self.pack(fill=BOTH, expand=True)

        for idx in range(0, self.textColumn):
            self.columnconfigure(idx, weight=2)
        # self.columnconfigure(0, weight=2)
        self.columnconfigure(self.textColumn + 2, weight=1)
        self.columnconfigure(self.textColumn + 4, weight=1)
        for idx in range(0, 16):
            self.rowconfigure(idx, weight=1)

        self.lbl = Label(self, text="未打开任何文件")
        self.lbl.grid(sticky=W, pady=4, padx=5)
        self.fnt = tkFont.Font(
            family=self.textFontStyle,
            size=self.textRow,
            weight="bold",
            underline=0)
        self.text = Text(
            self, font=self.fnt, selectbackground=self.selectColor)
        self.text.grid(
            row=1,
            column=0,
            columnspan=self.textColumn,
            rowspan=self.textRow,
            padx=12,
            sticky=E + W + S + N)

        self.sb = Scrollbar(self)
        self.sb.grid(
            row=1,
            column=self.textColumn,
            rowspan=self.textRow,
            padx=0,
            sticky=E + W + S + N)
        self.text['yscrollcommand'] = self.sb.set
        self.sb['command'] = self.text.yview
        # self.sb.pack()

        self.ctrl_group = LabelFrame(self)
        
        # self.combox_group.config(borderwidth=10, background='red')
        self.ctrl_group.grid(row=1, column=self.textColumn + 1,
                             columnspan=2, 
                             rowspan=2,
                             # sticky=E + W + S + N,
                             padx=5,
                            #  ipadx=20,
                       )

        abtn = Button(self.ctrl_group, text="打开文件", command=self.onOpen)
        abtn.grid(row=0, column=0)

        style = ttk.Style()
        style.configure("C.TButton", foreground="#32cd32")
        self.recButton = Button(self.ctrl_group, text="自动同步", style="C.TButton", command=self.setInRecommendModel)
        # recButton.config(style="C.TButton")
        self.recButton.grid(row=0, column=1)

        # noRecButton = Button(
        #     self, text="退出同步", command=self.setInNotRecommendModel)
        # noRecButton.grid(row=0, column=self.textColumn + 3)

        # ubtn = Button(self, text="ReMap", command=self.renewPressCommand)
        # ubtn.grid(row=1, column=self.textColumn + 1)

        exportbtn = Button(
             self.ctrl_group, text="输出结果", command=self.generateSequenceFile)
        exportbtn.grid(row=1, column=0)

        cbtn = Button(self.ctrl_group, text="退出", command=self.quit)
        cbtn.grid(row=1, column=1)

        style = ttk.Style()
        style.configure("C.TLabelframe", 
                         background='red',
                         borderwidth=0, bordercolor='#00FF00')

        self.combox_group = LabelFrame(self)
        
        # self.combox_group.config(borderwidth=10, background='red')
        self.combox_group.grid(row=3, column=self.textColumn + 1,
                               columnspan=2,
                               rowspan=3
                               # sticky=E + W + S + N,
                            #    padx=5
                       )
        # self.combox_group.config(style="C.TLabelframe")

        combox_row = 0
        combox_col = 0
        self.class_handler = []
        for i in self.combox_lst:
            first_calss_label = Label(self.combox_group, text=i.get("text"))
            first_calss_label.grid(row=combox_row, column=combox_col,
                                   sticky=E )
            
            first_class = Combobox(self.combox_group, textvariable=i.get("options"), width=10, state='readonly')
            first_class['values'] = i.get("lst")
            first_class.current(0)
            first_class.grid(row=combox_row, column=combox_col + 1,
                            sticky=W, padx=0)
            first_class.idx = i.get("idx")
            first_class.bind("<<ComboboxSelected>>", self.tt)
            combox_row += 1
            i['handler'] = first_class
            self.class_handler.append(first_class)
            # combox_col += 1

        style = ttk.Style()
        style.configure("Black.TLabelframe", font=("黑体", 100, 'bolder'))
        self.btn_group = LabelFrame(self, text="特征量", style="Black.TLabelframe")
        self.btn_group.grid(row=6, column=self.textColumn + 1,
                       columnspan=2, sticky='W'
                       )
        
        col = row = 0
        for i in self.crt_remark:
            # Button(self.btn_group, text=i, command=self.set_cur_mark).grid(column=col%3, row=row)
            btn = Button(self.btn_group, text=i)
            if i == "添加":
                btn.bind('<Button-1>', self.popup)
            else:
                btn.bind('<Button-1>', self.set_cur_mark)
            btn.grid(column=col%3, row=row)
            col += 1
            if col and col%3 == 0:
                row += 1
        
        #self.btn_group.children[-1].bind('<Button-1>', self.popup)

        # self.cursorName = Label(
        #     self,
        #     text="Cursor: ",
        #     foreground="Blue",
        #     font=(self.textFontStyle, 14, "bold"))
        # self.cursorName.grid(row=9, column=self.textColumn + 1, pady=4)
        self.cursorIndex = Label(
            self,
            text=("row: %s col: %s" % (0, 0)),
            foreground="red",
            font=(self.textFontStyle, 12))
        self.cursorIndex.grid(row=self.textRow + 1, column=self.textColumn + 2, pady=4)

        # self.RecommendModelName = Label(
        #     self,
        #     text="RModel: ",
        #     foreground="Blue",
        #     font=(self.textFontStyle, 14, "bold"))
        # self.RecommendModelName.grid(
        #     row=12, column=self.textColumn + 1, pady=4)
        # self.RecommendModelFlag = Label(
        #     self,
        #     text=str(self.recommendFlag),
        #     foreground="red",
        #     font=(self.textFontStyle, 14, "bold"))
        # self.RecommendModelFlag.grid(
        #     row=13, column=self.textColumn + 1, pady=4)

        # recommend_value = StringVar()
        # recommend_value.set("R")
        # a = Radiobutton(self.parent,  text="Recommend",   width=12, variable=recommend_value, value="R")
        # # a.grid(row =1 , column = 2)
        # a.pack(side='left')
        # b = Radiobutton(self.parent, text="NotRecommend",   width=12,  variable=recommend_value, value="N")
        # # b.grid(row =1 , column = 3)
        # b.pack(side='left')

        lbl_entry = Label(self, text="Command:")
        lbl_entry.grid(
            row=self.textRow + 1, sticky=E + W + S + N, pady=4, padx=4)
        self.entry = Entry(self)
        self.entry.grid(
            row=self.textRow + 1,
            columnspan=self.textColumn + 1,
            rowspan=1,
            sticky=E + W + S + N,
            pady=4,
            padx=80)
        self.entry.bind('<Return>', self.returnEnter)

        # for press_key in self.pressCommand.keys():
        # for idx in range(0, len(self.allKey)):
        #     press_key = self.allKey[idx]

        #     # self.text.bind(press_key, lambda event, arg=press_key:self.textReturnEnter(event,arg))
        #     self.text.bind(press_key, self.textReturnEnter)
        #     simplePressKey = "<KeyRelease-" + press_key + ">"
        #     self.text.bind(simplePressKey, self.deleteTextInput)
        #     if self.OS != "windows":
        #         controlPlusKey = "<Control-Key-" + press_key + ">"
        #         self.text.bind(controlPlusKey, self.keepCurrent)
        #         altPlusKey = "<Command-Key-" + press_key + ">"
        #         self.text.bind(altPlusKey, self.keepCurrent)

        self.text.bind('<Control-Key-z>', self.pop_his)
        ## disable the default  copy behaivour when right click. For MacOS, right click is button 2, other systems are button3
        self.text.bind('<Button-2>', self.rightClick)
        self.text.bind('<Button-3>', self.rightClick)

        self.text.bind('<Double-Button-1>', self.doubleLeftClick)
        self.text.bind('<ButtonRelease-1>', self.singleLeftClick)

        # self.setMapShow()

        self.enter = Button(self, text="Enter", command=self.returnButton)
        self.enter.grid(row=self.textRow + 1, column=self.textColumn + 1)

    def popup(self, event):
        # if self.popup_widget:
        #     self.popup_widget.destroy()
        #     self.popup_widget = Tk()
        # else:
        if not self.popup_widget:
            self.popup_widget = Tk()
            self.popup_widget.title("新建特征量")
            popup_frame = Frame(self.popup_widget)
            popup_frame.pack(fill=BOTH, expand=True)
            popup_widget = self.popup_widget
            popup_widget.geometry("+200+200")
            Label(popup_frame, text="输入特征量名称").grid(row=0, column=0)
            self.add_input = Entry(popup_frame)
            self.add_input.grid(row=0, column=1)
            Button(popup_frame, text="提交", command=self.get_input).grid(row=1, column=1, sticky=E + W + S + N)
            Button(popup_frame, text="取消", command=self.cancel_popup).grid(row=1, column=0, sticky=E + W + S + N)
        

    def cancel_popup(self):
        """
            弹出框取消操作
        """
        self.popup_widget.destroy()
        self.popup_widget = None

    
    def get_input(self):
        """
             接受输入参数
        """
        new_flag = self.add_input.get().strip()
        self.popup_widget.destroy()
        self.popup_widget = None
        if not new_flag:
            return
        self.crt_remark_orig.append(new_flag)
        # print(self.flags)
        self.flags_dumps(self.flags)
        self._update_remark()
        
    def flags_dumps(self, flags_dict):
        """
            保存标记文件
        """
        def _loop_all(crt_data, fd, level=0):
            crt_lev = level
            if isinstance(crt_data, dict):
                for k, v in crt_data.items():
                    # print("  " * crt_lev + k + ":")
                    line_content = u"  " * crt_lev + unicode(k) + u":\n"
                    fd.write(unicode(line_content))
                    _loop_all(v, fd, crt_lev+1)
            elif isinstance(crt_data, list):
                for i in crt_data:
                    line_content = u"  " * crt_lev + u"- " + unicode(i) + u"\n"
                    fd.write(line_content)
                    # print("  " * crt_lev + "-" + i)
                    

        fd = codecs.open(self.remark_file, "w", encoding='utf-8')
        _loop_all(flags_dict, fd)
        
        fd.close()

    def tt(self, event):
        from_widget = event.widget
        curt_data = from_widget.get()
        curt_widget_idx = from_widget.idx
        # print(self.combox_lst[curt_widget_idx])
        self._update_combox(curt_widget_idx, curt_data)

    def _update_combox(self, idx, key_name):
        """
            更新下拉菜单
        """
        if self.combox_lst[idx]['cur'] == key_name:
            return
        
        self.combox_lst[idx]['cur'] = key_name
        if idx == 0:
            self.combox_lst[1]['lst'] = self.flags[key_name].keys()
            self.combox_lst[1]['cur'] = self.flags[key_name].keys()[0]
            self.combox_lst[1]['options'].set(tuple(self.combox_lst[1]['lst']))
            self.combox_lst[1]['handler']['values'] = self.combox_lst[1]['lst']
            self.combox_lst[1]['handler'].current(0)

            self.combox_lst[2]['lst'] = self.flags[key_name][self.combox_lst[1]['cur']].keys()
            self.combox_lst[2]['cur'] = self.flags[key_name][self.combox_lst[1]['cur']].keys()[0]
            self.combox_lst[2]['options'].set(tuple(self.combox_lst[2]['lst']))
            self.combox_lst[2]['handler']['values'] = self.combox_lst[2]['lst']
            self.combox_lst[2]['handler'].current(0)
        elif idx == 1:
            self.combox_lst[2]['lst'] = self.flags[self.combox_lst[0]['cur']][key_name].keys()
            self.combox_lst[2]['cur'] = self.flags[self.combox_lst[0]['cur']][key_name].keys()[0]
            self.combox_lst[2]['options'].set(tuple(self.combox_lst[2]['lst']))
            self.combox_lst[2]['handler']['values'] = self.combox_lst[2]['lst']
            self.combox_lst[2]['handler'].current(0)
        else:
            pass
        self._update_remark()

    def _update_remark(self):
        self.crt_remark_orig = self.flags[self.combox_lst[0]['cur']][self.combox_lst[1]['cur']][self.combox_lst[2]['cur']]
        if self.crt_remark_orig is None:
            self.crt_remark_orig = []
        self.crt_remark = self.crt_remark_orig + ['添加',]
        col = row = 0
        for k,v in self.btn_group.children.items():
            v.destroy()
        for i in self.crt_remark:
            btn = Button(self.btn_group, text=i)
            if i == "添加":
                btn.bind('<Button-1>', self.popup)
            else:
                btn.bind('<Button-1>', self.set_cur_mark)
            btn.grid(column=col%3, row=row)
            col += 1
            if col and col%3 == 0:
                row += 1

    def set_cur_mark(self, event):
        """
            设置当前标记
        """
        green_style = ttk.Style()
        green_style.configure("G.TButton", foreground="#32cd32")
        black_style = ttk.Style().configure("B.TButton", foreground="black")
        for k,v in self.btn_group.children.items():
            v.config(style='')
        event.widget.config(style='G.TButton')
        curt_data = event.widget['text']
        self.crt_mark = curt_data

    ## cursor index show with the left click
    def singleLeftClick(self, event):
        if self.debug:
            print "Action Track: singleLeftClick"
        cursor_index = self.text.index(INSERT)
        row_column = cursor_index.split('.')
        cursor_text = ("row: %s col: %s" % (row_column[0], row_column[-1]))
        self.cursorIndex.config(text=cursor_text)

        try:
            selected_txt = self.text.selection_get()
            self.selected_txt = selected_txt
            self.push_his()
            self.executeCursorCommand('a')
            self.setCurColor()
            
        except Exception as e:
            pass
        

    ## TODO: select entity by double left click
    def doubleLeftClick(self, event):
        if self.debug:
            print "Action Track: doubleLeftClick"
        #
        # cursor_index = self.text.index(INSERT)
        # start_index = ("%s - %sc" % (cursor_index, 5))
        # end_index = ("%s + %sc" % (cursor_index, 5))
        # self.text.tag_add('SEL', '1.0',"end-1c")

    ## Disable right click default copy selection behaviour
    def rightClick(self, event):
        if self.debug:
            print "Action Track: rightClick"
        try:
            firstSelection_index = self.text.index(SEL_FIRST)
            cursor_index = self.text.index(SEL_LAST)
            content = self.text.get('1.0', "end-1c").encode('utf-8')
            self.writeFile(self.fileName, content, cursor_index)
        except TclError:
            pass

    def setInRecommendModel(self):
        self.recommendFlag = not self.recommendFlag

        style = ttk.Style()
        if self.recommendFlag:
            style.configure("C.TButton", foreground="#32cd32")
        else:
            style.configure("C.TButton", foreground="red")
        self.recButton.config(style='C.TButton')
        # self.RecommendModelFlag.config(text=str(self.recommendFlag))
        # tkMessageBox.showinfo("Recommend Model",
        #                       "Recommend Model has been activated!")

    # def setInNotRecommendModel(self):
    #     self.recommendFlag = False
    #     self.RecommendModelFlag.config(text=str(self.recommendFlag))
    #     content = self.getText()
    #     content = removeRecommendContent(content, self.recommendRe)
    #     self.writeFile(self.fileName, content, '1.0')
    #     tkMessageBox.showinfo("Recommend Model",
    #                           "Recommend Model has been deactivated!")

    def onOpen(self):
        ftypes = [('all files', '.*'), ('text files', '.txt'), ('ann files',
                                                                '.ann')]
        dlg = tkFileDialog.Open(self, filetypes=ftypes)
        # file_opt = options =  {}
        # options['filetypes'] = [('all files', '.*'), ('text files', '.txt')]
        # dlg = tkFileDialog.askopenfilename(**options)
        fl = dlg.show()
        if fl != '':
            self.text.delete("1.0", END)
            text = self.readFile(fl)
            self.text.insert(END, text)
            self.setNameLabel("File: " + fl)
            self.autoLoadNewFile(self.fileName, "1.0")
            # self.setDisplay()
            # self.initAnnotate()
            self.text.mark_set(INSERT, "1.0")
            self.setCursorLabel(self.text.index(INSERT))

    def readFile(self, filename):
        f = open(filename, "rU")
        text = f.read()
        self.fileName = filename
        return text

    def setFont(self, value):
        _family = self.textFontStyle
        _size = value
        _weight = "bold"
        _underline = 0
        fnt = tkFont.Font(
            family=_family, size=_size, weight=_weight, underline=_underline)
        Text(self, font=fnt)

    def setNameLabel(self, new_file):
        self.lbl.config(text=new_file)

    def setCursorLabel(self, cursor_index):
        if self.debug:
            print "Action Track: setCursorLabel"
        row_column = cursor_index.split('.')
        cursor_text = ("row: %s col: %s" % (row_column[0], row_column[-1]))
        self.cursorIndex.config(text=cursor_text)

    def returnButton(self):
        if self.debug:
            print "Action Track: returnButton"
        self.pushToHistory()
        # self.returnEnter(event)
        content = self.entry.get()
        self.clearCommand()
        self.executeEntryCommand(content)
        return content

    def returnEnter(self, event):
        if self.debug:
            print "Action Track: returnEnter"
        self.pushToHistory()
        content = self.entry.get()
        self.clearCommand()
        self.executeEntryCommand(content)
        return content

    def textReturnEnter(self, event):
        press_key = event.char
        if self.debug:
            print "Action Track: textReturnEnter"
        self.pushToHistory()
        print "event: ", press_key
        # content = self.text.get()
        self.clearCommand()
        self.executeCursorCommand(press_key.lower())
        # self.deleteTextInput()
        return press_key


    def push_his(self):
        """
            保存历史
        """
        self.remarkHistory.append(self.getText())
        # print(self.getText())
    
    def pop_his(self, e):
        """
            撤回操作
        """
        if len(self.remarkHistory):
            text = self.remarkHistory.pop()
            # print(text)
            self.text.delete("1.0", END)
            self.text.insert("end-1c", text)
            # self.text.mark_set(INSERT, newcursor_index)
            # self.text.see(newcursor_index)
            # self.setCursorLabel(newcursor_index)
            if len(self.crt_selected_area):
                self.crt_selected_area.pop()
            self.setColorDisplay()
            self.setCurColor()

    def backToHistory(self, event):
        if self.debug:
            print "Action Track: backToHistory"
        if len(self.history) > 0:
            historyCondition = self.history.pop()
            # print "history condition: ", historyCondition
            historyContent = historyCondition[0]
            # print "history content: ", historyContent
            cursorIndex = historyCondition[1]
            # print "get history cursor: ", cursorIndex
            self.writeFile(self.fileName, historyContent, cursorIndex)
        else:
            print "History is empty!"
        self.text.insert(INSERT,
                         'p')  # add a word as pad for key release delete

    def keepCurrent(self, event):
        if self.debug:
            print "Action Track: keepCurrent"
        print("keep current, insert:%s" % (INSERT))
        print "before:", self.text.index(INSERT)
        self.text.insert(INSERT, 'p')
        print "after:", self.text.index(INSERT)

    def clearCommand(self):
        if self.debug:
            print "Action Track: clearCommand"
        self.entry.delete(0, 'end')

    def getText(self):
        textContent = self.text.get("1.0", "end-1c")
        textContent = textContent.encode('utf-8')
        return textContent

    def executeCursorCommand(self, command):
        if self.debug:
            print "Action Track: executeCursorCommand"
        content = self.getText()
        print("Command:" + command)
        try:
            firstSelection_index = self.text.index(SEL_FIRST)  # 选中开始坐标 1.1 1行第1个元素
            cursor_index = self.text.index(SEL_LAST)  # 选中的尾部坐标
            aboveHalf_content = self.text.get('1.0', firstSelection_index) # 选中部分以上的文本
            followHalf_content = self.text.get(firstSelection_index, "end-1c") # 选中以及以下文本
            selected_string = self.text.selection_get()  # 选中词组

            if re.match(self.entityRe, selected_string) != None:
                ## if have selected entity
                new_string_list = selected_string.strip('[@]').rsplit('#', 1)
                new_string = new_string_list[0]
                followHalf_content = followHalf_content.replace(
                    selected_string, new_string, 1)
                selected_string = new_string
                # cursor_index = "%s - %sc" % (cursor_index, str(len(new_string_list[1])+4))
                cursor_index = cursor_index.split('.')[0] + "." + str(
                    int(cursor_index.split('.')[1]) - len(new_string_list[1]) +
                    4)
            afterEntity_content = followHalf_content[len(selected_string):]

            if command == "q":
                print 'q: remove entity label'
            else:
                if len(selected_string) > 0:
                    entity_content, cursor_index = self.replaceString(  # 返回添加标记后的光标位置
                        selected_string, selected_string, command,
                        cursor_index)
            aboveHalf_content += entity_content
            content = self.addRecommendContent(
                aboveHalf_content, afterEntity_content, self.recommendFlag)
            # recommed_pos_lst = self.findAllRecommed(content)
            content = content.encode('utf-8')

            self.crt_selected_area.append({"master": (firstSelection_index, cursor_index),
                                        #   "recommed": recommed_pos_lst,
                                          "keyword": self.selected_txt
                                          })

            self.writeFile(self.fileName, content, cursor_index)
        except TclError:
            ## not select text
            cursor_index = self.text.index(INSERT)
            [line_id, column_id] = cursor_index.split('.')
            aboveLine_content = self.text.get('1.0',
                                              str(int(line_id) - 1) + '.end')
            belowLine_content = self.text.get(
                str(int(line_id) + 1) + '.0', "end-1c")
            line = self.text.get(line_id + '.0', line_id + '.end')
            matched_span = (-1, -1)
            detected_entity = -1  ## detected entity type:－1 not detected, 1 detected gold, 2 detected recommend
            for match in re.finditer(self.entityRe, line):
                if match.span(
                )[0] <= int(column_id) & int(column_id) <= match.span()[1]:
                    matched_span = match.span()
                    detected_entity = 1
                    break
            if detected_entity == -1:
                for match in re.finditer(self.recommendRe, line):
                    if match.span(
                    )[0] <= int(column_id) & int(column_id) <= match.span()[1]:
                        matched_span = match.span()
                        detected_entity = 2
                        break
            line_before_entity = line
            line_after_entity = ""
            if matched_span[1] > 0:
                selected_string = line[matched_span[0]:matched_span[1]]
                if detected_entity == 1:
                    new_string_list = selected_string.strip('[@*]').rsplit(
                        '#', 1)
                elif detected_entity == 2:
                    new_string_list = selected_string.strip('[$*]').rsplit(
                        '#', 1)
                new_string = new_string_list[0]
                old_entity_type = new_string_list[1]
                line_before_entity = line[:matched_span[0]]
                line_after_entity = line[matched_span[1]:]
                selected_string = new_string
                entity_content = selected_string
                cursor_index = line_id + '.' + str(
                    int(matched_span[1]) - (len(new_string_list[1]) + 4))
                if command == "q":
                    print 'q: remove entity label'
                elif command == 'y':
                    print "y: comfirm recommend label"
                    old_key = self.pressCommand.keys()[
                        self.pressCommand.values().index(old_entity_type)]
                    entity_content, cursor_index = self.replaceString(
                        selected_string, selected_string, old_key,
                        cursor_index)
                else:
                    if len(selected_string) > 0:
                        if command in self.pressCommand:
                            entity_content, cursor_index = self.replaceString(
                                selected_string, selected_string, command,
                                cursor_index)
                        else:
                            return
                line_before_entity += entity_content
            if aboveLine_content != '':
                aboveHalf_content = aboveLine_content + '\n' + line_before_entity
            else:
                aboveHalf_content = line_before_entity

            if belowLine_content != '':
                followHalf_content = line_after_entity + '\n' + belowLine_content
            else:
                followHalf_content = line_after_entity

            content = self.addRecommendContent(
                aboveHalf_content, followHalf_content, self.recommendFlag)
            content = content.encode('utf-8')
            self.writeFile(self.fileName, content, cursor_index)

    def executeEntryCommand(self, command):
        if self.debug:
            print "Action Track: executeEntryCommand"
        if len(command) == 0:
            currentCursor = self.text.index(INSERT)
            newCurrentCursor = str(int(currentCursor.split('.')[0]) + 1) + ".0"
            self.text.mark_set(INSERT, newCurrentCursor)
            self.setCursorLabel(newCurrentCursor)
        else:
            command_list = decompositCommand(command)
            for idx in range(0, len(command_list)):
                command = command_list[idx]
                if len(command) == 2:
                    select_num = int(command[0])
                    command = command[1]
                    content = self.getText()
                    cursor_index = self.text.index(INSERT)
                    newcursor_index = cursor_index.split('.')[0] + "." + str(
                        int(cursor_index.split('.')[1]) + select_num)
                    # print "new cursor position: ", select_num, " with ", newcursor_index, "with ", newcursor_index
                    selected_string = self.text.get(
                        cursor_index, newcursor_index).encode('utf-8')
                    aboveHalf_content = self.text.get(
                        '1.0', cursor_index).encode('utf-8')
                    followHalf_content = self.text.get(
                        cursor_index, "end-1c").encode('utf-8')
                    if command in self.pressCommand:
                        if len(selected_string) > 0:
                            # print "insert index: ", self.text.index(INSERT)
                            followHalf_content, newcursor_index = self.replaceString(
                                followHalf_content, selected_string, command,
                                newcursor_index)
                            content = self.addRecommendContent(
                                aboveHalf_content, followHalf_content,
                                self.recommendFlag)
                            # content = aboveHalf_content + followHalf_content
                    self.writeFile(self.fileName, content, newcursor_index)

    def deleteTextInput(self, event):
        if self.debug:
            print "Action Track: deleteTextInput"
        get_insert = self.text.index(INSERT)
        print "delete insert:", get_insert
        insert_list = get_insert.split('.')
        last_insert = insert_list[0] + "." + str(int(insert_list[1]) - 1)
        get_input = self.text.get(last_insert, get_insert).encode('utf-8')
        # print "get_input: ", get_input
        aboveHalf_content = self.text.get('1.0', last_insert).encode('utf-8')
        followHalf_content = self.text.get(last_insert,
                                           "end-1c").encode('utf-8')
        if len(get_input) > 0:
            followHalf_content = followHalf_content.replace(get_input, '', 1)
        content = aboveHalf_content + followHalf_content
        self.writeFile(self.fileName, content, last_insert)

    def replaceString(self, content, string, replaceType, cursor_index):
        if replaceType in self.pressCommand:
            new_string = "[@" + string + "#" + self.crt_mark + "*]"  # 根据标记字段标记文本
            newcursor_index = cursor_index.split('.')[0] + "." + str(
                int(cursor_index.split('.')[1]) +
                len(self.crt_mark) + 5)
        else:
            print "Invaild command!"
            print "cursor index: ", self.text.index(INSERT)
            return content, cursor_index
        content = content.replace(string, new_string, 1)
        return content, newcursor_index

    def writeFile(self, fileName, content, newcursor_index):
        if self.debug:
            print "Action track: writeFile"

        if len(fileName) > 0:
            if ".ann" in fileName:
                new_name = fileName
                ann_file = open(new_name, 'w')
                ann_file.write(content)
                ann_file.close()
            else:
                new_name = fileName + '.ann'
                ann_file = open(new_name, 'w')
                ann_file.write(content)
                ann_file.close()
            # print "Writed to new file: ", new_name
            self.autoLoadNewFile(new_name, newcursor_index)
            # self.generateSequenceFile()
        else:
            print "Don't write to empty file!"

    def addRecommendContent(self, train_data, decode_data, recommendMode):
        if not recommendMode:
            content = train_data + decode_data
        else:
            if self.debug:
                print "Action Track: addRecommendContent, start Recommend entity"
            content = maximum_matching(train_data, decode_data)
            # 正则匹配当前
            # self.findAllRecommed(content)
        return content

    def autoLoadNewFile(self, fileName, newcursor_index):
        if self.debug:
            print "Action Track: autoLoadNewFile"
        if len(fileName) > 0:
            self.text.delete("1.0", END)
            text = self.readFile(fileName)
            self.text.insert("end-1c", text)
            self.setNameLabel("File: " + fileName)
            self.text.mark_set(INSERT, newcursor_index)
            self.text.see(newcursor_index)
            self.setCursorLabel(newcursor_index)
            self.setColorDisplay()
            

    def setCurColor(self):
        """
            设置当前标记词语的颜色
        """
        if self.debug:
            print "Action Track: setCurColor"
        # if len(self.crt_selected_area) > 0:
        content = self.getText()
        content = content.decode("utf-8")

        match_pat = re.compile(r"\[\$|\$]\#.*?\*\]")
        last_pos_lst = self.findAllRecommed("", content, match_pat)
        self.text.tag_configure("last", background=self.lastRemarkColor)
        for i in last_pos_lst:
            self.text.tag_add("last", i[0], i[1])

        # for i in range(0, len(self.crt_selected_area) - 1):
        #     self.text.tag_configure("last", background=self.lastRemarkColor)
        #     self.text.tag_add("last", self.crt_selected_area[i]['master'][0], self.crt_selected_area[i]['master'][1])
        #     keyword = self.crt_selected_area[i]['keyword']
        #     recommend_pos_lst = self.findAllRecommed(keyword, content)
        #     for i in recommend_pos_lst:
        #         self.text.tag_add("last", i[0], i[1])
    
        if len(self.crt_selected_area) > 0:
            self.text.tag_configure("green", background=self.remarkColor)
            self.text.tag_configure("yellow", background="yellow")
            self.text.tag_add("green", self.crt_selected_area[-1]['master'][0], self.crt_selected_area[-1]['master'][1])
            keyword = self.crt_selected_area[-1]['keyword']
            recommend_pos_lst = self.findAllRecommed(keyword, content)
            for i in recommend_pos_lst:
                self.text.tag_add("yellow", i[0], i[1])


    def setColorDisplay(self, use_last_color=1):
        if self.debug:
            print "Action Track: setColorDisplay"
        self.text.config(insertbackground='red', insertwidth=4, font=self.fnt)

        # if use_last_color:
        txt_color = self.lastRemarkColor
        # else:
        #     txt_color = self.remarkColor

        countVar = StringVar()
        currentCursor = self.text.index(INSERT)
        lineStart = currentCursor.split('.')[0] + '.0'
        lineEnd = currentCursor.split('.')[0] + '.end'

        if self.colorAllChunk:
            self.text.mark_set("matchStart", "1.0")
            self.text.mark_set("matchEnd", "1.0")
            self.text.mark_set("searchLimit", 'end-1c')
            self.text.mark_set("recommend_matchStart", "1.0")
            self.text.mark_set("recommend_matchEnd", "1.0")
            self.text.mark_set("recommend_searchLimit", 'end-1c')
        else:
            self.text.mark_set("matchStart", lineStart)
            self.text.mark_set("matchEnd", lineStart)
            self.text.mark_set("searchLimit", lineEnd)
            self.text.mark_set("recommend_matchStart", lineStart)
            self.text.mark_set("recommend_matchEnd", lineStart)
            self.text.mark_set("recommend_searchLimit", lineEnd)
        while True:
            self.text.tag_configure("catagory", background=txt_color)
            self.text.tag_configure("edge", background=txt_color)
            pos = self.text.search(
                self.entityRe,
                "matchEnd",
                "searchLimit",
                count=countVar,
                regexp=True)
            if pos == "":
                break
            self.text.mark_set("matchStart", pos)
            self.text.mark_set("matchEnd", "%s+%sc" % (pos, countVar.get()))

            first_pos = pos
            second_pos = "%s+%sc" % (pos, str(1))
            lastsecond_pos = "%s+%sc" % (pos, str(int(countVar.get()) - 1))
            last_pos = "%s + %sc" % (pos, countVar.get())

            self.text.tag_add("catagory", second_pos, lastsecond_pos)
            self.text.tag_add("edge", first_pos, second_pos)
            self.text.tag_add("edge", lastsecond_pos, last_pos)
        ## color recommend type
        while True:
            self.text.tag_configure(
                "recommend", background=txt_color)
            recommend_pos = self.text.search(
                self.recommendRe,
                "recommend_matchEnd",
                "recommend_searchLimit",
                count=countVar,
                regexp=True)
            if recommend_pos == "":
                break
            self.text.mark_set("recommend_matchStart", recommend_pos)
            self.text.mark_set("recommend_matchEnd",
                               "%s+%sc" % (recommend_pos, countVar.get()))

            first_pos = recommend_pos
            # second_pos = "%s+%sc" % (recommend_pos, str(1))
            lastsecond_pos = "%s+%sc" % (recommend_pos,
                                         str(int(countVar.get())))
            self.text.tag_add("recommend", first_pos, lastsecond_pos)

        ## color the most inside span for nested span, scan from begin to end again
        if self.colorAllChunk:
            self.text.mark_set("matchStart", "1.0")
            self.text.mark_set("matchEnd", "1.0")
            self.text.mark_set("searchLimit", 'end-1c')
        else:
            self.text.mark_set("matchStart", lineStart)
            self.text.mark_set("matchEnd", lineStart)
            self.text.mark_set("searchLimit", lineEnd)
        while True:
            self.text.tag_configure(
                "insideEntityColor", background=self.insideNestEntityColor)
            pos = self.text.search(
                self.insideNestEntityRe,
                "matchEnd",
                "searchLimit",
                count=countVar,
                regexp=True)
            if pos == "":
                break
            self.text.mark_set("matchStart", pos)
            self.text.mark_set("matchEnd", "%s+%sc" % (pos, countVar.get()))
            first_pos = "%s + %sc" % (pos, 2)
            last_pos = "%s + %sc" % (pos, str(int(countVar.get()) - 1))
            self.text.tag_add("insideEntityColor", first_pos, last_pos)

    def findAllRecommed(self, keyword, content, re_pat=None):
        """
            查找所有同步产生的标记位置
        """
        content_lines = content.split("\n")
        if re_pat is None:
            match_pat = re.compile(r"\[\$" + keyword + "\#.*?\*\]")
        else:
            match_pat = re_pat
        line_no = 0
        recommed_pos_lst = []
        for line in content_lines:
            line_no += 1
            all_iter = match_pat.finditer(line)
            for i in all_iter:
                recommed_pos_lst.append(("{}.{}".format(line_no, i.start()),
                                         "{}.{}".format(line_no, i.end()),
                                        ))
        return recommed_pos_lst


    def pushToHistory(self):
        if self.debug:
            print "Action Track: pushToHistory"
        currentList = []
        content = self.getText()
        cursorPosition = self.text.index(INSERT)
        # print "push to history cursor: ", cursorPosition
        currentList.append(content)
        currentList.append(cursorPosition)
        self.history.append(currentList)

    def pushToHistoryEvent(self, event):
        if self.debug:
            print "Action Track: pushToHistoryEvent"
        currentList = []
        content = self.getText()
        cursorPosition = self.text.index(INSERT)
        # print "push to history cursor: ", cursorPosition
        currentList.append(content)
        currentList.append(cursorPosition)
        self.history.append(currentList)

    ## update shortcut map
    def renewPressCommand(self):
        if self.debug:
            print "Action Track: renewPressCommand"
        seq = 0
        new_dict = {}
        listLength = len(self.labelEntryList)
        delete_num = 0
        for key in sorted(self.pressCommand):
            label = self.labelEntryList[seq].get()
            if len(label) > 0:
                new_dict[key] = label
            else:
                delete_num += 1
            seq += 1
        self.pressCommand = new_dict
        for idx in range(1, delete_num + 1):
            self.labelEntryList[listLength - idx].delete(0, END)
            self.shortcutLabelList[listLength - idx].config(text="NON= ")
        with open(self.configFile, 'wb') as fp:
            pickle.dump(self.pressCommand, fp)
        self.setMapShow()
        tkMessageBox.showinfo(
            "Remap Notification",
            "Shortcut map has been updated!\n\nConfigure file has been saved in File:"
            + self.configFile)

    ## show shortcut map
    def setMapShow(self):
        if os.path.isfile(self.configFile):
            with open(self.configFile, 'rb') as fp:
                self.pressCommand = pickle.load(fp)
        hight = len(self.pressCommand)
        width = 2
        row = 0
        mapLabel = Label(
            self,
            text="Shortcuts map Labels",
            foreground="blue",
            font=(self.textFontStyle, 14, "bold"))
        mapLabel.grid(
            row=3,
            column=self.textColumn + 1,
            columnspan=2,
            rowspan=1,
            padx=10)
        self.labelEntryList = []
        self.shortcutLabelList = []
        row = 3
        for key in sorted(self.pressCommand):
            row += 1
            # print "key: ", key, "  command: ", self.pressCommand[key]
            symbolLabel = Label(
                self,
                text=key.upper() + ": ",
                foreground="blue",
                font=(self.textFontStyle, 14, "bold"))
            symbolLabel.grid(
                row=row,
                column=self.textColumn + 1,
                columnspan=1,
                rowspan=1,
                padx=3)
            self.shortcutLabelList.append(symbolLabel)

            labelEntry = Entry(
                self, foreground="blue", font=(self.textFontStyle, 14, "bold"))
            labelEntry.insert(0, self.pressCommand[key])
            labelEntry.grid(
                row=row, column=self.textColumn + 3, columnspan=1, rowspan=1)
            self.labelEntryList.append(labelEntry)
            # print "row: ", row

    def getCursorIndex(self):
        return self.text.index(INSERT)

    def generateSequenceFile(self):
        if (".ann" not in self.fileName) and (".txt" not in self.fileName):
            out_error = "Export only works on filename ended in .ann or .txt!\nPlease rename file."
            print out_error
            tkMessageBox.showerror("Export error!", out_error)

            return -1
        fileLines = open(self.fileName, 'rU').readlines()
        lineNum = len(fileLines)
        new_filename = self.fileName.split('.ann')[0] + '.anns'
        seqFile = open(new_filename, 'w')
        for line in fileLines:
            if len(line) <= 2:
                seqFile.write('\n')
                continue
            else:
                if not self.keepRecommend:
                    line = removeRecommendContent(line, self.recommendRe)
                wordTagPairs = getWordTagPairs(line, self.seged,
                                               self.tagScheme, self.onlyNP,
                                               self.goldAndrecomRe)
                for wordTag in wordTagPairs:
                    seqFile.write(wordTag)
                ## use null line to seperate sentences
                seqFile.write('\n')
        seqFile.close()
        print "Exported file into sequence style in file: ", new_filename
        print "Line number:", lineNum
        showMessage = "Exported file successfully!\n\n"
        showMessage += "Tag scheme: " + self.tagScheme + "\n\n"
        showMessage += "Keep Recom: " + str(self.keepRecommend) + "\n\n"
        showMessage += "Text Seged: " + str(self.seged) + "\n\n"
        showMessage += "Line Number: " + str(lineNum) + "\n\n"
        showMessage += "Saved to File: " + new_filename
        tkMessageBox.showinfo("Export Message", showMessage)


def getWordTagPairs(tagedSentence,
                    seged=True,
                    tagScheme="BMES",
                    onlyNP=False,
                    entityRe=r'\[\@.*?\#.*?\*\]'):
    newSent = tagedSentence.strip('\n').decode('utf-8')
    filterList = re.findall(entityRe, newSent)
    newSentLength = len(newSent)
    chunk_list = []
    start_pos = 0
    end_pos = 0
    if len(filterList) == 0:
        singleChunkList = []
        singleChunkList.append(newSent)
        singleChunkList.append(0)
        singleChunkList.append(len(newSent))
        singleChunkList.append(False)
        chunk_list.append(singleChunkList)
        # print singleChunkList
        singleChunkList = []
    else:
        for pattern in filterList:
            # print pattern
            singleChunkList = []
            start_pos = end_pos + newSent[end_pos:].find(pattern)
            end_pos = start_pos + len(pattern)
            singleChunkList.append(pattern)
            singleChunkList.append(start_pos)
            singleChunkList.append(end_pos)
            singleChunkList.append(True)
            chunk_list.append(singleChunkList)
            singleChunkList = []
    ## chunk_list format:
    full_list = []
    for idx in range(0, len(chunk_list)):
        if idx == 0:
            if chunk_list[idx][1] > 0:
                full_list.append([
                    newSent[0:chunk_list[idx][1]], 0, chunk_list[idx][1], False
                ])
                full_list.append(chunk_list[idx])
            else:
                full_list.append(chunk_list[idx])
        else:
            if chunk_list[idx][1] == chunk_list[idx - 1][2]:
                full_list.append(chunk_list[idx])
            elif chunk_list[idx][1] < chunk_list[idx - 1][2]:
                print "ERROR: found pattern has overlap!", chunk_list[idx][
                    1], ' with ', chunk_list[idx - 1][2]
            else:
                full_list.append([
                    newSent[chunk_list[idx - 1][2]:chunk_list[idx][1]],
                    chunk_list[idx - 1][2], chunk_list[idx][1], False
                ])
                full_list.append(chunk_list[idx])

        if idx == len(chunk_list) - 1:
            if chunk_list[idx][2] > newSentLength:
                print "ERROR: found pattern position larger than sentence length!"
            elif chunk_list[idx][2] < newSentLength:
                full_list.append([
                    newSent[chunk_list[idx][2]:newSentLength],
                    chunk_list[idx][2], newSentLength, False
                ])
            else:
                continue
    return turnFullListToOutputPair(full_list, seged, tagScheme, onlyNP)


def turnFullListToOutputPair(fullList,
                             seged=True,
                             tagScheme="BMES",
                             onlyNP=False):
    pairList = []
    for eachList in fullList:
        if eachList[3]:
            contLabelList = eachList[0].strip('[@$]').rsplit('#', 1)
            if len(contLabelList) != 2:
                print "Error: sentence format error!"
            label = contLabelList[1].strip('*')
            if seged:
                contLabelList[0] = contLabelList[0].split()
            if onlyNP:
                label = "NP"
            outList = outputWithTagScheme(contLabelList[0], label, tagScheme)
            for eachItem in outList:
                pairList.append(eachItem)
        else:
            if seged:
                eachList[0] = eachList[0].split()
            for idx in range(0, len(eachList[0])):
                basicContent = eachList[0][idx]
                if basicContent == ' ':
                    continue
                pair = basicContent + ' ' + 'O\n'
                pairList.append(pair.encode('utf-8'))
    return pairList


def outputWithTagScheme(input_list, label, tagScheme="BMES"):
    output_list = []
    list_length = len(input_list)
    if tagScheme == "BMES":
        if list_length == 1:
            pair = input_list[0] + ' ' + 'S-' + label + '\n'
            output_list.append(pair.encode('utf-8'))
        else:
            for idx in range(list_length):
                if idx == 0:
                    pair = input_list[idx] + ' ' + 'B-' + label + '\n'
                elif idx == list_length - 1:
                    pair = input_list[idx] + ' ' + 'E-' + label + '\n'
                else:
                    pair = input_list[idx] + ' ' + 'M-' + label + '\n'
                output_list.append(pair.encode('utf-8'))
    else:
        for idx in range(list_length):
            if idx == 0:
                pair = input_list[idx] + ' ' + 'B-' + label + '\n'
            else:
                pair = input_list[idx] + ' ' + 'I-' + label + '\n'
            output_list.append(pair.encode('utf-8'))
    return output_list


def removeRecommendContent(content, recommendRe=r'\[\$.*?\#.*?\*\](?!\#)'):
    output_content = ""
    last_match_end = 0
    for match in re.finditer(recommendRe, content):
        matched = content[match.span()[0]:match.span()[1]]
        words = matched.strip('[$]').split("#")[0]
        output_content += content[last_match_end:match.span()[0]] + words
        last_match_end = match.span()[1]
    output_content += content[last_match_end:]
    return output_content


def decompositCommand(command_string):
    command_list = []
    each_command = []
    num_select = ''
    for idx in range(0, len(command_string)):
        if command_string[idx].isdigit():
            num_select += command_string[idx]
        else:
            each_command.append(num_select)
            each_command.append(command_string[idx])
            command_list.append(each_command)
            each_command = []
            num_select = ''
    # print command_list
    return command_list


def main():
    print("SUTDAnnotator launched!")
    print(("OS:%s") % (platform.system()))
    root = Tk()
    root.geometry("1300x700+200+200")
    app = Example(root)
    app.setFont(17)
    root.mainloop()


if __name__ == '__main__':
    
    main()
