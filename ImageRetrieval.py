import tkinter as tk
from tkinter import Scrollbar
import math
import sys
from tkinter import messagebox
from PixInfo import PixInfo
from PIL import Image, ImageTk
import numpy as np
from statistics import stdev

# Use resampling to avoid antialias depreciation
ANTIALIAS = Image.Resampling.LANCZOS if hasattr(
    Image, "Resampling") else Image.ANTIALIAS

# Main app
class ImageViewer(tk.Frame):

    def __init__(self, master, pixInfo):

        tk.Frame.__init__(self, master)
        self.master = master
        self.pixInfo = pixInfo
        self.colorCode = pixInfo.get_colorCode()
        self.intenCode = pixInfo.get_intenCode()
        self.folderPath = pixInfo.get_folderPath()
        self.imageList = pixInfo.get_imageList()
        # list to store Thumbnail sized images
        self.photoList = pixInfo.get_photoList()
        # list to store image names
        self.imgNameList = pixInfo.get_imgNameList()
        # predefined column number for result listframe below
        self.colnum = 10
        # image name
        self.imageName = ""
        # image index
        self.index = 0
        # list to store image indexs
        self.indexList = pixInfo.get_indexList()
        # feature Matrix
        self.featureMatrix = pixInfo.get_featureMatrix()
        # relevance list
        self.relevanceList = pixInfo.get_relevanceList()
        # checkboxes list
        self.checkBoxValues = [tk.IntVar() for i in range(len(self.imageList))]
        # Image size for formatting.
        self.xmax = pixInfo.get_xmax()
        self.ymax = pixInfo.get_ymax()
        # total window size but it will open zoomed in as set
        master.geometry("1250x750")

        listFrame = tk.Frame(master, relief="groove",
                             borderwidth=1, padx=5, pady=5)
        listFrame.grid(row=1, column=0, columnspan=4,
                       sticky="news", padx=10, pady=5)

        self.listframe = listFrame

        # Create Control frame.
        controlFrame = tk.Frame(master, width=300)
        controlFrame.grid(row=0, column=3, sticky="sen", padx=10, pady=5)

        # Create Preview frame.
        previewListFrame = tk.Frame(
            master, width=30, height=self.ymax+100, borderwidth=1)
        previewListFrame.grid_propagate(0)
        previewListFrame.grid(row=0, column=0, sticky="news", padx=5, pady=5)

        previewFrame = tk.Frame(master, width=self.xmax+245, height=self.ymax+150, borderwidth=5,
                                relief="groove", highlightbackground='RED')
        previewFrame.grid_propagate(0)
        previewFrame.grid(row=0, column=1, sticky="news", padx=(5, 0), pady=5)
        self.previewFrame = previewFrame

        # Initialize selectImg usecase
        self.selectImg = tk.Label(self.previewFrame)
        self.selectImg.grid(row=0, column=0, sticky="news")

        # Create results frame.
        master.rowconfigure(0, weight=0)
        master.columnconfigure(0, weight=1)
        master.rowconfigure(1, weight=1)
        master.columnconfigure(1, weight=1)
        master.columnconfigure(2, weight=1)
        master.columnconfigure(3, weight=1)
        listFrame.rowconfigure(0, weight=1)
        listFrame.columnconfigure(0, weight=1)
        listFrame.columnconfigure(1, weight=0)
        controlFrame.rowconfigure(0, weight=1)
        controlFrame.columnconfigure(0, weight=1)
        previewFrame.rowconfigure(0, weight=1)
        previewFrame.columnconfigure(0, weight=1)

        # create listbox
        self.listbox = tk.Listbox(self.listframe, selectmode=tk.SINGLE)
        self.listbox.grid(row=0, column=0, sticky='news')
        self.listbox.bind('<<ListboxSelect>>', self.update_preview)

        self.photolist = tk.Listbox(previewListFrame, height=14)
        for i in range(len(self.imageList)):
            self.photolist.insert(
                i, self.getFilename(self.imageList[i].filename))
        self.photolist.activate(1)
        self.photolist.bind('<<ListboxSelect>>', self.update_preview)

        self.listbox = tk.Frame(listFrame)
        self.listbox.rowconfigure(0, weight=1)
        self.listbox.columnconfigure(0, weight=1)
        self.listbox.grid_propagate(False)

        # add canvas inside the list
        self.listcanvas = tk.Canvas(self.listbox)
        self.listcanvas.grid(row=0, column=0, sticky="news")
        self.gridframe = tk.Frame(self.listcanvas)
        self.listcanvas.create_window(
            (0, 0), window=self.gridframe, anchor='nw')
        # get a grid of all the images and it should be allowed to click
        listsize = len(self.photoList)

        rownum = int(math.ceil(listsize/float(self.colnum)))
        canvassize = (0, 0, (self.xmax*self.colnum), (self.ymax*rownum))
        for i in range(rownum):
            for j in range(self.colnum):
                if (i*self.colnum+j) < listsize:
                    particularImage = self.photoList[i*self.colnum+j]
                    index = i * self.colnum + j  # Calculate the index
                    img = tk.Button(self.gridframe, image=particularImage, fg='white',
                                    relief='flat', bg='white', bd=0, justify='center')
                    img.configure(image=particularImage)
                    img.photo = particularImage
                    img.config(command=lambda idx=index: self.display_image(
                        self.imgNameList[idx], idx))
                    img.grid(row=i, column=j, sticky='news', padx=5, pady=5)

        self.gridframe.update_idletasks()
        self.listcanvas.config(scrollregion=canvassize)
        self.listbox.grid(row=0, column=0, sticky='news')
        self.yaxis = self.listcanvas.yview()[0]
        self.listbox.bind('<<CanvasSelect>>', self.update_preview)

        # update lists
        self.photolist.delete(0, 'end')
        for i in range(len(self.imageList)):
            self.photolist.insert(
                i, self.getFilename(self.imageList[i].filename))

        # Colorcode button, clicking on this will sort by color code
        colorCodeButton = tk.Button(controlFrame, text="Sort by Color-Code", padx=5,
                                    width=15, command=lambda: self.find_distance(sortType='ColorCode'))
        colorCodeButton.grid(row=1, column=1, sticky="news", padx=5, pady=2)

        # Intensity Button, clicking on this will sort by intensity
        intensityButton = tk.Button(controlFrame, text="Sort by Intensity", padx=5,
                                    width=15, command=lambda: self.find_distance(sortType='intensity'))
        intensityButton.grid(row=1, column=0, sticky="news", padx=5, pady=2)

        # Colorcode + intensity Button, clicking on  this will sort by both color code and intensity
        bothButton = tk.Button(controlFrame, text="Sort by Color-code + Intensity", padx=5,
                               width=15, wraplength=100, command=lambda: self.find_distance(sortType='both'))
        bothButton.grid(row=2, column=0, sticky='news', padx=5, pady=2)

        # scrollbar at the bottom
        scrollbar_x = Scrollbar(self.listframe, orient="horizontal")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        # Create canvas for thumbnail iamges
        self.listcanvas = tk.Canvas(
            self.listbox, xscrollcommand=scrollbar_x.set)
        self.listcanvas.grid(row=0, column=0, sticky="news")
        scrollbar_x.config(command=self.listcanvas.xview)

        # checkboxes for Relevance feedback
        self.relevantChecks = tk.IntVar()
        self.relevantCheckBoxes = tk.Checkbutton(controlFrame, text='Enable Relevance Feedback', padx=5, width=15, wraplength=100,
                                                 variable=self.relevantChecks, offvalue=0, onvalue=1, command=lambda: self.add_relevant_checkbox(scrollbar_x))
        self.relevantCheckBoxes.grid(
            row=2, column=1, sticky='news', padx=5, pady=2)

        # Reset Button to go back to initial state
        resetButton = tk.Button(
            controlFrame, text='Reset', padx=5, width=15, command=lambda: self.reset())
        resetButton.grid(row=3, column=0, sticky="news", padx=5, pady=2)

        # Quit Button to exit the GUI
        quitButton = tk.Button(controlFrame, text='Quit',
                               padx=5, width=15, command=lambda: sys.exit(0))
        quitButton.grid(row=3, column=1, sticky="news", padx=5, pady=2)

        # Create a Label for displaying the page number
        self.page_label = tk.Label(master, text="Page: 1", font=("Arial", 10))
        self.page_label.grid(row=2, column=1, sticky="news", padx=5, pady=5)

        controlFrame.rowconfigure(0, weight=1)
        controlFrame.rowconfigure(1, weight=1)
        controlFrame.rowconfigure(2, weight=1)
        controlFrame.rowconfigure(3, weight=1)

        image = self.imageList[0]  # loads the first image
        self.previewFrame.update()
        # resize to fit the frame
        imResize = image.resize(self.resize_img(self.previewFrame.winfo_width(
        ), self.previewFrame.winfo_height(), image), ANTIALIAS)

        particularImage = ImageTk.PhotoImage(imResize)
        self.previewImg = tk.Label(self.previewFrame, image=particularImage)
        self.previewImg.photo = particularImage
        self.previewImg.grid(row=0, column=0, sticky='news')

        self.page_size = 20  # Set the page size to 20, only 20 images at a time
        self.current_page = 0  # set current page tp 0

        # button to move to the next page
        self.next_button = tk.Button(
            controlFrame, text="Next", padx=5, width=15, command=self.click_next_page)
        self.next_button.grid(row=4, column=1, sticky="news", padx=5, pady=2)

        # button to go back to the previous page
        self.previous_button = tk.Button(
            controlFrame, text="Prev", padx=5, width=15, command=self.click_prev_page)
        self.previous_button.grid(
            row=4, column=0, sticky="news", padx=5, pady=2)

        # Initialize the thumbnail grid with initial 20 images
        self.update_thumbnail_grid()

    # Update the thumbnail image grid
    def update_thumbnail_grid(self):
        start_index = (self.current_page) * self.page_size
        end_index = min(start_index + self.page_size, len(self.imageList))
        self.update_listbox(start_index, end_index)

        self.gridframe.update_idletasks()
        self.listcanvas.config(scrollregion=self.listcanvas.bbox("all"))

        current_page_number = self.current_page + \
            1  # 0-based index to 1-based page number
        total_pages = math.ceil(len(self.imageList) / self.page_size)
        self.page_label.config(
            text=f"Page: {current_page_number}/{total_pages}")

        # Enable both buttons initially
        self.previous_button['state'] = 'normal'
        self.next_button['state'] = 'normal'

        # Disable the "Prev" button on the first page
        if self.current_page == 0:
            self.previous_button['state'] = 'disabled'

        # Disable the "Next" button on the last page
        if (self.current_page + 1) * self.page_size >= len(self.imageList):
            self.next_button['state'] = 'disabled'

    # Display images in grid with sorting
    def update_listbox(self, start_index, end_index):

        self.photolist.delete(0, 'end')
        for i in range(start_index, end_index):
            img_index = self.indexList[i]
            img_name = self.getFilename(self.imageList[img_index].filename)
            self.photolist.insert(i, img_name)

        # Destroy the old grid frame
        self.gridframe.destroy()
        self.gridframe = tk.Frame(self.listcanvas)
        self.gridframe.update_idletasks()
        self.listcanvas.create_window(
            (0, 0), window=self.gridframe, anchor='nw')

        # Populate the grid with thumbnail iamges and image names
        listsize = len(self.photoList)
        rownum = int(math.ceil(listsize / float(self.colnum)))
        canvassize = (0, 0, (self.xmax * self.colnum), (self.ymax * rownum))
        for i in range(start_index // self.colnum, (end_index + self.colnum - 1) // self.colnum):
            for j in range(self.colnum):
                index = i * self.colnum + j
                if start_index <= index < end_index <= listsize:
                    # Add padding to the frame
                    frame = tk.Frame(self.gridframe, padx=5, pady=5)
                    frame.grid(row=i, column=j, sticky="news", padx=5, pady=5)

                    particularImage = self.photoList[self.indexList[index]]
                    img = tk.Button(frame, image=particularImage, fg='white',
                                    relief='flat', bg='white', bd=0, justify='center', padx=5, pady=5)  # Adjust padx and pady
                    img.configure(image=particularImage)
                    img.photo = particularImage
                    img.config(
                        command=lambda idx=index: self.display_image(self.imgNameList[self.indexList[idx]], self.indexList[idx]))
                    img.grid(row=0, column=0, sticky='news')

                    # Add label to display image name below the thumbnail.
                    img_name = self.getFilename(
                        self.imageList[self.indexList[index]].filename)[7:]
                    label = tk.Label(frame, text=img_name,
                                     font=("Arial", 8), wraplength=100)
                    label.grid(row=1, column=0, sticky='news')

                    if self.relevantChecks.get() == 1:
                        # add checkbox
                        checkbox = tk.Checkbutton(frame, text='Relevant',
                                                  variable=self.checkBoxValues[self.indexList[index]],
                                                  command=lambda x=self.indexList[index]: self.updateWeight(x))
                        if self.relevanceList[self.indexList[index]] == 1:
                            checkbox.select()
                        checkbox.grid(row=2, column=0, sticky='news')

        # Adjust size of canvas.
        self.gridframe.update_idletasks()
        self.listcanvas.config(scrollregion=canvassize)

    # Function for implementing next page pagination logic
    def click_next_page(self):
        if (self.current_page + 1) * self.page_size < len(self.imageList):
            self.current_page += 1
            self.update_thumbnail_grid()
        else:
            # Disable the "Next" button on the last page
            self.next_button['state'] = 'disabled'

    # Function for implementing previous page pagination logic
    def click_prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_thumbnail_grid()
        else:
            # Disable the "Prev" button on the first page
            self.previous_button['state'] = 'disabled'

    # Resize and scale the image
    def resize_img(self, width, height, img):
        prevwidth = img.size[0]
        prevheight = img.size[1]
        ratio = float(prevwidth)/prevheight
        if ratio >= 1:
            return (int(width), int(width/ratio))
        else:
            return (int(height*ratio), int(height))

    # Update the query image preview
    def update_preview(self,event):
        
        try:
            self.imgPreview = self.photolist.curselection()[0]
        except:
            self.imgPreview = 0
        image = self.imageList[int(self.imgPreview)]
        self.previewFrame.update()
        imageResize = image.resize(self.resize_img(self.previewFrame.winfo_width()-10, self.previewFrame.winfo_height()-10, image), ANTIALIAS)
        particularImage = ImageTk.PhotoImage(imageResize)
        self.previewImg.configure(image=particularImage)
        self.previewImg.photo = particularImage

    # Get the image distance using Manhattan distance function
    def find_distance(self, sortType):

        i = self.index  # get the current index

        # display error message box if no image selected but clicked on Sort by ColorCode + Intensity
        if self.relevantChecks.get() == 1 and all(var.get() == 0 for var in self.checkBoxValues):
            messagebox.showinfo("Error", "Please Select Relevant Images")
            return

        imageList = list(self.imageList[i].getdata())
        targetColorCode, targetIntensity = self.pixInfo.encode(imageList)
        targetSize = len(imageList)

        # if user selects Intensity
        if (sortType == 'intensity'):
            distances = self.calculate_manhattan_distance(targetIntensity, self.intenCode,
                                                     targetSize, self.pixInfo.get_imagesSizeList())

        # if user selects Color Code
        elif (sortType == 'ColorCode'):
            distances = self.calculate_manhattan_distance(targetColorCode, self.colorCode,
                                                     targetSize, self.pixInfo.get_imagesSizeList())

        # both refers to color code + intensity
        elif (sortType == 'both'):
            targetFeatureMatrix = self.featureMatrix[i]

            # check if Relevant is checked
            if (self.relevantChecks.get() == 0):
                distances = self.calculate_weighted_distance(
                    targetFeatureMatrix, self.featureMatrix, np.ones(targetFeatureMatrix.shape[0])*1/targetFeatureMatrix.shape[0])
            else:
                # get the relevant images row values
                relevantValues = []
                for i in range(len(self.relevanceList)):
                    if self.relevanceList[i] == 1:
                        relevantValues.append(self.featureMatrix[i])

                # display error message box if no image selected but clicked on Sort by ColorCode + Intensity
                if not relevantValues:
                    messagebox.showinfo(
                        "Error", "Please Select Relevant Images")
                    return

                # calculate weight for next itr
                stdDevValues = []
                for i in range(len(relevantValues[0])):
                    standarddev = stdev(np.array(relevantValues)[
                                        :, i])  # calc std dev
                    stdDevValues.append(standarddev)
                stdDevValues = np.array(stdDevValues)
                weights = []
                for i in range(len(stdDevValues)):
                    if stdDevValues[i] == 0:
                        average = (np.array(relevantValues)[
                               :, i]).mean()  # find avg
                        if average != 0:  # if avg not zero
                            # use minimum std deviation which is not zero multiplied by 0.5
                            weight = 1 /(0.5*min(stdDevValues[stdDevValues != 0]))
                        else:
                            weight = 0  # if avg is 0 use weight 0
                    else:
                        weight = 1/stdDevValues[i]
                    weights.append(weight)
                weights = np.array(weights)
                weights = weights/np.linalg.norm(weights, ord=1)
                distances = self.calculate_weighted_distance(
                    targetFeatureMatrix, self.featureMatrix, weights)

        distancesValues = [(self.photoList[i], distances[i])
                           for i in range(len(self.imageList))]

        self.update_results(distancesValues)
        self.update_thumbnail_grid()
        return

    # This function Calculates the Manhattan distance
    def calculate_manhattan_distance(self, targetIntensity, intensityValues, targetSize, sizeList):
        result = []
        for j in range(len(intensityValues)):
            code = intensityValues[j]
            sum = 0
            for i in range(len(targetIntensity)):
                sum += math.fabs(targetIntensity[i]/float(targetSize) -
                                 float(code[i])/sizeList[j])
            result.append(sum)
        return result

    # find weighted values for all images
    def calculate_weighted_distance(self, targetFeatureMatrix, featureMatrix, weights):
        result = []
        for i in range(featureMatrix.shape[0]):
            sum = 0
            for j in range(featureMatrix.shape[1]):
                weight = weights[j]
                sum += weight * math.fabs(featureMatrix[i][j]-targetFeatureMatrix[j])
            result.append(sum)
        return result

    # Update the results grid with the sorted images
    def update_results(self, sortedValues):
        # sort the obtained Manhattan Distance Array
        sortedOrderLists = sorted(sortedValues, key=lambda x: x[1])
        self.indexList = sorted(
            self.indexList, key=lambda i: sortedValues[i][1])
        photos = [(self.pixInfo.imageNamesList[i], sortedOrderLists[i][0])
                       for i in range(len(sortedOrderLists))]
        self.gridframe.destroy()
        self.gridframe = tk.Frame(self.listcanvas)
        self.gridframe.update_idletasks()
        self.listcanvas.create_window(
            (0, 0), window=self.gridframe, anchor='nw')
        listsize = len(self.photoList)
        rownum = int(math.ceil(listsize/float(self.colnum)))
        canvassize = (0, 0, (self.xmax*self.colnum), (self.ymax*rownum))
        for i in range(rownum):
            for j in range(self.colnum):
                if (i*self.colnum+j) < listsize:
                    frame = tk.Frame(self.gridframe)
                    frame.grid(row=i, column=j, sticky="news", padx=5, pady=5)
                    particularImage = photos[i*self.colnum+j][1]
                    img = tk.Button(frame, image=particularImage, fg='white',
                                    relief='flat', bg='white', bd=0, justify='center')
                    img.configure(image=particularImage)
                    img.photo = particularImage
                    img.config(command=lambda i=i, j=j: self.display_image(
                        self.imgNameList[self.indexList[i*self.colnum+j]], self.indexList[i*self.colnum+j]))

                    img.grid(row=0, column=0, sticky='news')
                    if (self.relevantChecks.get() == 1):
                        checkbox = tk.Checkbutton(frame, text='Relevant',
                                                  variable=self.checkBoxValues[self.indexList[i*self.colnum+j]],
                                                  command=lambda x=self.indexList[i*self.colnum+j]: self.updateWeight(x))
                        if self.relevanceList[self.indexList[i*self.colnum+j]] == 1:
                            checkbox.select()
                        checkbox.grid(row=1, column=0, sticky='news')
        # adjust size of canvas
        self.gridframe.update_idletasks()
        self.listcanvas.config(scrollregion=canvassize)
        self.listcanvas.yview_moveto(self.yaxis)
        self.current_page = 0

    # Display the image with the filename
    def display_image(self, imgname, index):
        image = Image.open(imgname)
        self.imageName = imgname
        self.index = index

        # resize to fit the frame
        self.previewFrame.update()
        imResize = image.resize((400, 200), ANTIALIAS)
        particularImage = ImageTk.PhotoImage(imResize)
        self.previewImg.configure(
            image=particularImage)
        self.previewImg.photo = particularImage

    # Add checkbox for all the images in the grid
    def add_relevant_checkbox(self, scrollbar_x):

        # destroy the grid inside canvas
        self.gridframe.destroy()
        self.gridframe = tk.Frame(self.listcanvas)
        self.gridframe.update_idletasks()
        self.listcanvas.create_window((0, 0), window=self.gridframe, anchor='nw')
        listsize = len(self.photoList)
        items_per_page = 20
        self.current_page = 1
        start_index = (self.current_page - 1) * items_per_page
        end_index = min(self.current_page * items_per_page, listsize)
        rownum = int(math.ceil((end_index - start_index) / float(self.colnum)))

        for i in range(rownum):
            for j in range(self.colnum):
                index = start_index + i * self.colnum + j
                if index < end_index:
                    frame = tk.Frame(self.gridframe)
                    frame.grid(row=i, column=j, sticky="news", padx=5, pady=5)
                    particularImage = self.photoList[self.indexList[index]]
                    img = tk.Button(frame, image=particularImage, fg='white',
                                    relief='flat', bg='white', bd=0, justify='center')
                    img.configure(image=particularImage)
                    img.photo = particularImage
                    img.config(command=lambda idx=index: self.display_image(
                        self.imgNameList[self.indexList[idx]], self.indexList[idx]))
                    img.grid(row=0, column=0, sticky='news')

                    # Add a label to display image name below the thumbnail
                    img_name = self.getFilename(
                        self.imageList[self.indexList[index]].filename)[7:]
                    label = tk.Label(frame, text=img_name,
                                     font=("Arial", 8), wraplength=100)
                    label.grid(row=1, column=0, sticky='news')

                    # Get relevant images
                    if self.relevantChecks.get() == 1:
                        checkbox = tk.Checkbutton(frame, text='Relevant',
                                                  variable=self.checkBoxValues[self.indexList[index]],
                                                  command=lambda x=self.indexList[index]: self.updateWeight(x))
                        checkbox.grid(row=2, column=0, sticky='news')

        # Add horizontal scrollbar to canvas - this will be displayed at the bottom
        scrollbar_x.config(command=self.listcanvas.xview)
        self.listcanvas.config(xscrollcommand=scrollbar_x.set)
        self.gridframe.update_idletasks()
        self.listcanvas.config(scrollregion=self.listcanvas.bbox("all"))

    # Update the weightS after each iteration
    def updateWeight(self, index):
        relevantVals = self.checkBoxValues[index]
        self.relevanceList[index] = relevantVals.get()

    # Get filename from the filepath
    def getFilename(self, imageName):
        i = imageName.rfind('/')
        return imageName[i+1:]

    # Reset the application
    def reset(self):
        
        self.imgPreview = 0  # Reset the preview image index to 0
        self.index = 0  # Reset the image index to 0
        self.current_page = 0  # Reset the current page to the first page
        self.page_size = 20  # Set the page size to 20
        self.indexList = list(range(len(self.imageList)))
        self.relevanceList = [0] * len(self.imageList)
        self.checkBoxValues = [tk.IntVar() for _ in range(len(self.imageList))]
        self.relevantCheckBoxes.deselect()

        # Destroy the old grid frame
        self.gridframe.destroy()
        self.gridframe = tk.Frame(self.listcanvas)
        self.gridframe.update_idletasks()
        self.listcanvas.create_window(
            (0, 0), window=self.gridframe, anchor='nw')

        # Get a grid view of images for the current page you are in
        self.update_thumbnail_grid()
        self.update_preview(0)


# the main executable section
if __name__ == '__main__':

    root = tk.Tk()
    # CBIR - content based image retrieval
    root.title('CBIR With Relevance Feedback')
    root.state('zoomed')
    pixInfo = PixInfo(root)
    imageViewer = ImageViewer(root, pixInfo)
    root.mainloop()
