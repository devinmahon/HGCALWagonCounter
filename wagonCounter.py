import pandas as pd
import numpy as np
from collections import Counter
import itertools
import wagonDrawer
import sys
import time
import copy
import os
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

pd.set_option('display.max_columns', None)

# Return true if the modules are ordered such that each one touches the previous one
def checkContiguity(group):

  group = group[['u','v']].diff()
  group['diff'] = list(zip(group.u,group.v))
  group['touchPrev'] = group['diff'].apply(lambda x: True if x in [(1,0),(1,1),(0,1),(-1,0),(-1,-1),(0,-1)] else False)
  group.loc[group.index[0],'touchPrev'] = True
  if group['touchPrev'].all():
    return True, -1
  else:
    return False, group.index.get_loc(group[group.touchPrev == False].iloc[0].name) # Index of first non-touching module

# Properly order the modules
def makeContiguous(group):

  nModules = group.shape[0]
  nomSequence = list(range(nModules)) #list(range(nModules - 1) + np.ones(nModules - 1,dtype=int))
  orderings = list(itertools.permutations(nomSequence))
  orderings = orderings[1:] # First one is the nominal ordering
  groupTemp = group.copy()
  for ordering in orderings:
    isContiguous, badIndex = checkContiguity(groupTemp)
    if isContiguous:
      break
    else:
      #groupTemp.iloc[nomSequence] = group.iloc[list(ordering)]
      
      groupTemp = group.iloc[list(ordering)]
  group = groupTemp
  #print(checkContiguity(group))
  #print(checkContiguity(group)[0])
  if not checkContiguity(group)[0]:
    print('ERROR: Could not make wagon contiguous')
    print(group)

  return group

def dictDifferences(dict1, dict2):
  for key in dict1.keys():
    if key in dict2.keys():
      diff = len(dict2[key]) - len(dict1[key])
      if diff != 0:
        print(str(key) + ": " + str(len(dict1[key])) + ", " + str(diff))

def reverseCode(code):
  preCode = code[:3]
  labels = code[3::3]
  labelsReversed = tuple(reversed(labels))
  codes = [x for x in code[3:] if x not in labels]
  codes = [codes[n:n+2] for n in range(0, len(codes), 2)]
  if codes.count([3, 0]) != len(codes):
    return code
  codesReversed = reversed(codes)
  codesReversed = [list(((x[0] - x[1] - 3) % 6, (6 - x[1]) % 6)) for x in codesReversed]
  codesReversed = [x for grouping in codesReversed for x in grouping]
  middleCode = [list(labelsReversed[int(i / 2)]) + codesReversed[i:i+2] for i in range(0, len(codesReversed), 2)]
  newCode = list(preCode) + [x for ele in middleCode for x in ele] + list(labelsReversed[-1])
  return tuple(newCode)

def recode(code):
  wagonLength = len(code[3::3])
  wagonTypes = code[3::3]
  if wagonTypes.count('F') != wagonLength:
    return code
  if code[1] == 0:
    return code
  elif code[1] == -1:
    return reverseCode(code)
  else:
    engineIndex = code[1]
    if engineIndex != wagonLength - 1:
      # print("Recoding not possible; returning original code")
      return code
    return reverseCode(code)

def getUVDiff(plane,angle):

  angle %= 6

  if plane > 26 or plane % 2:
    uDiff = {0: 1, 1: 1, 2: 0, 3: -1, 4: -1, 5:  0}
    vDiff = {0: 0, 1: 1, 2: 1, 3:  0, 4: -1, 5: -1}
  else:
    uDiff = {0: -1, 1:  0, 2: 1, 3:  1, 4:  0, 5: -1}
    vDiff = {0:  0, 1:  1, 2: 1, 3:  0, 4: -1, 5: -1}

  return uDiff[angle],vDiff[angle]

def findEngine(code,wagonCodesDict,geomGrouped):

  if code[1] != -1:
    return code[1]

  moduleTypes = list(code[3::3])
  if len(moduleTypes) == 1:
    return 0
  if moduleTypes.count('F') == 1:
    return moduleTypes.index('F')

  earliestWagonID = wagonCodesDict[code][0]
  earliestWagon = geomGrouped.get_group((earliestWagonID[0], earliestWagonID[1], earliestWagonID[2]))
  earliestWagonPartner = geomGrouped.get_group((earliestWagonID[0], earliestWagonID[1], not earliestWagonID[2]))

  u,v,irot,plane = earliestWagonPartner.loc[earliestWagonPartner['isEngine'],['u','v','irot','plane']].values.flatten().tolist()
 
  uEastEngine,vEastEngine = [sum(x) for x in zip([u,v],list(getUVDiff(plane,irot)))]

  coords = earliestWagon[['u','v']].values.tolist()
  index = [i for i in range(len(coords)) if coords[i] == [uEastEngine,vEastEngine]][0]

  return index

def findEastEngineModule(plane,uWest,vWest,irotWest):

  uEastEngine,vEastEngine = [sum(x) for x in zip([uWest,vWest],list(getUVDiff(plane,irotWest)))]
  return uEastEngine,vEastEngine

def nextModule(plane,u,v,irot,angle,orient):

  uNext,vNext = [sum(x) for x in zip([u,v],list(getUVDiff(plane,angle+irot)))]
  return uNext,vNext,(irot+orient)%6

def reverseAngleOrient(angle,orient):

  return (angle + 3 - orient) % 6,(orient * -1) % 6

##################################################
# MAIN
##################################################
def main():

  # Rounding (decimal places)
  dec = 3

  # Configuration parameters
  threesSeparate = False
  halvesSemisSame = False
  halvesSemisFivesSame = True
  LDHDBoth = 0

  # Specify the geometry file to be used
  #geomVersion = 'v15.3_NadjaOct2023'
  #geometryPath = 'geometries/{}/'.format(geomVersion)
  geomVersion = 'v15.3'
  geometryPath = '../hgcal_modmap/geometries/{}/'.format(geomVersion)
  geometryFile = 'geometry.hgcal'

  # Extract required columns
  geom = pd.read_csv('{0}{1}.txt'.format(geometryPath,geometryFile),delim_whitespace=True)
  geomBasic = geom[['plane','u','v','x0','y0', 'vx_0', 'vy_0', 'vx_1', 'vy_1', 'vx_2', 'vy_2', 'vx_3', 'vy_3', 'vx_4', 'vy_4', 'vx_5', 'vy_5', 'vx_6', 'vy_6', 'itype','irot','MB','wagon','isEngine','HDorLD','trigLinks','dataLinks_ld','dataLinks_hd','icassette']].copy()

  geomBasic['irot'] = geomBasic['irot'].astype('int')

  if not threesSeparate: geomBasic = geomBasic[~geomBasic['itype'].str.contains('c')] # Threes don't affect wagon shape

  # Add distance from origin
  geomBasic['r'] = np.sqrt(geomBasic['x0']**2 + geomBasic['y0']**2)

  # HD
  geomBasic.loc[(geomBasic['HDorLD']) & (geomBasic['itype'].str.contains('aIe')),'irot'] += 3

  geomBasic['irot'] %= 6
  #geomBasic['itype'] = geomBasic['itype'].str[0]

  if halvesSemisSame: 

    geomBasic['itype'] = geomBasic['itype'].str[0]
    geomBasic.loc[geomBasic['itype'] == 'A','itype'] = 'D'
    geomBasic.loc[geomBasic['itype'] == 'a','itype'] = 'd'

  elif halvesSemisFivesSame:

    # LD halves(aOe + T/B)
    geomBasic.loc[(geomBasic['itype'].str[0] == 'a') & (geomBasic['itype'].str[-1] == 'B'),'irot'] += 5
    geomBasic.loc[(geomBasic['itype'].str[0] == 'a') & (geomBasic['itype'].str[-1] == 'T'),'irot'] += 1
  
    # LD semis (dOe + R/L)
    geomBasic.loc[(geomBasic['itype'].str[0] == 'd') & (geomBasic['itype'].str[-1] == 'R'),'irot'] += 0
    geomBasic.loc[(geomBasic['itype'].str[0] == 'd') & (geomBasic['itype'].str[-1] == 'L'),'irot'] += 3
  
    # LD fives (bOe + RL/LR)
    geomBasic.loc[(geomBasic['itype'].str[0] == 'b') & (geomBasic['itype'].str[-2:] == 'RL'),'irot'] += 3
    geomBasic.loc[(geomBasic['itype'].str[0] == 'b') & (geomBasic['itype'].str[-2:] == 'LR'),'irot'] += 3
 
    geomBasic['itype'] = geomBasic['itype'].str[0]
    geomBasic.loc[geomBasic['itype'] == 'a','itype'] = 'd'
    geomBasic.loc[geomBasic['itype'] == 'b','itype'] = 'd'

    geomBasic['irot'] %= 6

  else: geomBasic['itype'] = geomBasic['itype'].str[0]


  #  Specify the file with the fiber counts
  fiberCountsFile = 'fiberCounts/fiberCounts_220221_163022.txt'
  fiberCounts = pd.read_csv(fiberCountsFile,delim_whitespace=True,dtype={'TlpGBT':'Int64'})
  geomBasic = pd.merge(geomBasic, fiberCounts,  how='left', on=['plane','MB'])

  # Get a subset (if needed)
  #geomBasic = geomBasic[(geomBasic['plane'] <= 28) | (geomBasic['plane'] >= 37)]
  if LDHDBoth == 0: 	geomBasic = geomBasic[geomBasic['HDorLD'] == 0]
  elif LDHDBoth == 1: 	geomBasic = geomBasic[geomBasic['HDorLD'] == 1]

  # Remove impossible wagons
  removeWagons = [[3,2,0],[3,102,0],[5,2,0],[5,102,0],[3,0,0],[3,100,0],[5,0,0],[5,100,0]]
  for w in removeWagons:
    geomBasic = geomBasic.drop(geomBasic[(geomBasic['plane'] == w[0]) & (geomBasic['MB'] == w[1]) & (geomBasic['wagon'] == w[2])].index)

  #geomBasic = geomBasic[((geomBasic['plane'] < 4) & (geomBasic['MB'] < 4)) | ((geomBasic['plane'] == 1) & (geomBasic['MB'] == 11))]
  #geomBasic = geomBasic[(geomBasic['plane'] <= 4)]

  # Group modules by plane (layer), MB index, and wagon index
  geomGrouped = geomBasic.sort_values('r',ascending=True).groupby(['plane','MB','wagon'])

  #print(geomGrouped.get_group((1,4,0)))
  #print('#'*50)
  #print(geomGrouped.get_group((1,10,1)))

  wagonCodes = []
  wagonCodesDict = {}
  for name, group in geomGrouped:
    
    newCode = []

    # Ensure that ordering of modules is contiguous
    group = makeContiguous(group)    

    # Add code for HD/LD
    if group['HDorLD'].astype(bool).all():
      newCode.append(1)
    elif (~group['HDorLD'].astype(bool)).all():
      newCode.append(0)
    else:
      print('ERROR: Train contains both HD and LD modules. MB:',group.loc[0,'MB'])

    # Add code for isEngine (for west wagons set index of engine, for east wagons set to -1)
    #newCode.append(1) if (group['isEngine'] == True).any() else newCode.append(0)
    try: enginePos = list(group['isEngine'] == True).index(True)
    except ValueError: enginePos = -1
    newCode.append(enginePos)   

    # Add placeholder code for crossover trigger links (# of outgoing links)
    newCode.append(0)

    # Determine angles and orientation codes
    irotPrev, uPrev, vPrev = -999 * np.ones(3,dtype=int)
    i = 0
    for rowIndex, row in group.iterrows():

      # Odd CE-E layer flag
      isOdd = row['plane'] % 2 or row['plane'] > 26

      irotCurr = row['irot']
      uCurr    = row['u']
      vCurr    = row['v']

      # Fixing rotations in even layers
      #if not isOdd and not row['itype'] == 'F': irotCurr -= 3

      if i != 0:
        
        # Angle code
        deltaU = uCurr - uPrev
        deltaV = vCurr - vPrev

        if deltaU == 1 and deltaV == 0:
          angle = 0 if isOdd else 3
        elif deltaU == 1 and deltaV == 1:
          angle = 1 if isOdd else 2
        elif deltaU == 0 and deltaV == 1:
          angle = 2 if isOdd else 1
        elif deltaU == -1 and deltaV == 0:
          angle = 3 if isOdd else 0
        elif deltaU == -1 and deltaV == -1:
          angle = 4 if isOdd else 5
        elif deltaU == 0 and deltaV == -1:
          angle = 5 if isOdd else 4
        else:
          print('ERROR: Invalid angle. plane:',row['plane'],'u:',row['u'],'v:',row['v'])
          print(group)
        
        angleCode = (angle - irotPrev) % 6
        newCode.append(angleCode)

        # Orientation code
        orientCode = (irotCurr - irotPrev) % 6
        newCode.append(orientCode)

      newCode.append(row['itype'])
      
      irotPrev = irotCurr
      uPrev    = uCurr
      vPrev    = vCurr
      i += 1
  
    wagonCodes.append(newCode)
    wagonCodesDict.setdefault(tuple(newCode),[]).append([row['plane'],row['MB'],row['wagon']])

  # Get all unique wagons
  codeCounter = Counter([tuple(i) for i in wagonCodes])

  # Consolidate 180 degree rotations
  duplicateCodes = [] 
  for wagon in list(codeCounter.keys()):
    if len(wagon) == 4:
      continue
    preCodes = wagon[0:3] #wagon[0:2]
    if preCodes[1] != -1:
      preCodesRot = [preCodes[0],list(reversed(list(range(int(len(wagon)/3)))))[preCodes[1]],preCodes[2]]
    else:
      preCodesRot = preCodes
    labels = wagon[3:][::3]
    codes = [x for x in wagon[3:] if x not in labels]
    codes = [codes[n:n+2] for n in range(0,len(codes),2)]
    labelsRot = tuple(reversed(labels))
    codesRot = tuple(reversed (codes))
    codesRot = [[(x[0]+6-(x[1]+3))%6,(6-x[1])%6] for x in codesRot]
    wagonRot = list(preCodesRot) + [x for sublist in [[labelsRot[i]] + codesRot[i] for i in range(len(labelsRot)-1)] for x in sublist] + [labelsRot[-1]]
    #print('rotated:',wagonRot)

    wagonRot = tuple(wagonRot)
    if wagonRot in codeCounter and not wagonRot in duplicateCodes and wagon != wagonRot:

      for id in wagonCodesDict[wagonRot]:
        geomBasic.loc[(geomBasic['plane'] == id[0]) & (geomBasic['MB'] == id[1]) & (geomBasic['wagon'] == id[2]),'r'] *= -1

      codeCounter[wagon] += codeCounter[wagonRot]
      duplicateCodes.append(wagon)
      codeCounter.pop(wagonRot,None)

      wagonCodesDict[wagon] = wagonCodesDict[wagon] + wagonCodesDict[wagonRot]
      wagonCodesDict.pop(wagonRot)

  geomGrouped = geomBasic.sort_values('r',ascending=True).groupby(['plane','MB','wagon'])

  def maxLinksCalculation(code, dict1 = wagonCodesDict):
    lenWagon = len(code[3::3])
    maxLinksList = []
    for i in range(lenWagon):
      maxLinksList.append(0)
    for loc in dict1[code]:
      wagonLoc = geomGrouped.get_group((loc[0], loc[1], loc[2]))
      numTrigLinks = [int(x) for x in wagonLoc['trigLinks'].tolist()]
      for j in range(len(numTrigLinks)):
        if numTrigLinks[j] > maxLinksList[j]:
          maxLinksList[j] = numTrigLinks[j]
    return maxLinksList

  maxLinks = {x:maxLinksCalculation(x, wagonCodesDict) for x in wagonCodesDict}

  numTrigLinksHDLT15 = 0
  numHD = 0

  wagonCodesDictCopy = copy.deepcopy(wagonCodesDict)
  for key, value in wagonCodesDictCopy.items():
    maxTrigLinks = []
    numDataLinksHDGT7 = 0
    for id in value:
      wagonTemp = geomGrouped.get_group((id[0],id[1],id[2])) #geomBasic[(geomBasic['plane'] == id[0]) & (geomBasic['MB'] == id[1]) & (geomBasic['wagon'] == id[2])]#.sort_values('r',ascending=True)
      numTrigLinks = [int(x) for x in wagonTemp['trigLinks'].tolist()]
      totTrigLinks = sum(numTrigLinks)
      totMaxLinks = sum(maxLinks[key])
      if key[0] == 0: numDataLinks = [int(x) for x in wagonTemp['dataLinks_ld'].tolist()]
      else          : numDataLinks = [int(x) for x in wagonTemp['dataLinks_hd'].tolist()]
      if key[0] == 1 and sum(numDataLinks) > 7: numDataLinksHDGT7 += 1
      #print(numTrigLinks)
      #print(numTrigLinks,maxTrigLinks)

      if key[0] == 1: 
        numHD += 1
        if totTrigLinks <= 14: numTrigLinksHDLT15 += 1

      # Analyze crossovers
      doConsol = True
      isNew = False
      if key[0] == 0:
        idPartner = [id[0],id[1],int(not id[2])]
        wagonTempPartner = geomGrouped.get_group((idPartner[0],idPartner[1],idPartner[2]))
        numTrigLinksPartner = [int(x) for x in wagonTempPartner['trigLinks'].tolist()]
        totTrigLinksPartner = sum(numTrigLinksPartner)
        # Overflow links
        if totTrigLinks > 7:
          isNew = True
          x1 = totTrigLinks - 7
          x2 = -x1
        # Unambiguous LpGBT consolidation
        elif doConsol and totTrigLinks != 0 and totTrigLinks > 3 and totTrigLinksPartner <= 3 and totTrigLinksPartner <= (7 - totTrigLinks):
          isNew = True
          x1 = -totTrigLinksPartner
          x2 = totTrigLinksPartner
        # Ambiguous LpGBT consolidation (wagon with engine receives the crossovers (key[1] != -1), for the opposite, do key[1] == -1)
        elif doConsol and key[1] != -1 and totTrigLinks != 0 and totTrigLinks <= 3 and totTrigLinksPartner <= 3:
          #print('Ambiguous:',id)
          isNew = True
          x1 = -totTrigLinksPartner
          x2 = totTrigLinksPartner
        if isNew:
          # Make new codes
          oldCode1 = key
          newCode1 = list(oldCode1)
          newCode1[2] = x1
          newCode1 = tuple(newCode1)
          for k,v in wagonCodesDict.items():
            if idPartner in v:
              oldCode2 = k
          newCode2 = list(oldCode2)
          newCode2[2] = x2
          newCode2 = tuple(newCode2)

          # Remove old ids
          codeCounter[oldCode1] -= 1
          codeCounter[oldCode2] -= 1
          wagonCodesDict[oldCode1].remove(id)
          wagonCodesDict[oldCode2].remove(idPartner)  
          # Add new ids
          if newCode1 in codeCounter:
            codeCounter[newCode1] += 1
            wagonCodesDict[newCode1] = wagonCodesDict[newCode1] + [id]
          else:
            codeCounter[newCode1] = 1
            wagonCodesDict[newCode1] = [id]
          if newCode2 in codeCounter:
            codeCounter[newCode2] += 1
            wagonCodesDict[newCode2] = wagonCodesDict[newCode2] + [idPartner]
          else:
            codeCounter[newCode2] = 1
            wagonCodesDict[newCode2] = [idPartner]

      # Trigger links
      if not len(maxTrigLinks): maxTrigLinks = numTrigLinks
      else: 
        maxTrigLinks = np.maximum(maxTrigLinks,numTrigLinks)

  # Recoding
  wagonCodesDictCopy = copy.deepcopy(wagonCodesDict)
  recodedCodesList = []
  for code in wagonCodesDictCopy:
      recodedCode = recode(code)
      if recodedCode != code:
        codeCounter[recodedCode] = codeCounter[code]
        codeCounter.pop(code)
        wagonCodesDict[recodedCode] = wagonCodesDict[code]  
        
        wagonCodesDict.pop(code)
        recodedCodesList.append(recodedCode)

  wagonCodesDict = {x:y for x, y in wagonCodesDict.items() if len(y) > 0}
  wagonCodesDictCopy = copy.deepcopy(wagonCodesDict)
  removedWagonsList = []
  removedWagonsDict = {x:[] for x in wagonCodesDict}
  wagonMovementDict = {x:[] for x in wagonCodesDict}

  # Get all codes that are the same except for # of incoming/outgoing links
  def getGroupedCodes(wagonDict):
    groupedCodes = {}
    for code in wagonDict:
      codeTemp = list(code)
      del codeTemp[2]
      if tuple(codeTemp) in groupedCodes: groupedCodes[tuple(codeTemp)].append(code)
      else: groupedCodes[tuple(codeTemp)] = [code]
    return groupedCodes

  # Consolidate based on incoming links

  incomingWagonCodesDict = {x:wagonCodesDictCopy[x] for x in wagonCodesDictCopy.keys() if x[2] <= 0}
  incomingWagonCodesCopy = copy.deepcopy(incomingWagonCodesDict)

  # Run 4 times to allow 0-3 incoming links
  for deltaLinks in [1,2,3]:
    #print('Trying to add {} incoming links'.format(deltaLinks))
    for iPass in range(int(3/deltaLinks)):
      changes = 0
      newCodesPass = []
      for metacode, codes in getGroupedCodes(incomingWagonCodesCopy).items():
        for code in [x for x in codes if x[0] == 0]:
          canAddLink = True
          # Make sure this code still exists after any previous consolidations
          if code not in wagonCodesDict: continue
          # Make sure we haven't already consolidated to this code in this pass
          if code in newCodesPass: continue
          newCode = list(code)
          newCode[2] -= deltaLinks
          newCode = tuple(newCode)
          for loc in wagonCodesDict[code]:
            numLinks = sum([int(x) for x in geomGrouped.get_group((loc[0], loc[1], loc[2]))['trigLinks'].tolist()]) - code[2]
            # Get partner info
            locPartner = [loc[0],loc[1],int(not loc[2])]
            #numLinksPartner = sum([int(x) for x in geomGrouped.get_group((locPartner[0], locPartner[1],locPartner[2]))['trigLinks'].tolist()])
            index = 99999
            for i,val in enumerate(wagonCodesDict.values()):
              if locPartner in val:
                index = i
            if index == 99999: print('ERROR: Wagon partner with location',locPartner,'not found')
            codePartner = list(wagonCodesDict.keys())[index]
            newCodePartner = list(codePartner)
            newCodePartner[2] += deltaLinks
            newCodePartner = tuple(newCodePartner)
            # Only allow an extra incoming link if 1) taking it gives <= 7 links, 2) taking it doesn't make > 3 xovers, 3) the new code already exists, and 4) all of the new partner codes also exist
            if not ((numLinks + deltaLinks) <= 7 and newCode[2] >= -3 and newCode in wagonCodesDict and newCode != newCodePartner):
            #if not (newCode in wagonCodesDict and newCode != newCodePartner):
              canAddLink = False
              break
          if canAddLink: 
            #print(code,'can be changed to',newCode)
            changes += 1
            # Do the consolidation
            wagonCodesDict[newCode] = wagonCodesDict[newCode] + wagonCodesDict[code]
            wagonCodesDict.pop(code)
            wagonCodesDict = {x:y for x, y in wagonCodesDict.items() if len(y) > 0}
            newCodesPass.append(newCode)
          
      #print(changes,'can be consolidated in pass',iPass)

  # Consolidate outgoing links
  
  outgoingWagonCodesDict = {x:wagonCodesDictCopy[x] for x in wagonCodesDictCopy.keys() if x[2] >= 0}
  outgoingWagonCodesDictCopy = copy.deepcopy(outgoingWagonCodesDict)

  for deltaLinks in [1,2,3]:
    #print('Trying to add {} outgoing links'.format(deltaLinks))
    # Run 4 times to allow 0-3 outgoing links
    for iPass in range(int(3/deltaLinks)):
      changes = 0
      newCodesPass = []
      for metacode, codes in getGroupedCodes(outgoingWagonCodesDictCopy).items():
        for code in [x for x in codes if x[0] == 0]:
          canAddLink = True
          # Make sure this code still exists after any previous consolidations
          if code not in wagonCodesDict: continue
          # Make sure we haven't already consolidated to this code in this pass
          if code in newCodesPass: continue
          newCode = list(code)
          newCode[2] += deltaLinks
          newCode = tuple(newCode)
          for loc in wagonCodesDict[code]:
            #numLinks = sum([int(x) for x in geomGrouped.get_group((loc[0], loc[1], loc[2]))['trigLinks'].tolist()]) - code[2]
            # Get partner info
            locPartner = [loc[0],loc[1],int(not loc[2])]
            numLinksPartner = sum([int(x) for x in geomGrouped.get_group((locPartner[0], locPartner[1],locPartner[2]))['trigLinks'].tolist()]) + code[2]
            index = 99999
            for i,val in enumerate(wagonCodesDict.values()):
              if locPartner in val:
                index = i
            if index == 99999: print('ERROR: Wagon partner with location',locPartner,'not found')
            codePartner = list(wagonCodesDict.keys())[index]
            newCodePartner = list(codePartner)
            newCodePartner[2] -= deltaLinks
            newCodePartner = tuple(newCodePartner)
            # Only allow an extra outgoing link if 1) sending it gives <= 7 links on partner, 2) taking it doesn't make > 3 xovers, 3) the new code already exists, and 4) all of the new partner codes also exist
            #if not ((numLinksPartner + deltaLinks) <= 7 and (newCode[2]) <= 3 and newCode in wagonCodesDict and newCode != newCodePartner):
            if not (newCode[2] <= 3 and newCode in wagonCodesDict and newCode != newCodePartner):
              canAddLink = False
              break
          if canAddLink: 
            #print(code,'can be changed to',newCode)
            changes += 1
            # Do the consolidation
            wagonCodesDict[newCode] = wagonCodesDict[newCode] + wagonCodesDict[code]
            wagonCodesDict.pop(code)
            wagonCodesDict = {x:y for x, y in wagonCodesDict.items() if len(y) > 0}
            newCodesPass.append(newCode)
          
      #print(changes,'can be consolidated in pass',iPass)

  codeCounter = Counter({tuple(key):len(val) for key,val in wagonCodesDict.items()})

  wagonCodesDict = {x:y for x, y in wagonCodesDict.items() if len(y) > 0}

  # Finding max. links on each module on each wagon type
  maxLinks = {x:maxLinksCalculation(x, wagonCodesDict) for x in wagonCodesDict}

  # Removed Wagons
  removedWagonsDict = {x:y for x, y in removedWagonsDict.items() if x in removedWagonsList}
  wagonMovementDict = {x:y for x, y in wagonMovementDict.items() if x in removedWagonsList}
  wagonMovementSummaryFile = 'movementsummary'
  with open('{}.txt'.format(wagonMovementSummaryFile), 'w') as f:
    for wagon, movements in wagonMovementDict.items():
      for receivingWagon in movements:
        print("{0} moves {1} times into {2}".format(wagon, receivingWagon[1], receivingWagon[0]), file = f)
      print("\n", file = f)

  # Which links are getting sent where?
  outgoingMaxLinks = {x:maxLinks[x] for x in maxLinks if x[2] > 0}
  linksSummary = {x:[] for x in maxLinks if x[2] > 0}
 
  for code in wagonCodesDict:
    if code[2] > 0:
      numOutgoingLinks = code[2]
      maxLinksList = maxLinks[code]
      maxIndex = maxLinksList.index(max(maxLinksList))
      numUnaccountedFor = numOutgoingLinks

      for i in range(len(maxLinksList)):
        linksSummary[code].append(0)

      maxLinksListCopy = maxLinksList
      while numUnaccountedFor > 0:
        linksSummary[code][maxIndex] -= 1
        # print(maxLinks[code])
        maxLinksListCopy[maxIndex] -= 1
        # print(maxLinks[code])
        maxIndex = maxLinksListCopy.index(max(maxLinksListCopy))
        numUnaccountedFor -= 1
        # print('---')
      
      # Below spreads out the outgoing links for two module wagons, but this is not necessary
      #if linksSummary[code] == [-2, 0] or linksSummary[code] == [0, -2]:
      #  linksSummary[code] = [-1, -1]
      for i in range(len(maxLinksList)):
        maxLinksList[i] += -1 * linksSummary[code][i]
      maxLinks[code] = maxLinksList

  linksRoutingSummaryFile = 'link-routing-summary'
  with open("{}.txt".format(linksRoutingSummaryFile), 'w') as f:
    for code in linksSummary:
      linksInfoList = linksSummary[code]
      maxLinksList = maxLinks[code]
      print("{0}: {1} + {2}".format(code, maxLinksList, linksInfoList), file = f)

  # Finding engine pos. for east wagons
  eastEnginePositions = {x:findEngine(x, wagonCodesDict, geomGrouped) for x in wagonCodesDict if x[1] == -1 and x[0] == 0}  

  for code in eastEnginePositions:
    if code in recodedCodesList and code not in removedWagonsList:
      lenWagon = len(code[3::3])
      eastEnginePositions[code] = (lenWagon - 1) - eastEnginePositions[code]

  # Setting engineType column in new geometry file
  engineTypeDict = {}
  for code in wagonCodesDict:
    if code[1] == -1:
      position = eastEnginePositions[code]
    else:
      position = code[1]
    for location in wagonCodesDict[code]:
      wagon = geomGrouped.get_group((location[0], location[1], location[2]))
      plane = [x for x in wagon['plane'].tolist()]
      u = [x for x in wagon['u'].tolist()]
      v = [x for x in wagon['v'].tolist()]
      for i in range(len(plane)):
        module_loc = (plane[i], u[i], v[i])
        if i == position and code[1] == -1:
          engineTypeDict[module_loc] = 'E'
        elif i == position and code[1] != -1:
          engineTypeDict[module_loc] = 'W'
        else:
          engineTypeDict[module_loc] = 'N'
  
  geom.insert(44, 'engineType', ['N' for i in range(len(geom['plane']))])
  for i in range(len(geom['engineType'])):
    ele = geom['engineType'][i]
    ele_coords = (geom['plane'][i], geom['u'][i], geom['v'][i])
    if ele_coords in engineTypeDict:
      geom.loc[i,'engineType'] = engineTypeDict[ele_coords]

  geometryPath = geometryPath
  geometryFile_WithEngine = 'geom_with_east.hgcal'
  geomFilePath_WithEngine = '{0}{1}.txt'.format(geometryPath, geometryFile_WithEngine)
  geom = np.around(geom, decimals = 3)
  cols = [x for x in geom.columns]
  np.savetxt(geomFilePath_WithEngine, geom, fmt = '%s', header = ' '.join(cols))

  # Print message about total number of HD wagons with <= 14 trigger links
  #print(numTrigLinksHDLT15,'out of',numHD,'(','{:.1f}'.format(numTrigLinksHDLT15 * 100.0 / numHD),'%) HD wagons have <= 14 trigger links')

  # Remove empty Counter entries
  codeCounter = Counter({i:j for i,j in codeCounter.items() if j != 0})

  wagonNameDict = {
    '0000F1100F2000F2000F20'	: 'WE40A1',
    '0000F1100F2000F2005d20'	: 'WE31A1',
    '0030d1152F2030F2030F20'	: 'WE31A2',
    '0030F1130F2022F2024F20'	: 'WE40A2',
    '0000F1114F2012F2015d20'	: 'WE31A3',
    '0101F2030F2030F20'		: 'WW30A1',
    '0100F3030F2031d20'		: 'WW21A1',
    '0001F2000F2005d20'		: 'WE21A1',
    '0000F2000F2000F20'		: 'WE30A1',
    '0001F3000F2005d10'		: 'WE21B1',
    '0000F3015d2000d20'		: 'WE12A1',
    '0100F3121d2030d20'		: 'WW12A1',
    '0010F2030F2022F20'		: 'WE30A2',
    '0100F2014F2030F20'		: 'WW30B1',
    '0000F2014F2012F20'		: 'WE30A3',
    '0101F2030F2031d20'		: 'WW21B1',
    '0000F2015d2001F20'		: 'WE21C1',
    '0100F2022F2024F20'		: 'WW30B2',
    '0111F2000F2014F20'		: 'WW30A2',
    '0100F3014F2031d20'		: 'WE21D1',
    '0000F0022F0005d00'		: 'WW21C1',
    '0100F2020d2041d20'		: 'WE12B1',
    '0000F2010d2055d20'		: 'WW12B1',
    '0101F3030F2031d10'		: 'WW21D1',
    '0110d2044F2014F20'		: 'WW21E1',
    '0000F2010d2050F20'		: 'WE21C2',
    '0100F2020d2040F20'		: 'WW21E2',
    '0110F2000F2010d20'		: 'WW21E3',
    '0010F2030F2021d20'		: 'WE21C3',
    '0000F2014F2011d20'		: 'WE21C4',
    '0111d2040F2021d20'		: 'WW12C1',
    '0100F3130F41'		: 'WW20A1',
    '0000F3200F40'		: 'WE20A1',
    '0101F4031d20'		: 'WW11A1',
    '0001F4005d20'		: 'WE11A1',
    '0001F3000F30'		: 'WE20B1',
    '0010F3103F40'		: 'WE20C1',
    '0102F3030F20'		: 'WW20B1',
    '0100F4014F30'		: 'WW20C1',
    '0010d2052F20'		: 'WE11B1',
    '0101F3030F30'		: 'WW20D1',
    '0000F4021d20'		: 'WE11C1',
    '0111d2044F20'		: 'WW11B1',
    '0000F2015d20'		: 'WE11B2',
    '0000F2022F20'		: 'WE20D1',
    '0102F2031d20'		: 'WW11C1',
    '0002F2000F30'		: 'WE20E1',
    '0101F50'			: 'WW10A1',
    '0001F50'			: 'WE10A1',
    '0000F03'			: 'WE10B1',
    '0103F30'			: 'WW10B1',
  }

  if not os.path.exists('output/geometriesWagon/{}'.format(geomVersion)): os.makedirs('output/geometriesWagon/{}'.format(geomVersion))
  f = open('output/geometriesWagon/{}/geometryWagon.txt'.format(geomVersion),'w')

  f.write('plane u v itype x0 y0 irot nvertices vx_0 vy_0 vx_1 vy_1 vx_2 vy_2 vx_3 vy_3 vx_4 vy_4 vx_5 vy_5 vx_6 vy_6 icassette trigRate trigLinks dataRate_ld dataLinks_ld dataRate_hd dataLinks_hd MB wagon isEngine nROCs power mrot phi HDorLD hash hash_hdld engine_trig_fibres engine_data_fibres engine_ctrl_fibres dataPp0 trigPp0 dataPp0_type trigPp0_type dataPp1 trigPp1 dataPp1_type trigPp1_type dataPp2 DAQ\n')

  for tempCode,indices in wagonCodesDict.items():

    if tempCode[1] == -1: continue
    if not (len(tempCode) - 1) / 3 == 2: continue
    #print(tempCode)
    #print(indices)

    for index in indices:

      tempIndex = index

      #u,v,irot = geomBasic.loc[(geomBasic['plane'] == tempIndex[0]) & (geomBasic['MB']  == tempIndex[1]) & (geomBasic['wagon'] == tempIndex[2]) & (geomBasic['isEngine']),['u','v','irot']].values.flatten().tolist()
      geomTempIndex = geomBasic.loc[(geomBasic['plane'] == tempIndex[0]) & (geomBasic['MB']  == tempIndex[1]) & (geomBasic['wagon'] == tempIndex[2]) & (geomBasic['isEngine'])]
      u,v,irot = geomTempIndex[['u','v','irot']].iloc[0]

      if ''.join(str(x) for x in tempCode) in wagonNameDict: wagonName = wagonNameDict[''.join(str(x) for x in tempCode)]
      else: wagonName = 'XXXXXX'
      f.write('{} {} {} {}\n'.format(geomTempIndex.iloc[0]['plane'],u,v,wagonName))

      #print('M0:',u,v)
      #print('irot',irot)
      angleCode,orientCode = tempCode[4],tempCode[5]
      angleCode = (angleCode + irot) % 6
      #print('angleCode',angleCode)
      if angleCode == 0: 
        u += 1
      elif angleCode == 1:
        u += 1
        v += 1
      elif angleCode == 2:
        v += 1
      elif angleCode == 3:
        u -= 1
      elif angleCode == 4:
        u -= 1
        v -= 1
      elif angleCode == 5:
        v -= 1
      #print('M1:',u,v)

  #print(geomGrouped.get_group((20,11,1)))
  #print(geomGrouped.get_group((20,11,0)))
  #print(geomGrouped.get_group((19,11,0)))
  #print(geomGrouped.get_group((1,8,0)))
  #print(geomGrouped.get_group((1,8,1)))

  # Count no. of trigger lpGBTs required per variety and make histograms
  lpGBTCounts = {}
  maxTrigLinksPerFiber = {}
  for key, value in wagonCodesDict.items():
    if key[0] != 1: continue
    lpGBTCounts[key] = []
    #for id in value:
    #  numlpGBT = geomBasic[(geomBasic['plane'] == id[0]) & (geomBasic['MB'] == id[1]) & (geomBasic['wagon'] == id[2])]['TlpGBT'].iloc[0]
    #  if not pd.isna(numlpGBT) and numlpGBT != 0: 
    #    lpGBTCounts[key].append(numlpGBT)
    # Get maxTrigLinks for each variety per no. of TlpGBTs
    for i in [1,2,3,4]:
      maxTrigLinks = []
      for id in value:
        wagonTemp = geomGrouped.get_group((id[0],id[1],id[2]))
        numlpGBT = wagonTemp['TlpGBT'].iloc[0] #****
        if pd.isna(numlpGBT) or numlpGBT == 0 or numlpGBT != i: continue
        lpGBTCounts[key].append(numlpGBT)
        numTrigLinks = [int(x) for x in wagonTemp['trigLinks'].tolist()]
        totTrigLinks = sum(numTrigLinks)
        if not len(maxTrigLinks): maxTrigLinks = numTrigLinks
        else: 
          maxTrigLinks = np.maximum(maxTrigLinks,numTrigLinks)
      if len(maxTrigLinks): 
        maxTrigLinksPerFiber[key+(i,)] = []
        maxTrigLinksPerFiber[key+(i,)] = np.array(maxTrigLinks)
       
  for key,value in lpGBTCounts.items():
    ax = plt.figure().gca()
    plt.hist(value,bins=[1,2,3,4,5],orientation='horizontal')
    plt.xlabel('Counts')
    plt.ylabel('No. of Required Trigger lpGBTs')
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    # Add maxTrigLinks labels for each bin
    for i in [1,2,3,4]:
      if key+(i,) in maxTrigLinksPerFiber:
        plt.text(0.2,i+0.5,str(maxTrigLinksPerFiber[key+(i,)]),fontsize=14) 

    plt.savefig('output/fiberHistograms/hist_{}.png'.format(''.join([str(x) for x in key])))
    plt.clf()

  # Add link distribtion to codes
  wagonCodesDictCopy = copy.deepcopy(wagonCodesDict)
  codeCounterCopy = copy.deepcopy(codeCounter)
  maxLinksCopy = copy.deepcopy(maxLinks)
  #eastEnginePositionsCopy = copy.deepcopy(eastEnginePositions)
  for code in wagonCodesDict:
  
    # Compute new code
    newCode = list(code)
    nAdded = 0
    if code not in linksSummary: newCode[2] *= -1 # converting outgoing links code to incoming
    else: newCode[2] = 0
    for i,nLinks in enumerate(maxLinks[code]):
      newCode.insert(4+3*i+nAdded,format(nLinks,'x') if code not in linksSummary else format(nLinks + linksSummary[code][i],'x'))
      nAdded += 1
      newCode.insert(4+3*i+nAdded,0 if code not in linksSummary else -1*linksSummary[code][i])
      nAdded += 1

    # Change code[1] from engine position (or -1 for E) to E/W + engine position
    if code[1] == -1: # E wagons
      newCode[1] = 0
      newCode.insert(2,eastEnginePositions[code])
    else: # W wagons
      newCode.insert(1,1)

    # Replace old with new code
    codeCounterCopy[tuple(newCode)] = codeCounterCopy[code] 
    del codeCounterCopy[code]
    wagonCodesDictCopy[tuple(newCode)] = wagonCodesDictCopy[code]
    del wagonCodesDictCopy[code]
    maxLinksCopy[tuple(newCode)] = maxLinks[code]
    del maxLinksCopy[code]
    #if code[1] == -1: 
    #  eastEnginePositionsCopy[tuple(newCode)] = eastEnginePositionsCopy[code]
    #  del eastEnginePositionsCopy[code]

  wagonCodesDict = wagonCodesDictCopy
  codeCounter = codeCounterCopy
  maxLinks = maxLinksCopy
  #eastEnginePositions = eastEnginePositionsCopy

  # Split varieties if incoming links make a single link routing impossible
  incomingWagonCodesDict = {x:wagonCodesDict[x] for x in wagonCodesDict.keys() if x[3] > 0}
  for key,locs in incomingWagonCodesDict.items():
    if sum(maxLinks[key]) + key[3] > 7:
      linkConfigs = {}
      for loc in locs:
        wagonTemp = geomGrouped.get_group((loc[0],loc[1],loc[2]))
        numTrigLinks = tuple([int(x) for x in wagonTemp['trigLinks'].tolist()])
        if numTrigLinks in linkConfigs: linkConfigs[numTrigLinks] += [loc]
        else:                               linkConfigs[numTrigLinks] = [loc]
      # Merge any non-problematic link configurations into another one (first one in list)
      for linkConfig in copy.deepcopy(linkConfigs):
        if sum(linkConfig) + key[3] != 7:
          mergeInto = next(x for x in linkConfigs if x != linkConfig)
          linkConfigs[mergeInto] += linkConfigs[linkConfig]
          del linkConfigs[linkConfig]
      for linkConfig,locs in linkConfigs.items():
        newCode = list(key)
        for i,modLinks in enumerate(linkConfig):
          newCode[i*5+5] = format(modLinks,'x')
        newCode = tuple(newCode)
        if newCode in wagonCodesDict: wagonCodesDict[newCode] += locs
        else:                         wagonCodesDict[newCode] = locs
      del wagonCodesDict[key]

  codeCounter = Counter({tuple(key):len(val) for key,val in wagonCodesDict.items()})
  maxLinks = {x:maxLinksCalculation(x, wagonCodesDict) for x in wagonCodesDict}

  if not os.path.exists('output/geometriesWagon/{}'.format(geomVersion)): os.makedirs('output/geometriesWagon/{}'.format(geomVersion))
  f = open('output/geometriesWagon/{}/geometryWagon.txt'.format(geomVersion),'w')

  f.write('plane u v itype x0 y0 irot nvertices vx_0 vy_0 vx_1 vy_1 vx_2 vy_2 vx_3 vy_3 vx_4 vy_4 vx_5 vy_5 vx_6 vy_6 icassette trigRate trigLinks dataRate_ld dataLinks_ld dataRate_hd dataLinks_hd MB wagon isEngine nROCs power mrot phi HDorLD hash hash_hdld engine_trig_fibres engine_data_fibres engine_ctrl_fibres dataPp0 trigPp0 dataPp0_type trigPp0_type dataPp1 trigPp1 dataPp1_type trigPp1_type dataPp2 DAQ\n')

  for tempCode,indices in wagonCodesDict.items():
    tempCodeString = ''.join(str(x) for x in tempCode)
    for index in indices:

      tempIndex = index

      #u,v,irot = geomBasic.loc[(geomBasic['plane'] == tempIndex[0]) & (geomBasic['MB']  == tempIndex[1]) & (geomBasic['wagon'] == tempIndex[2]) & (geomBasic['isEngine']),['u','v','irot']].values.flatten().tolist()
      #geomTempIndex = geomBasic.loc[(geomBasic['plane'] == tempIndex[0]) & (geomBasic['MB']  == tempIndex[1]) & (geomBasic['wagon'] == tempIndex[2]) & (geomBasic['isEngine'])]
      #geomTempIndex = geomBasic.loc[(geomBasic['plane'] == tempIndex[0]) & (geomBasic['MB']  == tempIndex[1]) & (geomBasic['wagon'] == tempIndex[2])]
      #geomTempPartnerIndex = geomBasic.loc[(geomBasic['plane'] == tempIndex[0]) & (geomBasic['MB']  == tempIndex[1]) & (geomBasic['wagon'] == tempIndex[2])]
      geomTempIndex = geomGrouped.get_group((tempIndex[0],tempIndex[1],tempIndex[2]))
      geomTempPartnerIndex = geomGrouped.get_group((tempIndex[0],tempIndex[1],not tempIndex[2]))
      plane,icassette,MB,wagon = geomTempIndex[['plane','icassette','MB','wagon']].iloc[0]
      if int(tempCodeString[1]):
        u,v,irot,x0,y0,trig0,daqLD0,daqHD0 = geomTempIndex[['u','v','irot','x0','y0','trigLinks','dataLinks_ld','dataLinks_hd']].loc[geomTempIndex['isEngine']].iloc[0]
      else:
        uWest,vWest,irotWest = [int(x) for x in geomTempPartnerIndex[['u','v','irot']].loc[geomTempPartnerIndex['isEngine']].iloc[0]]
        u,v = findEastEngineModule(plane,uWest,vWest,irotWest)
        irot,x0,y0,trig0,daqLD0,daqHD0 = geomTempIndex[['irot','x0','y0','trigLinks','dataLinks_ld','dataLinks_hd']].loc[(geomTempIndex['u'] == u) & (geomTempIndex['v'] == v)].iloc[0]
      u,v,irot = [int(x) for x in [u,v,irot]]
      uList = list('-'*4)
      vList = list('-'*4)
      irotList = list('-'*4)
      nActiveTrig = trig0
      nActiveData = daqLD0 if int(tempCodeString[0]) == 0 else daqHD0
      if int(tempCodeString[2]) == 0:
        uList[0],vList[0],irotList[0] = [u,v,irot]
      else:
        uPrev,vPrev,irotPrev = [u,v,irot]
        for i in reversed(range(int(tempCodeString[2]))):
          angleRev,orientRev = reverseAngleOrient(int(tempCodeString[5*i+7]),int(tempCodeString[5*i+8]))
          uPrev,vPrev,irotPrev = nextModule(plane,uPrev,vPrev,irotPrev,angleRev,orientRev)
        uList[0],vList[0],irotList[0] = [uPrev,vPrev,irotPrev]
      for i in range(len(tempCodeString)//5-1):
        uNext,vNext,irotNext = nextModule(plane,uList[i],vList[i],irotList[i],int(tempCodeString[5*i+7]),int(tempCodeString[5*i+8]))
        uList[i+1],vList[i+1],irotList[i+1] = uNext,vNext,irotNext
        trigTemp,daqLDTemp,daqHDTemp = geomTempIndex[['trigLinks','dataLinks_ld','dataLinks_hd']].loc[(geomTempIndex['u'] == uNext) & (geomTempIndex['v'] == vNext)].iloc[0]
        nActiveTrig += trigTemp
        nActiveData += daqLDTemp if int(tempCodeString[0]) == 0 else daqHDTemp
      xFX11,yFX11 = [61.2,23.0]
      x0FX11 = x0 + xFX11 * np.cos(np.pi/3*irot) + yFX11 * np.sin(np.pi/3*irot)
      y0FX11 = y0 + xFX11 * np.sin(np.pi/3*irot) - yFX11 * np.cos(np.pi/3*irot)
      nModules = int((len(tempCodeString)-2)/5)
      nTrigTotal = int(tempCodeString[3]) + \
                   sum([int(tempCodeString[5*i+5]) for i in range(len(tempCodeString)//5)]) + \
                   sum([int(tempCodeString[5*i+6]) for i in range(len(tempCodeString)//5)])
      nTrigXOutTotal = sum([int(tempCodeString[5*i+6]) for i in range(len(tempCodeString)//5)])
      nDataTotal = 7 if int(tempCodeString[0]) == 0 else 14
      if tempCodeString in wagonNameDict: wagonName = wagonNameDict[tempCodeString]
      else: 
        print('ERROR: Wagon type code for {} not found')
        wagonName = 'XXXXXX'
      f.write('{}\n'.format(' '.join(str(x) for x in [	plane,u,v,wagonName,round(x0FX11,3),					# 1-5
							round(y0FX11,3),irot,nModules,uList[0],vList[0],			# 6-10
							uList[1],vList[1],uList[2],vList[2],uList[3],				# 11-15
							vList[3],'-','-','-','-',						# 16-20
							'-','-',icassette,nTrigTotal,int(nActiveTrig),				# 21-25
							nDataTotal,int(nActiveData),int(tempCodeString[3]),nTrigXOutTotal,MB,	# 26-30
							wagon,0,0,'-','-',							# 31-35
							'-',int(tempCodeString[0]),'-','-','-',					# 36-40
							'-',tempCodeString,'-','-','-',						# 41-45
							'-','-','-','-','-',							# 46-50
							'-','-'])))								# 51-52

  f.close()

  #geomWagon = pd.read_csv('output/geometriesWagon/{}/geometryWagon.txt'.format(geomVersion),delim_whitespace=True)


  if not os.path.exists('output/geometriesEngine/{}'.format(geomVersion)): os.makedirs('output/geometriesEngine/{}'.format(geomVersion))
  f = open('output/geometriesEngine/{}/geometryEngine.txt'.format(geomVersion),'w')

  f.write('plane u v itype x0 y0 irot nvertices vx_0 vy_0 vx_1 vy_1 vx_2 vy_2 vx_3 vy_3 vx_4 vy_4 vx_5 vy_5 vx_6 vy_6 icassette trigRate trigLinks dataRate_ld dataLinks_ld dataRate_hd dataLinks_hd MB wagon isEngine nROCs power mrot phi HDorLD hash hash_hdld engine_trig_fibres engine_data_fibres engine_ctrl_fibres dataPp0 trigPp0 dataPp0_type trigPp0_type dataPp1 trigPp1 dataPp1_type trigPp1_type dataPp2 DAQ\n')


  geomEngine = geomBasic[geomBasic['isEngine']]
  for i,engine in geomEngine.iterrows():
    plane,u,v,irot,icassette = engine['plane'],engine['u'],engine['v'],engine['irot'],engine['icassette']
    engineType = ''
    if engine['HDorLD'] == 0:
      if irot == 0: engineType = 'EL10E0' if engine['x0'] > 0 else 'EL10W0'
      elif irot == 1 or irot == 2: engineType = 'EL10E0'
      elif irot == 3: engineType = 'EL10W0'
      elif irot == 4 or irot ==  5: engineType = 'EL10W0'
      else: print('ERROR: Invalid irot for engine {}'.format(i))
    else:
      if irot == 0 or irot == 5: engineType = 'EH10W0'
      elif irot == 3 or irot == 4: engineType = 'EH10E0'
      else: print('ERROR: Invalid irot for engine {}'.format(i))
    f.write('{}\n'.format(' '.join(str(x) for x in [plane,'-','-',engineType,'-','-','-','-','-','-',u,v,'-','-','-','-','-','-','-','-','-','-',icassette,'-','-','-','-','-','-','-','-','-','-','-','-','-',engine['HDorLD'],'-','-','-','-','-','-','-','-','-','-','-','-','-','-','-'])))

  #geomEngineHD = geomBasic[(geomBasic['HDorLD'] == 1) & (geomBasic['isEngine'])]

  f.close()

  #codeCounterTemp = {k: v for k,v in codeCounter.items() if len(k) == 12 and sum([i == 'F' for i in k]) == 2 and k[1] == 0 and k[7] == 0 and k[8] == 0}
  #codeCounter = codeCounterTemp

  #print(codeCounter)
  uniqueWagonCodes = [list(i) for i in set(tuple(i) for i in list(codeCounter.keys()))]
  uniqueWagonCodesHD = [i for i in uniqueWagonCodes if i[0] == 1]
  uniqueWagonCodesLD = [i for i in uniqueWagonCodes if i[0] == 0]
  print('Number of HD wagon types:',len(uniqueWagonCodesHD))
  #print(uniqueWagonCodesHD)
  print('Number of LD wagon types:',len(uniqueWagonCodesLD))
  #print(uniqueWagonCodesLD)

  # Save dictionary to file
  with open('wagonDict/wagonDict_{}.txt'.format(geometryFile),'w') as f:
    print(wagonCodesDict,file=f)

  # Print wagon info
  wagonCodesDict = dict(sorted(wagonCodesDict.items(),key=lambda x:(x[0][0],len(x[0]),len(x[1])),reverse=True))
  with open('wagonInfo/wagonInfo_{}.txt'.format(geomVersion),'w') as f:
    for code,locs in wagonCodesDict.items():
      if len(locs) > 10: continue
      print('-'*20,''.join([str(x) for x in code]),'-'*20,file=f)
      print('No. of instances:',len(locs),file=f)
      print('Locations:',sorted(locs,key=lambda x:x[0]),file=f)
      partnerCodes = []
      for loc in locs:
        index = 99999
        for i,val in enumerate(wagonCodesDict.values()):
          if [loc[0],loc[1],int(not loc[2])] in val:
            index = i
        partnerCodes.append(''.join(str(i) for i in list(wagonCodesDict.keys())[index]))
      print('Partner codes and counts:',Counter(partnerCodes),file=f)
      print('-'*(40+len(''.join([str(x) for x in code]))),'\n',file=f)

  # Select only varieties with <= 10 instances
  #for key,val in list(wagonCodesDict.items()):
  #  if len(val) > 10: del wagonCodesDict[key]
  #codeCounter = Counter({tuple(key):len(val) for key,val in wagonCodesDict.items()})
  #maxLinks = {x:maxLinksCalculation(x, wagonCodesDict) for x in wagonCodesDict}  

  # Sort by HD/LD then no. of modules then no. of instances 
  codeCounter = dict(sorted(codeCounter.items(), key=lambda item: (item[0][0],len(item[0]),item[1]), reverse=True))

  #for key,item in codeCounter.items():
  #  print(''.join([str(x) for x in key]))

  # Draw and save the wagon summary (see wagonDrawer.py)
  wagonDrawer.wagonDrawer(codeCounter,geomVersion,maxLinks)

if __name__ == '__main__':
  main()
