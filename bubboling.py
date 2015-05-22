'''
    This file is part of Bubboling.
    Bubboling is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    DeviantArtWatcher is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with  WhatsApp Dragon.  If not, see <http://www.gnu.org/licenses/>.
    
    @author DangerBlack
    @version 0.1
   
'''
import numpy as np
import random
import scipy.misc
import os.path
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from copy import copy, deepcopy
import pyocr
import pyocr.builders
import goslate

class Bbox:
	def __init__(self, minx,miny,maxx,maxy):
		self.minx=minx
		self.miny=miny
		self.maxx=maxx
		self.maxy=maxy	
	def printS(self):
		print("["+str(self.minx)+"-"+str(self.maxx)+"]["+str(self.miny)+"-"+str(self.maxy)+"]")
	def toS(self):
		return "["+str(self.minx)+"-"+str(self.maxx)+"]["+str(self.miny)+"-"+str(self.maxy)+"]"
	def adapt(self,i,j):
		if(self.minx>i):
			self.minx=i
		if(self.miny>j):
			self.miny=j
		if(self.maxx<i):
			self.maxx=i
		if(self.maxy<j):
			self.maxy=j
	def area(self):
		return (self.maxx-self.minx)*(self.maxy-self.miny)

filename="dvigil.png"

im = Image.open(filename) #Can be many different formats.
pix = im.load()
dx= im.size[0]
dy= im.size[1]

if(len(pix[10,10])>2): #color comics
	print('Color comics')
	stepx=20
	stepy=20
	#dvigil
	minTol=0.05
	maxTol=0.65
	background=(255,255,255)
	textcolor=(3,3,3)
	debugcolor=(255,0,0)
	tollerance=2
else:				  #manga
	print("it's a manga")
	stepx=25 #20
	stepy=25 #20
	#onepiece
	minTol=0.20
	maxTol=0.95
	background=(255,255)
	textcolor=(0,255)
	debugcolor=(125,255)
	tollerance=3


print(im.size) 		#Get the width and hight of the image for iterating over
print(pix[10,10])	#Get the RGBA Value of the a pixel of an image
#pix[x,y] = value 	# Set the RGBA Value of the image (tuple)

#This method check 'precision' point in the img in the area [px, px+stepx][py, py+stepy]
# checking if they are text color or background color
# return the ratio of this two quantities
# return -1 if no text found 
def montecarlo(img,c_bg,c_text,px,py,stepx,stepy,precision):
	find_bg=0
	find_text=0
	#print("x:"+str(px)+"-"+str(px+stepx-1)),
	#print("y:"+str(py)+"-"+str(py+stepy-1))
	for i in range(0,precision):
		x=random.randint(px,px+stepx-1)		
		y=random.randint(py,py+stepy-1)
		#print(img[x,y])
		#print(c_bg)
		if(np.allclose(img[x,y],c_bg,atol=10)):
			#print("BG"+str(img[x,y]))
			find_bg=find_bg+1
		elif(np.allclose(img[x,y],c_text,atol=10)):#allclose array_equal4  #5
			#print("TX"+str(img[x,y]))
			find_text=find_text+1
	if(find_bg>0):
		ratio=float(find_text)/float(find_bg)
	else:
		ratio=find_text
	ignore=precision-(find_bg+find_text)
	
	if(px==3*stepx)and(py==3*stepy): #debugpurpose
		print("     ratio: "+str(ratio))
		print("     nope:  "+str(ignore))
		print("     bg:    "+str(find_bg))
		print("     text:  "+str(find_text))
	
	if(ratio!=0)and(ignore<(precision/tollerance)+10):#2
		return ratio
	elif(ignore>=(precision/tollerance)+10):
		return -1
	else:
		return 0

# this method tryes to clear the bubble 
# deprecated
def whiteBubble(sizex,sizey,mat,img,stepx,stepy,color):
	for j in range(0,sizey-1):#me ne fotto dei bordi, non ci sono scritte ai bordi hipotesis
		for i in range(0,sizex-1):
			if(mat[i][j]==1):
				for q in range(i*stepx,i*stepx+stepx):
					for k in range(j*stepy,j*stepy+stepy):
						img[q,k]=color
	return img

# this method print a matrix from the bubble
# returns a matrix of 0 1, 1 if contains text	
def matrixOfBubble(mat,bat,minTol,maxTol):
	for j in range(0,sizey):
		for i in range(0,sizex):
			if(mat[i][j]>minTol)and(mat[i][j]<maxTol):
				print('| x '),
				bat[i][j]=1
			else:
				print('|   '),
		print('|')
	return bat

#this method agglomerate the text in the bat matrix,
#search locally if there are contiguos 1 in the matrix
def agglomerate(bat,sizex,sizey):
	cat= deepcopy(bat)
	agg=[]
	for j in range(0,sizey):
		for i in range(0,sizex):
			if(cat[i][j]==1):
				agg.append(localsearch(cat,i,j,sizex,sizey,Bbox(i,j,i,j)))
	return agg


def extendBB(i,j,bb):
	if(i<bb.minx):
		bb.minx=i
	if(i>bb.maxx):
		bb.maxx=i
	if(j<bb.miny):
		bb.miny=j
	if(i>bb.maxy):
		bb.maxy=j
	return bb
	
#This method recursively search for 1 in the matrix cat
def localsearch(cat,i,j,sizex,sizey,bb):
	#print("LS: "+str(i)+" "+str(j)+" {["+str(bb.minx)+"-"+str(bb.maxx)+"]["+str(bb.miny)+"-"+str(bb.maxy)+"]}")
	if(cat[i,j]==1):
		bb.adapt(i,j)
		cat[i,j]=-1
		temp=[Bbox(bb.minx,bb.miny,bb.maxx,bb.maxy)]
		if(i>1):
			t=localsearch(cat,i-1,j,sizex,sizey,bb)
			temp.append(t)
		if(j>1):
			t=localsearch(cat,i,j-1,sizex,sizey,bb)
			temp.append(t)
		if(i<sizex):
			t=localsearch(cat,i+1,j,sizex,sizey,bb)
			temp.append(t)
		if(j<sizey):
			t=localsearch(cat,i,j+1,sizex,sizey,bb)
			temp.append(t)
		if(i>1)and(j>1):
			t=localsearch(cat,i-1,j-1,sizex,sizey,bb)
			temp.append(t)
		if(i>1)and(j<sizey):
			t=localsearch(cat,i-1,j+1,sizex,sizey,bb)
			temp.append(t)
		if(i<sizex)and(j>1):
			t=localsearch(cat,i+1,j-1,sizex,sizey,bb)
			temp.append(t)
		if(i<sizex)and(j<sizey):
			t=localsearch(cat,i+1,j+1,sizex,sizey,bb)
			temp.append(t)
		res=temp[0]
		for q in temp:#TODO
			#print("Aggiorno res "+str(res.toS())+" "+str(q.toS()))
			if(res.minx>q.minx):
				res.minx=q.minx
			if(res.miny>q.miny):
				res.miny=q.miny
			if(res.maxx<q.maxx):
				res.maxx=q.maxx
			if(res.maxy<q.maxy):
				res.maxy=q.maxy
		return res
	else:
		return Bbox(bb.minx,bb.miny,bb.maxx,bb.maxy)	

def depixelation(img,x,y,k,color):
	img[x,y]=color
	img[x+k,y]=color
	img[x-k,y]=color
	img[x,y+k]=color
	img[x,y-k]=color
	img[x+k,y+k]=color
	img[x-k,y-k]=color
	img[x+k,y-k]=color
	img[x-k,y+k]=color
	
def clearOldText(img,bb,stepx,stepy,textcolor,background):
	for x in range(bb.minx*stepx,bb.maxx*stepy+stepx):
		for y in range(bb.miny*stepy,bb.maxy*stepy+stepy):
			if(x==bb.minx*stepx)or((x==bb.maxx*stepx+stepx-1)):
				depixelation(img,x,y,1,debugcolor)					
			if(y==bb.miny*stepy)or((y==bb.maxy*stepy+stepy-1)):
				depixelation(img,x,y,1,debugcolor)
			if(np.allclose(img[x,y],textcolor,atol=40,rtol=5)):
				img[x,y]=background
				depixelation(img,x,y,1,background)
				depixelation(img,x,y,2,background)

def writeOnImg(img,text,bb,stepx,stepy,textcolor,gs,leng):
	font = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSans.ttf",16)
	#img=Image.new("RGBA", (500,250),(255,255,255))
	draw = ImageDraw.Draw(img)
	text=sanitizeText(text)
	text=gs.translate(text,leng)
	print('TRADOTTO: '+text)
	lines= text.split('\n')
	count=0
	for line in lines:
		if(line!=""):
			#2*stepx 2*stepy (bubble curvature correction)
			draw.text((bb.minx*stepx+1*stepx, 1*stepy+bb.miny*stepy+count*16),line,textcolor,font=font)
			count=count+1
	draw = ImageDraw.Draw(img)

def sanitizeText(text):
	human=('A','B','C','I','E','E','G','S','O','H','T','I','T')
	leet=('4','8',':','{','3','2','6','5','0','}|','|\'','/','1\'')
	for i in np.arange(len(human)):
		text=text.replace(leet[i],human[i])
	return text
def saveMatrix(bat,sizex,sizey):
	temp=np.matrix(bat)
	np.save('results/working.txt',temp)
def loadMatrix():
	temp=np.load('results/working.txt.npy')
	return temp

#montecarlo(pix,(255,255,255),(0,0,0),0,0,stepx,stepy,100)


media=0
count=0
sizex=dx/stepx
if(dx % stepx !=0):
	sizex=sizex+1
sizey=dy/stepy
if(dy % stepy !=0):
	sizey=sizey+1
mat=[[float(0) for x in range(sizey)] for x in range(sizex)]
bat=[[0 for x in range(sizey)] for x in range(sizex)]

for i in range(0,sizex):
	for j in range(0,sizey):
		lstepx=stepx
		if(i*stepx+stepx>dx):
			lstepx=dx-i*stepx
		lstepy=stepy
		if(j*stepy+stepy>dy):
			lstepy=dy-j*stepy
		#print("cella "+str(i)+" "+str(j))
		mat[i][j]=montecarlo(pix,background,textcolor,i*stepx,j*stepy,lstepx,lstepy,200)
		if(mat[i][j]!=0):
			media=media+mat[i][j]
			count=count+1

matrixOfBubble(mat,bat,minTol,maxTol)

media=float(media)/float(count)
print("La media e': "+str(media))

#img=whiteBubble(sizex,sizey,bat,pix,stepx,stepy,debugcolor)

saveMatrix(bat,sizex,sizey)

bat=loadMatrix()
sizex=len(bat)
sizey=len(bat[0])
print('Comicio ad agglomerare')
cluster=agglomerate(bat,sizex,sizey)

tools = pyocr.get_available_tools()
tool = tools[0]
gs=goslate.Goslate()
for i in np.arange(len(cluster)):
	#q in cluster:
	q=cluster[i]
	print(str(i)+': cluster in: '+q.toS()+" "+str(q.area()))
	bbox = (q.minx*stepx, q.miny*stepy, q.maxx*stepx+stepx, q.maxy*stepy+stepy)
	working_slice = im.crop(bbox)
	txt = tool.image_to_string(
		working_slice,
		lang='eng',
		builder=pyocr.builders.TextBuilder()
	)
	print(txt)
	if(len(txt)>0):
		clearOldText(pix,q,stepx,stepy,textcolor,background)
		writeOnImg(im,txt,q,stepx,stepy,textcolor,gs,'it')
	#working_slice.save('results/bubble/bubble_'+str(i)+'.png')

print('cerco il file')
num=0
while(os.path.exists('results/testing_'+str(num)+"_"+filename)):
	#print('Esiste '+str(num))
	num=num+1
print("Salvato in "+str(num))
im.save('results/testing_'+str(num)+"_"+filename)
