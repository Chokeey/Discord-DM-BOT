import asyncio
import queue
from tkinter import *

import aiofiles


class BotGui:
    def __init__(self):
        self._root = Tk()
        self.dmListQueue = queue.Queue()
        self.logListQueue = queue.Queue()
        self._dmLabel = Label(self._root, text="Messages Sent:")
        self._logLabel = Label(self._root, text="Logs:")
        self._dmListBox = Listbox(self._root)
        self._logListBox = Listbox(self._root)
        self._xdmListScroll = Scrollbar(self._root, orient=HORIZONTAL)
        self._xlogListScroll = Scrollbar(self._root, orient=HORIZONTAL)
        self._ydmListScroll = Scrollbar(self._root)
        self._ylogListScroll = Scrollbar(self._root)

    def run(self):
        self._dmLabel.pack(side=TOP, anchor=NW)
        self._logLabel.pack(side=TOP, anchor=NE)
        self._dmListBox.pack(side=LEFT, fill=BOTH, expand=True)
        self._xdmListScroll.pack(side=LEFT, fill=BOTH)
        self._ydmListScroll.pack(side=LEFT, fill=BOTH)
        self._logListBox.pack(side=LEFT, fill=BOTH, expand=True)
        self._xlogListScroll.pack(side=LEFT, fill=BOTH)
        self._ylogListScroll.pack(side=LEFT, fill=BOTH)

        # Attaching Listbox to Scrollbar
        # Since we need to have a vertical
        # scroll we use yscrollcommand
        self._dmListBox.config(yscrollcommand=self._ydmListScroll.set, xscrollcommand=self._xdmListScroll.set)
        self._logListBox.config(yscrollcommand=self._ylogListScroll.set, xscrollcommand=self._xlogListScroll.set)

        # setting scrollbar command parameter
        # to listbox.yview method its yview because
        # we need to have a vertical view
        self._xdmListScroll.config(command=self._dmListBox.xview)
        self._xlogListScroll.config(command=self._logListBox.xview)
        self._ydmListScroll.config(command=self._dmListBox.yview)
        self._ylogListScroll.config(command=self._logListBox.yview)
        self.update()
        self._root.mainloop()

    def update(self):
        if self.dmListQueue.qsize() > 0:
            self._dmListBox.insert(END, self.dmListQueue.get())
            self._dmListBox.select_clear(self._dmListBox.size() - 2)  # Clear the current selected item
            self._dmListBox.select_set(END)  # Select the new item
            self._dmListBox.yview(END)

        if self.logListQueue.qsize() > 0:
            self._logListBox.insert(END, self.logListQueue.get())
            self._logListBox.select_clear(self._logListBox.size() - 2)  # Clear the current selected item
            self._logListBox.select_set(END)  # Select the new item
            self._logListBox.yview(END)

        self._root.after(10, self.update)

    @staticmethod
    async def writeToLog(line):
        async with aiofiles.open("gui.log", "a+") as f:
            await f.write(line)
            await f.write("\n")

    def pushToLogQueue(self, log):
        #loop = asyncio.get_event_loop()
        #if loop is None:
        #    loop = asyncio.new_event_loop()
        #asyncio.set_event_loop(loop)
        self.logListQueue.put(log)
        #asyncio.ensure_future(BotGui.writeToLog(log))

    def pushToNotificationQueue(self, notification):
        #loop = asyncio.get_event_loop()
        #if loop is None:
        #    loop = asyncio.new_event_loop()
        #asyncio.set_event_loop(loop)
        self.dmListQueue.put(notification)
        #asyncio.ensure_future(BotGui.writeToLog(notification))
