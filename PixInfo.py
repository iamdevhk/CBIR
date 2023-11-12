# PixInfo.py
# Program to start evaluating an image in python

from PIL import Image, ImageTk
import glob, os
import numpy as np
from statistics import stdev 



# Use resampling to avoid antialias depreciation
ANTIALIAS = Image.Resampling.LANCZOS if hasattr(
    Image, "Resampling") else Image.ANTIALIAS
# Pixel Info class.
class PixInfo:
    
    # Constructor.
    def __init__(self, master):
    
        self.master = master
        self.imageList = []
        self.photoList = []
        self.imageNamesList=[]
        self.imagesSizeList=[]
        self.xmax = 0
        self.ymax = 0
        self.colorCode = []
        self.intenCode = []
        self.folderPath = 'images'
        self.reloadImages(self.folderPath)
            
    def reloadImages(self, folderPath):
        self.imageList = []
        self.photoList = []
        self.imageNamesList = []
        self.imagesSizeList = []
        self.xmax = 0
        self.ymax = 0
        self.colorCode = []
        self.intenCode = []
        self.folderPath = folderPath

        # Create a list of image files and sort them based on the numeric part in the file names.
        image_files = sorted(glob.glob(self.folderPath + '/*.jpg'), key=lambda x: int(os.path.splitext(os.path.basename(x))[0]))

        # Add all images to list
        for infile in image_files:
            image = Image.open(infile)
            self.imageNamesList.append(infile)
            imageSize = image.size
            x = int(imageSize[0] / 3)
            y = int(imageSize[1] / 3)
            resizedImg = image.resize((x, y),ANTIALIAS)
            photo = ImageTk.PhotoImage(resizedImg)

            # max sizes of the image
            if x > self.xmax:
                self.xmax = x
            if y > self.ymax:
                self.ymax = y

            # Add image to list
            self.imageList.append(image)
            self.photoList.append(photo)
        
        # Create a list of pixel data for each image and add it
        # to a list.
        for image in self.imageList[:]:
            imgList = list(image.getdata())
            CcBins, InBins = self.encode(imgList)
            self.colorCode.append(CcBins)
            self.intenCode.append(InBins)
            self.imagesSizeList.append(len(imgList))
        
        #nromalzie intensty
        sum = np.linalg.norm(self.intenCode, axis=1, ord=1) 
        normalizedIntensity = (self.intenCode/sum[:, np.newaxis])
        # normalize color code
        sum = np.linalg.norm(self.colorCode, axis=1, ord=1)
        normalizedColorCode = self.colorCode/sum[:,np.newaxis]
        # concatenate intensity and color code
        self.featureMatrix = np.concatenate((normalizedIntensity, normalizedColorCode), axis=1)
        # calculate average
        avg = np.average(self.featureMatrix, axis=0)
        # calculate standard deviation
        sd = []
        for i in range(self.featureMatrix.shape[1]):
            sdVal = stdev(self.featureMatrix[:,i])
            sd.append(sdVal)

        # calcualte gaussian normalalized matrix
        gaussiannormalizedMatrix = np.zeros((self.featureMatrix.shape[0], self.featureMatrix.shape[1]))
        for i in range(self.featureMatrix.shape[0]):
            for j in range(self.featureMatrix.shape[1]):
                if (sd[j]!=0):
                    gaussiannormalizedMatrix[i][j] = (self.featureMatrix[i][j]-avg[j])/(sd[j])
                else:
                    gaussiannormalizedMatrix[i][j]=0
        self.featureMatrix = gaussiannormalizedMatrix
       
        self.indexList = list(range(len(self.imageList)))
        self.relevanceList = [0]*len(self.imageList)

    # Bin function returns an array of bins for each 
    # image, both Intensity and Color-Code methods.
    def encode(self, imageList):
        
        # 2D array initilazation for bins, initialized
        # to zero.
        CcBins = [0 for i in range(64)]
        InBins = [0 for i in range(25)]
        for rgb in imageList:
            intensity = rgb[0]*0.299+rgb[1]*0.587+rgb[2]*0.114
            if (intensity >= 250):
                InBins[24]+=1
            else:
                InBins[int(intensity/10)]+=1
        for rgb in imageList:
            mask = rgb[0]//64*16+rgb[1]//64*4+rgb[2]//64
            CcBins[mask]+=1
        
        return CcBins, InBins
     
    # Accessor functions:
    def get_imageList(self):
        return self.imageList
    
    def get_photoList(self):
        return self.photoList
    
    def get_imgNameList(self):
        return self.imageNamesList

    def get_xmax(self):
        return self.xmax
    
    def get_ymax(self):
        return self.ymax
    
    def get_colorCode(self):
        return self.colorCode
        
    def get_intenCode(self):
        return self.intenCode

    def get_folderPath(self):
        return self.folderPath

    def get_imagesSizeList(self):
        return self.imagesSizeList

    def get_indexList(self):
        return self.indexList

    def get_featureMatrix(self):
        return self.featureMatrix

    def get_relevanceList(self):
        return self.relevanceList