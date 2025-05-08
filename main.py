import cv2
import cvzone
import numpy as np
from cvzone.ColorModule import ColorFinder
import pickle

#marcusboard oben links 2,3; oben rechts 2072,3; unten links 1, 1167; unten rechts 2072, 1167


# - Dartpfeile müssen deutlich farbig sein und nicht ähnlich wie die Scheibe sein
# - Kamera muss fest und stabil sein --> darf sich nicht bewegen
# - gute Bildqualität, kein bis wenig Schatten zb


# - Code funktioniert gerade nur für Video, für live: cap = cv2.VideoCapture(0) setzen oder so 
# - Was sind Polygone? Ein Polygon ist eine geometrische Fläche, die aus mehreren geraden Linien besteht und 
#   eine geschlossene Form bildet ( Dreieck = 3 Punkte, Viereck = 4 Punkte usw).
#   Kontext Dartscheibe: man erstellt Flächen denen eine Punktzahl zugeordnet ist. In PathPicker.py erstellt man Polygone

cap = cv2.VideoCapture('C:\\Users\\padav\\OneDrive\\Dokumente\\OpenCV\\DartTutorial\\Videos\\Video10.MOV')

 
frameCounter = 0

cornerPoints = [[700, 30], [3000, 30], [700, 2000], [3000, 2000]]

colorFinder = ColorFinder(False)
#hsvVals = {'hmin': 0, 'smin': 42, 'vmin': 0, 'hmax': 25, 'smax': 74, 'vmax': 130} #metall barrel
hsvVals = {'hmin': 0, 'smin': 119, 'vmin': 126, 'hmax': 17, 'smax': 255, 'vmax': 255} #roter schaft
countHit = 0
imgListBallsDetected = []
hitDrawBallInfoList = []
totalScore = 0
with open('C:\\Users\\padav\\OneDrive\\Dokumente\\OpenCV\\DartTutorial\\polygons', 'rb') as f:
    polygonsWithScore = pickle.load(f)
'''
hsvVals = {'hmin': 30, 'smin': 34, 'vmin': 0, 'hmax': 41, 'smax': 255, 'vmax': 255}
countHit = 0
imgListBallsDetected = []
hitDrawBallInfoList = []
totalScore = 0
'''
#with open('C:\\Users\\padav\\OneDrive\\Dokumente\\OpenCV\\DartTutorial\\polygons', 'rb') as f:
 #   polygonsWithScore = pickle.load(f)


# print(polygonsWithScore)

#bringt das Bild in eine gerade zentrale Perspektive, also als wäre Kamera frontal drauf
def getBoard(img):
    width, height = int(2072), int(1167)
    
    pts1 = np.float32(cornerPoints)
    pts2 = np.float32([[0,0],[width,0],[0,height],[width,height]])
    matrix = cv2.getPerspectiveTransform(pts1, pts2)
    imgOutput = cv2.warpPerspective(img, matrix,(width, height))
    for x in range(4):
        cv2.circle(img, (cornerPoints[x][0], cornerPoints[x][1]), 25 ,(0,255,0), cv2.FILLED)
    imgOutput = cv2.resize(imgOutput, (1280, 720))
    return imgOutput


def detectColorDarts(img):
    #img = cv2.resize(img, (1280, 720))
    imgBlur = cv2.GaussianBlur(img, (7, 7),2)
    imgColor, mask = colorFinder.update(imgBlur, hsvVals)
    
    kernel = np.ones((7, 7), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.medianBlur(mask, 9)
    mask = cv2.dilate(mask, kernel, iterations=4)
    kernel = np.ones((9, 9), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    cv2.imshow("Image Color", imgColor)
    '''
    imgBlur = cv2.GaussianBlur(img, (7, 7), 2)
    imgColor, mask = colorFinder.update(imgBlur, hsvVals)
    kernel = np.ones((7, 7), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.medianBlur(mask, 9)
    mask = cv2.dilate(mask, kernel, iterations=4)
    kernel = np.ones((9, 9), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    #cv2.imshow("Image Color", imgColor)
   '''
    return mask
    

while True:
    #img = cv2.imread('C:\\Users\\padav\\OneDrive\\Dokumente\\OpenCV\\DartTutorial\\marcus_imgBoard_with_dart.png')
    #imgColor, mask = colorFinder.update(img)
    #img = cv2.resize(img, (1580, 920))  # oder kleiner, z.B. (960, 540)
    #img = cv2.resize(img, (1280, 720))
    frameCounter += 1 
    if frameCounter == cap.get(cv2.CAP_PROP_FRAME_COUNT): #Checking how many frames are in the video
        frameCounter = 0
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0) ##if reached max set back to 0

    success, img = cap.read()
    if not success or img is None:
        print("❌ Kein Frame mehr verfügbar – Neustart")
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        continue
    
    imgBoard = getBoard(img)
    imgBoard = cv2.resize(imgBoard,(1280, 720))
    mask = detectColorDarts(imgBoard)
    for oldMask in imgListBallsDetected:
        mask = cv2.subtract(mask, oldMask)
        # cv2.imshow(str(x), mask)
    imgContours, conFound = cvzone.findContours(imgBoard, mask, 500)

    if conFound:
        countHit += 1
        if countHit == 10:
            imgListBallsDetected.append(mask)
            print("Hit Detected")
            countHit = 0
            for polyScore in polygonsWithScore:
                center = conFound[0]['center']
                poly = np.array([polyScore[0]], np.int32)
                inside = cv2.pointPolygonTest(poly, center, False) # prüft ob Dartpfeil innerhalb des Polygoms liegt
                print(inside)
                if inside == 1:
                    print("Yes")
                    hitDrawBallInfoList.append([conFound[0]['bbox'], conFound[0]['center'], poly])
                    totalScore += polyScore[1]
    print(totalScore)
    imgBlank = np.zeros((imgContours.shape[0], imgContours.shape[1], 3), np.uint8)

    for bbox, center, poly in hitDrawBallInfoList:
        cv2.rectangle(imgContours, bbox, (255, 0, 255), 2)
        cv2.circle(imgContours, center, 5, (0, 255, 0), cv2.FILLED)
        cv2.drawContours(imgBlank, poly, -1, color=(0, 255, 0), thickness=cv2.FILLED)


    imgBoard = cv2.addWeighted(imgBoard, 0.7, imgBlank, 0.5, 0)

    imgBoard,_ = cvzone.putTextRect(imgBoard, f'Total Score: {totalScore}',
                                  (10, 40), scale=2, offset=20)

    imgStack = cvzone.stackImages([imgContours, imgBoard], 2, 1)
   
    '''
    ### Remove Previous Detections
    for x, img in enumerate(imgListBallsDetected):
        mask = mask - img
        # cv2.imshow(str(x), mask)

    imgContours, conFound = cvzone.findContours(imgBoard, mask, 3500)

    if conFound:
        countHit += 1
        if countHit == 10:
            imgListBallsDetected.append(mask)
            # print("Hit Detected")
            countHit = 0
            for polyScore in polygonsWithScore:
                center = conFound[0]['center']
                poly = np.array([polyScore[0]], np.int32)
                inside = cv2.pointPolygonTest(poly, center, False) # prüft ob Dartpfeil innerhalb des Polygoms liegt
                print(inside)
                if inside == 1:
                    print("Yes")
                    hitDrawBallInfoList.append([conFound[0]['bbox'], conFound[0]['center'], poly])
                    totalScore += polyScore[1]
    print(totalScore)
    imgBlank = np.zeros((imgContours.shape[0], imgContours.shape[1], 3), np.uint8)

    for bbox, center, poly in hitDrawBallInfoList:
        cv2.rectangle(imgContours, bbox, (255, 0, 255), 2)
        cv2.circle(imgContours, center, 5, (0, 255, 0), cv2.FILLED)
        cv2.drawContours(imgBlank, poly, -1, color=(0, 255, 0), thickness=cv2.FILLED)


    imgBoard = cv2.addWeighted(imgBoard, 0.7, imgBlank, 0.5, 0)

    imgBoard,_ = cvzone.putTextRect(imgBoard, f'Total Score: {totalScore}',
                                  (10, 40), scale=2, offset=20)

    imgStack = cvzone.stackImages([imgContours, imgBoard], 2, 1)
    '''
    #imgBoard = cv2.resize(imgBoard,(1280, 720))
    #imgBoard = cv2.resize(imgBoard,(800, 600))
    #cv2.imwrite('marcus_imgBoard_without_dart.png',imgBoard)
    #cv2.imshow("Image", img)
    
    #cv2.imshow("Image", img)
    cv2.imshow("Image Board", imgBoard)
    #cv2.imshow("Image Color", imgColor)

    cv2.imshow("Image Mask", mask)
    #cv2.imshow("Image Contours", imgStack)
    cv2.imshow("Image Contours", imgContours)

    cv2.waitKey(1)
