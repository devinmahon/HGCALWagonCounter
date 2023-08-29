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
 
  if plane > 26 or plane % 2: 
    uDiff = {0: 1, 1: 1, 2: 0, 3: -1, 4: -1, 5:  0}
    vDiff = {0: 0, 1: 1, 2: 1, 3:  0, 4: -1, 5: -1} 
    uEastEngine = u + uDiff[irot]
    vEastEngine = v + vDiff[irot]
  else:
    uDiff = {0: -1, 1:  0, 2: 1, 3: -1, 4:  0, 5: -1}
    vDiff = {0:  0, 1: -1, 2: 1, 3:  0, 4: -1, 5: -1}
    uEastEngine = u + uDiff[irot]
    vEastEngine = v + vDiff[irot]

  coords = earliestWagon[['u','v']].values.tolist()
  index = [i for i in range(len(coords)) if coords[i] == [uEastEngine,vEastEngine]][0]
  if index != 0: print(plane,u,v,index,code)

  return index



#def findEngine(code, wagonCodesDict, geomGrouped):
#  if code[1] != -1:
#    return code[1]
#  
#  moduleTypes = list(code[3::3])
#  if len(moduleTypes) == 1:
#    return 0
#  if moduleTypes.count('F') == 1:
#    return moduleTypes.index('F')
# 
#  earliestWagonID = wagonCodesDict[code][0]
#  earliestWagon = geomGrouped.get_group((earliestWagonID[0], earliestWagonID[1], earliestWagonID[2]))
#  earliestWagonPartner = geomGrouped.get_group((earliestWagonID[0], earliestWagonID[1], not earliestWagonID[2]))
#  
#  earliestWagon_plane = [x for x in earliestWagon['plane'].tolist()]
#  earliestWagon_u = [x for x in earliestWagon['u'].tolist()]
#  earliestWagon_v = [x for x in earliestWagon['v'].tolist()]
#
#  partnerModule_plane = [x for x in earliestWagonPartner['plane'].tolist()]
#  partnerModule_u = [x for x in earliestWagonPartner['u'].tolist()]
#  partnerModule_v = [x for x in earliestWagonPartner['v'].tolist()]
#
#  partnerEngineTF = [x for x in earliestWagonPartner['isEngine'].tolist()]
#  partnerEnginePos = partnerEngineTF.index(True)
#
#  partnerEngineCoords = [(), (), (), (), (), ()]
#  for k in range(6):
#    vertexNum_x = 'vx_{0}'.format(k)
#    vertexNum_y = 'vy_{0}'.format(k)
#
#    partnerModuleVertex_x = [x for x in earliestWagonPartner[vertexNum_x].tolist()]
#    partnerModuleVertex_y = [y for y in earliestWagonPartner[vertexNum_y].tolist()]
#
#    partnerEngineModuleCoords = (partnerModuleVertex_x[partnerEnginePos], partnerModuleVertex_y[partnerEnginePos])
#    partnerEngineCoords[k] = partnerEngineModuleCoords
#  # print(partnerEngineCoords)
#  
#  moduleCoords = []
#  for i in range(len(moduleTypes)):
#    moduleCoords.append([])
#
#  i = 0
#  while i < 6:
#    print(i)
#    if i == 0:
#      prev_i = 5
#      next_i = 1
#    elif i == 5:
#      prev_i = 4
#      next_i = 0
#    else:
#      prev_i = i - 1
#      next_i = i + 1
#    
#    vertexNum_x = 'vx_{0}'.format(i)
#    vertexNum_y = 'vy_{0}'.format(i)
#
#    moduleCoord_x = [x for x in earliestWagon[vertexNum_x].tolist()]
#    moduleCoord_y = [y for y in earliestWagon[vertexNum_y].tolist()]
#
#    for j in range(len(moduleCoord_x)):
#      print(j,next_i,prev_i)
#      coords = (moduleCoord_x[j], moduleCoord_y[j], j, i)
#      moduleCoords[j].append(coords)
#      if (moduleCoord_x[j], moduleCoord_y[j]) in partnerEngineCoords:
#        vertexNum_nextx = 'vx_{0}'.format(next_i)
#        vertexNum_nexty = 'vy_{0}'.format(next_i)
#
#        vertexNum_prevx = 'vx_{0}'.format(prev_i)
#        vertexNum_prevy = 'vy_{0}'.format(prev_i)
#
#        moduleCoord_nextx = [x for x in earliestWagon[vertexNum_nextx].tolist()]
#        moduleCoord_nexty = [y for y in earliestWagon[vertexNum_nexty].tolist()]
#
#        moduleCoord_prevx = [x for x in earliestWagon[vertexNum_prevx].tolist()]
#        moduleCoord_prevy = [y for y in earliestWagon[vertexNum_prevy].tolist()]
#        print(partnerEngineCoords)
#        print(moduleCoord_nextx)
#        if (moduleCoord_nextx[j], moduleCoord_nexty[j]) in partnerEngineCoords:
#          print('next',j)
#          return j
#        elif (moduleCoord_prevx[j], moduleCoord_prevy[j]) in partnerEngineCoords:
#          print('prev',j)
#          return j
#
#    i += 1

  

##################################################
# MAIN
##################################################
def main():

  # Configuration parameters
  threesSeparate = False
  halvesSemisSame = False
  halvesSemisFivesSame = True
  LDHDBoth = 0

  # Specify the geometry file to be used
  geomVersion = 'v15.3_development_irot'#'v15.2_uniformirot_def_fixed'
  geometryPath = 'geometries/{}/'.format(geomVersion)
  geometryFile = 'geometry.hgcal'
  #geometryFile = 'geo_with_east'

  # Extract required columns
  geom = pd.read_csv('{0}{1}.txt'.format(geometryPath,geometryFile),delim_whitespace=True)
  geomBasic = geom[['plane','u','v','x0','y0', 'vx_0', 'vy_0', 'vx_1', 'vy_1', 'vx_2', 'vy_2', 'vx_3', 'vy_3', 'vx_4', 'vy_4', 'vx_5', 'vy_5', 'vx_6', 'vy_6', 'itype','irot','MB','wagon','isEngine','HDorLD','trigLinks','dataLinks_ld','dataLinks_hd','icassette']].copy()

  # Reflect even layers
  #geomBasic.loc[geomBasic['plane'] % 2 == 0,'irot'] *= -1
  #geomBasic.loc[geomBasic['plane'] % 2 == 0,'irot'] %= 6
  #geomBasic.loc[geomBasic['plane'] % 2 == 0,'u'] *= -1

  if not threesSeparate: geomBasic = geomBasic[~geomBasic['itype'].str.contains('c')] # Threes don't affect wagon shape

  # Add distance from origin
  geomBasic['r'] = np.sqrt(geomBasic['x0']**2 + geomBasic['y0']**2)

  # Format type
  #geomBasic['itype'] = geomBasic['itype'].str[0]
  #geomBasic['itype'] = geomBasic['itype'].str[0] if ('T' in geomBasic['itype']) or ('L' in geomBasic['itype'])
  geomBasic.loc[(geomBasic['itype'].str.contains('T|L')),'irot'] += 3
  geomBasic['irot'] %= 6
  geomBasic['itype'] = geomBasic['itype'].str[0]

  if halvesSemisSame: 
    #geomBasic.loc[geomBasic['itype'] == 'd','irot'] += 1
    geomBasic.loc[geomBasic['itype'] == 'd','itype'] = 'a'
  elif halvesSemisFivesSame:
    geomBasic.loc[geomBasic['itype'] == 'd','irot'] +=1

    geomBasic.loc[geomBasic['itype'] == 'a','itype'] = 'd'

    geomBasic.loc[geomBasic['itype'] == 'b','irot'] += 1
    geomBasic.loc[geomBasic['itype'] == 'b','itype'] = 'd'

    geomBasic['irot'] %= 6

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

  #geomBasic = geomBasic[((geomBasic['plane'] == 23) & (geomBasic['MB'] == 5)) | ((geomBasic['plane'] == 1) & (geomBasic['MB'] == 11))]
  #geomBasic = geomBasic[(geomBasic['plane'] == 2)]

  # Group modules by plane (layer), MB index, and wagon index
  geomGrouped = geomBasic.sort_values('r',ascending=True).groupby(['plane','MB','wagon'])

  #print(geomGrouped.get_group((2,10,0)))
  #print('#'*50)
  #print(geomGrouped.get_group((2,10,1)))

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
    if wagonRot in codeCounter and not wagonRot in duplicateCodes:
      #if wagon == (0, 0, 0, 'F', 3, 0, 'F', 3, 0, 'F', 3, 3, 'a'): print('deleting',wagonRot)

      for id in wagonCodesDict[wagonRot]:
        geomBasic.loc[(geomBasic['plane'] == id[0]) & (geomBasic['MB'] == id[1]) & (geomBasic['wagon'] == id[2]),'r'] *= -1

      codeCounter[wagon] += codeCounter[wagonRot]
      duplicateCodes.append(wagon)
      codeCounter.pop(wagonRot,None)

      wagonCodesDict[wagon] = wagonCodesDict[wagon] + wagonCodesDict[wagonRot]
      wagonCodesDict.pop(wagonRot)

  geomGrouped = geomBasic.sort_values('r',ascending=True).groupby(['plane','MB','wagon'])

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
        if totTrigLinks > 7: #****
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

      ################################
      # Print out optional information
      ################################

      # Check number of links on individual MBs
      #if key == (1, 2, 0, 'g', 3, 3, 'F', 0, 0, 'F'):
      #  if sum(numTrigLinks) >= 24: print(id,numTrigLinks)
      #  if numTrigLinks[1] == 6: print(id,numTrigLinks,wagonTemp)
      #if key == (1, 3, 0, 'd', 4, 4, 'F', 0, 0, 'F', 0, 0, 'F'):
      #  if sum(numTrigLinks) > 28: print(id,numTrigLinks)

      # Check if link counts
      #if sum(numTrigLinks) > 28: print(id,numTrigLinks)
        #if numTrigLinks[0] > 6:
        #  print(id,numTrigLinks)
        #if numTrigLinks[1] > 3:
        #  print(id,numTrigLinks)

    # Print out links (WARNING: THE CROSSOVERS AREN'T FIXED IN THE COPY!!!)
    #print(maxTrigLinks)

    # Print messages about link distribution on LD wagons
    #if key[0] == 0 and sum(maxTrigLinks) > 7: print('Wagon',key,'has maxTrigLinks with total > 7. maxTrigLinks = ',maxTrigLinks)
    #if key in [(0,-1,0,'F'),(0,0,0,'F'),(0,-1,0,'F',3,0,'F'),(0,0,0,'F',3,0,'F'),(0,-1,0,'F',0,0,'F',0,0,'F'),(0,0,0,'F',3,0,'F',3,0,'F'),(0,0,1,'F',3,0,'F'),(0,-1,-1,'F',3,0,'F')]: print('-->',key,':',maxTrigLinks)

    # Print messages about HD links
    #if key[0] == 1: print('Wagon',key,'has maxTrigLinks = ',maxTrigLinks)
    # Print message about how many HD wagons has more than 7 DAQ links
    #if key[0] == 1: print(numDataLinksHDGT7,'/',len(value),'('+'{:.1f}'.format(100 * numDataLinksHDGT7 / len(value)),'%) HD wagons with code',key,'have more than 7 DAQ links')

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
  
  def minLinksCalculation(code, dict1):
    lenWagon = len(code[3::3])
    minLinksList = []
    for i in range(lenWagon):
      minLinksList.append(5)
    for loc in dict1[code]:
      wagonLoc = geomGrouped.get_group((loc[0], loc[1], loc[2]))
      numTrigLinks = [int(x) for x in wagonLoc['trigLinks'].tolist()]
      for j in range(len(numTrigLinks)):
        if numTrigLinks[j] < minLinksList[j] and numTrigLinks[j] != 0:
          minLinksList[j] = numTrigLinks[j]
    return minLinksList
     
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
  
  # Consolidating using Incoming Crossover Links
  wagonCodesDictCopy = copy.deepcopy(wagonCodesDict)
  incomingWagonCodesDict = {x:wagonCodesDictCopy[x] for x in wagonCodesDictCopy.keys() if x[2] <= 0}
  incomingWagonCodesCopy = copy.deepcopy(incomingWagonCodesDict)
  removedWagonsList = []
  removedWagonsDict = {x:[] for x in wagonCodesDict}
  wagonMovementDict = {x:[] for x in wagonCodesDict}
  for code, vals in incomingWagonCodesCopy.items():
    transferredCodes = {}
    numTransfers = 0
    counterCopy = copy.deepcopy(codeCounter)
    for loc in vals:
      wagonLoc = geomGrouped.get_group((loc[0], loc[1], loc[2]))
      numTrigLinks = [int(x) for x in wagonLoc['trigLinks'].tolist()]
      totTrigLinks = sum(numTrigLinks)
      numAvailable = 7 - totTrigLinks
      availableRange = range(-1 * numAvailable, 0)
      for i in availableRange:
        possibleCode = list(code)
        possibleCode = possibleCode[:2] + [i] + possibleCode[3:]
        possibleCode = tuple(possibleCode)
        if possibleCode in incomingWagonCodesCopy and possibleCode != code:
          incomingWagonCodesDict[possibleCode].append(loc)
          if (sum(maxLinksCalculation(possibleCode, incomingWagonCodesDict)) + -1 * possibleCode[2] > 7):
            incomingWagonCodesDict[possibleCode].remove(loc)
            break
          elif possibleCode in transferredCodes.keys():
            transferredCodes[possibleCode].append(loc)
            numTransfers += 1
          else:
            transferredCodes[possibleCode] = [loc]
            numTransfers += 1  
          incomingWagonCodesDict[possibleCode].remove(loc)      
          break
    if numTransfers == codeCounter[code] or code[2] == 0:
      for possibleCode, locations in transferredCodes.items():
        for loc in locations:
          incomingWagonCodesDict[code].remove(loc)
          incomingWagonCodesDict[possibleCode].append(loc)
          codeCounter[code] -= 1
          codeCounter[possibleCode] += 1
          if codeCounter[code] == 0:
            removedWagonsList.append(code)
          if possibleCode not in removedWagonsDict[code]:
            removedWagonsDict[code].append(possibleCode)
    for wagon in removedWagonsDict[code]:
      delta = codeCounter[wagon] - counterCopy[wagon]
      if delta != 0:
        wagonMovementDict[code].append((wagon, delta))


  for key, val in incomingWagonCodesDict.items():
    wagonCodesDictCopy[key] = val
  
  wagonCodesDict = copy.deepcopy(wagonCodesDictCopy)

  # Consolidating using outgoing crossover links, taking into account wagon partners
  outgoingWagonCodesDict = {x:wagonCodesDictCopy[x] for x in wagonCodesDictCopy.keys() if x[0] == 0 and x[2] >= 0}
  outgoingWagonCodesCopy = copy.deepcopy(outgoingWagonCodesDict)
  for key, val in outgoingWagonCodesCopy.items():
    counterCopy = copy.deepcopy(codeCounter)
    transferredCodes = {}
    preConsolLength = len(wagonCodesDict[key])
    numTransfers = 0
    for loc in val:
      wagonLoc = geomGrouped.get_group((loc[0], loc[1], loc[2]))
      wagonPartnerLoc = geomGrouped.get_group((loc[0], loc[1], int(not loc[2])))
      numTrigLinks = [int(x) for x in wagonLoc['trigLinks'].tolist()]
      numLinks = sum([int(x) for x in wagonLoc['trigLinks'].tolist()])
      numOutgoingLinks = key[2]
      numPartnerLinks = sum([int(x) for x in wagonPartnerLoc['trigLinks'].tolist()])
      numAvailablePartnerLinks = 7 - numPartnerLinks
      acceptableRange = list(range(numAvailablePartnerLinks + 1, 0, -1))
      if len(acceptableRange) and key[2] == acceptableRange[0]:
        continue 
      for num in acceptableRange:
        possibleCode = list(key)
        possibleCode = possibleCode[:2] + [num] + possibleCode[3:]
        possibleCode = tuple(possibleCode)
        if possibleCode in outgoingWagonCodesCopy and possibleCode != code:
          if possibleCode in transferredCodes.keys():
            transferredCodes[possibleCode].append(loc)
          else:
            transferredCodes[possibleCode] = [loc]
          numTransfers += 1
          break
    if numTransfers == preConsolLength or key[2] == 0:
      for possibleCode, locations in transferredCodes.items():
        for loc in locations:
          outgoingWagonCodesDict[key].remove(loc)
          outgoingWagonCodesDict[possibleCode].append(loc)
          codeCounter[key] -= 1
          codeCounter[possibleCode] += 1
          if codeCounter[key] == 0:
            removedWagonsList.append(key)
          if possibleCode not in removedWagonsDict[key]:
            removedWagonsDict[key].append(possibleCode)
    for wagon in removedWagonsDict[key]:
      delta = codeCounter[wagon] - counterCopy[wagon]
      if delta != 0:
        wagonMovementDict[key].append((wagon, delta))
    postConsolLength = len(outgoingWagonCodesDict[key])
    diff = preConsolLength - postConsolLength

  for key, val in outgoingWagonCodesDict.items():
    wagonCodesDictCopy[key] = val

  wagonCodesDict = copy.deepcopy(wagonCodesDictCopy)
  wagonCodesDict = {x:y for x, y in wagonCodesDict.items() if len(y) > 0}

  # Finding max. links on each module on each wagon type
  maxLinks = {x:maxLinksCalculation(x, wagonCodesDict) for x in wagonCodesDict}

  # print(maxLinks)

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
      
      if linksSummary[code] == [-2, 0] or linksSummary[code] == [0, -2]:
        linksSummary[code] == [-1, -1]
      for i in range(len(maxLinksList)):
        maxLinksList[i] += -1 * linksSummary[code][i]
      maxLinks[code] = maxLinksList
    
    # elif code[2] < 0:
    #   numIncomingLinks = code[2]
    #   maxLinksList = maxLinks[code]
    #   minIndex = maxLinksList.index(min(maxLinksList))
    #   numUnaccountedFor = -1 * numIncomingLinks

    #   for i in range(len(maxLinksList)):
    #     linksSummary[code].append(0)
      
    #   maxLinksListCopy = maxLinksList
    #   while numUnaccountedFor > 0:
    #     linksSummary[code][minIndex] += 1
    #     maxLinksListCopy[minIndex] += 1
    #     minIndex = maxLinksListCopy.index(min(maxLinksListCopy))
    #     numUnaccountedFor -= 1
      
    #   for i in range(len(maxLinksList)):
    #     maxLinksList[i] -= linksSummary[code][i]
    #   maxLinks[code] = maxLinksList

  linksRoutingSummaryFile = 'link-routing-summary'
  with open("{}.txt".format(linksRoutingSummaryFile), 'w') as f:
    for code in linksSummary:
      linksInfoList = linksSummary[code]
      maxLinksList = maxLinks[code]
      print("{0}: {1} + {2}".format(code, maxLinksList, linksInfoList), file = f)

  #maxLinksSummary = {x:[] for x in linksSummary}
  #for code in linksSummary:
  #  if linksSummary[code] == [-2, 0] or linksSummary[code] == [0, -2]:
  #    linksSummary[code] = [-1, -1]
  #  for i in range(len(linksSummary[code])):
  #    maxLinksSummary[code].append(str(maxLinks[code][i]) + "-" + str(-1 * linksSummary[code][i]))
  #  maxLinks[code] = maxLinksSummary[code]

  emptyCounter = Counter([tuple(i) for i in removedWagonsList])
  for wagon in removedWagonsList:
    emptyCounter[wagon] = 0
  
  # Finding engine pos. for east wagons
  eastEnginePositions = {x:findEngine(x, wagonCodesDict, geomGrouped) for x in wagonCodesDict if x[1] == -1}  

  for code in eastEnginePositions:
    if code in recodedCodesList and code not in removedWagonsList:
      lenWagon = len(code[3::3])
      eastEnginePositions[code] = (lenWagon - 1) - eastEnginePositions[code]

  # Recoding as per new format
  newCodeFormat = {}
  for code in wagonCodesDict:
      HDorLD = code[0]
      EastorWest = 0 if code[1] == -1 else 1
      enginePos = code[1] if code[1] != -1 else eastEnginePositions[code]
      if code[2] < 0:
        incomingNum = -1 * code[2]
      else:
        incomingNum = 0
      preCode = (HDorLD, EastorWest, enginePos, incomingNum)

      wagonTypes = code[3::3]
      codeMinusTypes = tuple([x for x in code[3:] if x not in wagonTypes])
      angleOrientationCodes = tuple([codeMinusTypes[i:i+2] for i in range(0, len(codeMinusTypes), 2)])
      newCode = preCode
      for i in range(len(wagonTypes)):
        wagonType = wagonTypes[i]
        maxLinksModule = maxLinks[code][i]
        if type(maxLinksModule) == str:
          maxLinksModule = int(maxLinksModule[0])
        if code in linksSummary:
          crossoverLinks = -1 * linksSummary[code][i]
          engineLinks = maxLinksModule - crossoverLinks
        else:
          crossoverLinks = 0
          engineLinks = maxLinksModule
        angleOrientationCode = angleOrientationCodes[i] if i < (len(wagonTypes) - 1) else ()
        newCode += (wagonType, engineLinks, crossoverLinks)
        newCode += angleOrientationCode
      newCodeFormat[code] = newCode
  #print(newCodeFormat)

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

  # geometryFile2 = 'removedWagons'
  # with open('wagonDict/{}.txt'.format(geometryFile2), 'w') as f:
  #   print(removedWagonsList, file = f) 

  # wagonDrawer.wagonDrawer(emptyCounter, geometryFile2)

  # Print message about total number of HD wagons with <= 14 trigger links
  #print(numTrigLinksHDLT15,'out of',numHD,'(','{:.1f}'.format(numTrigLinksHDLT15 * 100.0 / numHD),'%) HD wagons have <= 14 trigger links')

  # Print out maxTrigLinks for individual wagon varieties
  #for key,value in wagonCodesDict.items():
  #  maxTrigLinks = []
  #  for id in value:
  #    wagonTemp = geomGrouped.get_group((id[0],id[1],id[2]))
  #    numTrigLinks = [int(x) for x in wagonTemp['trigLinks'].tolist()]
  #    if not len(maxTrigLinks):	maxTrigLinks = numTrigLinks
  #    else: 			maxTrigLinks = np.maximum(maxTrigLinks,numTrigLinks)
  #    #if key == (0, 0, 0, 'F', 3, 0, 'F', 3, 0, 'F', 3, 3, 'a') and numTrigLinks[3] == 2: print(id,numTrigLinks)
  #  #if key[0] == 0 and sum(maxTrigLinks) > 7: print(key,maxTrigLinks)
  #  if key in [(0,-1,0,'F'),(0,0,0,'F'),(0,-1,0,'F',3,0,'F'),(0,0,0,'F',3,0,'F'),(0,-1,0,'F',0,0,'F',0,0,'F'),(0,0,0,'F',3,0,'F',3,0,'F'),(0,0,1,'F',3,0,'F'),(0,-1,-1,'F',3,0,'F')]: print(key,':',maxTrigLinks)

  # Remove empty Counter entries
  codeCounter = Counter({i:j for i,j in codeCounter.items() if j != 0})

  ## Mapping modules to wagon schematics
  #tempCode = (0,0,0,'F',3,0,'F',3,0,'F')
  #tempIndex = wagonCodesDict[tempCode][0]
  #print(tempIndex)
  #temp = geomGrouped.get_group(tuple(tempIndex))
  ##temp = temp[temp['isEngine'] == 1]
  #print(temp)

  wagonNameDict = {
  '1130d7030Fb030F7030F50'	 : 'WH31A1',
  '1130d0025F0030F0030F00'	 : 'WH31B1',
  '1130d5051F5020F5030F50'	 : 'WH31C1',
  '1120F9000F6000F40'	         : 'WH30A1',
  '1120g9030F8030F50'	         : 'WH21A1',
  '1120F7040F6020F60'	         : 'WH30B1',
  '1110F0030F0050F00'	         : 'WH30C1',
  '1110F5000F50'	         : 'WH20A1',
  '0000F1100F2000F2005d20'	 : 'WE31A1',
  '0100F1130F2030F2032d20'	 : 'WW31A1',
  '0100F1122F2024F2022d20'	 : 'WW31A2',
  '0100F1121d2035F2022d20'	 : 'WW22A1',
  '0000F1114F2012F2010d20'	 : 'WE31A3',
  '0101F2030F2030F20'	         : 'WW30A1', # West 3A
  '0001F2000F2000F20'	         : 'WE30A1',
  '0000F2000F2005d20'	         : 'WE21A1',
  '0100F3030F2032d20'	         : 'WW21A1',
  '0101F3030F2032d10'	         : 'WW21B1',
  '0001F3000F2005d10'	         : 'WE21B1',
  '0011F2030F2022F20'	         : 'WE30A2',
  '0000F3010d2050d20'	         : 'WE12A1',
  '0100F2014F2030F20'	         : 'WW30A2', # Lefty Python
  '0000F2014F2012F20'	         : 'WE30A3', # East T
  '0100F2022F2024F20'	         : 'WW30A3', # West T
  '0000F2000F2000d20'	         : 'WE21A2',
  '0100F2222d3120d20'	         : 'WW12A1',
  '0111F2000F2014F20'	         : 'WW30B1',
  '0100F0014F0033d00'	         : 'WW12C1',
  '0000F0011d0040d00'	         : 'WE12B1',
  '0000F2010d2050F20'	         : 'WE21A3',
  '0100F2022d2020d20'	         : 'WW12B1',
  '0100F0014F0031d00'	         : 'WW21C2',
  '0000F0000F0001d00'	         : 'WE21C1',
  '0000F0015d0000d00'	         : 'WE12B2',
  '0100F2021d2031d20'	         : 'WW12B2',
  '0000F2010d2055d20'	         : 'WE12C1',
  '0000F0015d0001F00'	         : 'WE21C2',
  '0100F0030F0031d00'	         : 'WW21D1',
  '0100F2030F2033d20'	         : 'WW21E1',
  '0110d2033F2014F20'	         : 'WW21E2',
  '0011d2051F2024F20'	         : 'WE21D1',
  '0100F3014F2032d20'	         : 'WW21A2',
  '0000F0011d0044d00'	         : 'WE12B3',
  '0100F2030F2035d20'	         : 'WW21E3',
  '0000F2011d2045d20'	         : 'WE12C2',
  '0000F2011d2045F20'	         : 'WE21A4',
  '0100F2021d2035F20'	         : 'WW21E4',
  '0110F2000F2011d20'	         : 'WW21E5',
  '0020F2030F2022d20'	         : 'WE21A5',
  '0000F2014F2012d20'	         : 'WE21A6',
  '0002F2000F30'	         : 'WE20C1',
  '0102F3030F20'	         : 'WW20B1',
  '0100F3130F41'	         : 'WW20A1', # West 2A
  '0001F4005d20'	         : 'WE11A1',
  '0102F2032d20'	         : 'WW11A1',
  '0001F3000F30'	         : 'WE20B1', # East 2B
  '0100F3033d30'	         : 'WW11B1',
  '0000F3200F40'	         : 'WE20A1', # East 2A
  '0101F3030F30'	         : 'WW20C1',
  '0100F0031d00'	         : 'WW11C1',
  '0100F4014F30'	         : 'WW2001',
  '0001F3000d30'	         : 'WE11B1',
  '0100F3132d40'	         : 'WW11D1',
  '0110d3124F40'	         : 'WW11E1',
  '0000F2010d20'	         : 'WE11C1',
  '0000F2022F20'	         : 'WE20D1',
  '0000F3100F30'	         : 'WE20E1',
  '0103F40'	                 : 'WW10B1',
  '0003F40'	                 : 'WE10B1',
  '0001F50'	                 : 'WE10A1', # East 1A 
  '0101F50'	                 : 'WW10A1', # West 1A
  '0000F03'	                 : 'WE10C1',
  '0100F02'	                 : 'WW10C1',
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


  if not os.path.exists('output/geometriesWagon/{}'.format(geomVersion)): os.makedirs('output/geometriesWagon/{}'.format(geomVersion))
  f = open('output/geometriesWagon/{}/geometryWagon.txt'.format(geomVersion),'w')

  f.write('plane u v itype x0 y0 irot nvertices vx_0 vy_0 vx_1 vy_1 vx_2 vy_2 vx_3 vy_3 vx_4 vy_4 vx_5 vy_5 vx_6 vy_6 icassette trigRate trigLinks dataRate_ld dataLinks_ld dataRate_hd dataLinks_hd MB wagon isEngine nROCs power mrot phi HDorLD hash hash_hdld engine_trig_fibres engine_data_fibres engine_ctrl_fibres dataPp0 trigPp0 dataPp0_type trigPp0_type dataPp1 trigPp1 dataPp1_type trigPp1_type dataPp2 DAQ\n')

  for tempCode,indices in wagonCodesDict.items():

    #iif tempCode[1] == -1: continue
    #if not (len(tempCode) - 1) / 3 == 2: continue
    #print(tempCode)
    #print(indices)

    for index in indices:

      tempIndex = index

      #u,v,irot = geomBasic.loc[(geomBasic['plane'] == tempIndex[0]) & (geomBasic['MB']  == tempIndex[1]) & (geomBasic['wagon'] == tempIndex[2]) & (geomBasic['isEngine']),['u','v','irot']].values.flatten().tolist()
      #geomTempIndex = geomBasic.loc[(geomBasic['plane'] == tempIndex[0]) & (geomBasic['MB']  == tempIndex[1]) & (geomBasic['wagon'] == tempIndex[2]) & (geomBasic['isEngine'])]
      geomTempIndex = geomBasic.loc[(geomBasic['plane'] == tempIndex[0]) & (geomBasic['MB']  == tempIndex[1]) & (geomBasic['wagon'] == tempIndex[2])]
      plane,u,v,irot,icassette = geomTempIndex[['plane','u','v','irot','icassette']].iloc[0]

      if ''.join(str(x) for x in tempCode) in wagonNameDict: wagonName = wagonNameDict[''.join(str(x) for x in tempCode)]
      else: wagonName = 'XXXXXX'
      f.write('{}\n'.format(' '.join(str(x) for x in [plane,u,v,wagonName,'-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-',icassette,'-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-',''.join(str(y) for y in tempCode),'-','-','-','-','-','-','-','-','-','-'])))

  f.close()

  geomWagon = pd.read_csv('output/geometriesWagon/{}/geometryWagon.txt'.format(geomVersion),delim_whitespace=True)


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

  # Sort by HD/LD then no. of modules then no. of instances 
  codeCounter = dict(sorted(codeCounter.items(), key=lambda item: (item[0][0],len(item[0]),item[1]), reverse=True))

  #for code in codeCounter: print('\'{}\'\t : \'\','.format(''.join([str(x) for x in code])))

  # Draw and save the wagon summary (see wagonDrawer.py)
  wagonDrawer.wagonDrawer(codeCounter,geomVersion,maxLinks)

if __name__ == '__main__':
  main()
