import pandas as pd
import numpy as np
from collections import Counter
import itertools
import wagonDrawer
import sys
import time
import copy
import os
import subprocess
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import argparse
from tabulate import tabulate
import json

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
      groupTemp = group.iloc[list(ordering)]
  group = groupTemp
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

  preCode = list(code[:3])
  if preCode[1] != -1: preCode[1] = len(code[3::3]) - 1 - code[1]

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

  newCode = preCode + [x for ele in middleCode for x in ele] + list(labelsReversed[-1])

  return tuple(newCode)

def recode(code):
  wagonLength = len(code[3::3])
  wagonTypes = code[3::3]
  if wagonTypes.count('F') != wagonLength:
    return code
  if code[1] == 0:
    return code
  if code[1] == -1:
    return reverseCode(code)
  else:
    engineIndex = code[1]
    if engineIndex != wagonLength - 1:
      # Recoding not possible, return original code
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

def findEngine(code,codeFormat,instance,geomGrouped,recodedCodesList):

  # If it's already been calculated, just check if it's been recoded
  if code[1] != -1:
    if code not in recodedCodesList: 
      return code[1]
    else:
      if codeFormat == 'A':   lenWagon = int((len(code)-4)/3+1)
      elif codeFormat == 'B': lenWagon = int((len(code)-7)/5+1)
      else: print('ERROR: Invalid code format specified')
      return (lenWagon - 1) - code[1]

  moduleTypes = list(code[3::3])
  if len(moduleTypes) == 1:
    return 0
  if moduleTypes.count('F') == 1:
    return moduleTypes.index('F')

  earliestWagonID = instance
  earliestWagon = geomGrouped.get_group((earliestWagonID[0], earliestWagonID[1], earliestWagonID[2]))
  earliestWagonPartner = geomGrouped.get_group((earliestWagonID[0], earliestWagonID[1], not earliestWagonID[2]))

  u,v,irot,plane = earliestWagonPartner.loc[earliestWagonPartner['isEngine'],['u','v','irot','plane']].values.flatten().tolist()
 
  uEastEngine,vEastEngine = [sum(x) for x in zip([u,v],list(getUVDiff(plane,irot)))]

  coords = earliestWagon[['u','v']].values.tolist()
  index = [i for i in range(len(coords)) if coords[i] == [uEastEngine,vEastEngine]][0]

  if code in recodedCodesList:
    lenWagon = len(code[3::3])
    index = (lenWagon - 1) - index

  return index

def findEastEngineModule(plane,uWest,vWest,irotWest):

  uEastEngine,vEastEngine = [sum(x) for x in zip([uWest,vWest],list(getUVDiff(plane,irotWest)))]
  return uEastEngine,vEastEngine

def nextModule(plane,u,v,irot,angle,orient):

  uNext,vNext = [sum(x) for x in zip([u,v],list(getUVDiff(plane,angle+irot)))]
  return uNext,vNext,(irot+orient)%6

def reverseAngleOrient(angle,orient):

  return (angle + 3 - orient) % 6,(orient * -1) % 6

def maxLinksCalculation(code,codeFormat,linkType,wagonCodesDict,geomGrouped,recodedCodesList):

  isHD = code[0]

  if codeFormat == 'A':   maxLinksList = [0] * int((len(code)-4)/3+1)
  elif codeFormat == 'B': maxLinksList = [0] * int((len(code)-7)/5+1)
  else: print('ERROR: Invalid code format specified')

  linkTypeOptions = ['trigLinks','dataLinks_ld','dataLinks_hd']
  if linkType not in linkTypeOptions: print('ERROR: Invalid link type specified: {}. Must be in {}'.format(linkType,linkTypeOptions))

  for instance in wagonCodesDict[code]:

    geomTemp = geomGrouped.get_group((instance[0],instance[1],instance[2]))
    if not isHD: geomTempPartner = geomGrouped.get_group((instance[0],instance[1],not int(instance[2])))

    plane,icassette,MB,wagon = geomTemp[['plane','icassette','MB','wagon']].iloc[0]

    angleOrientCodes = []
    if not isHD: # LD
      if codeFormat == 'A':
        if code[1] >= 0:
          eastWest = 1
          enginePos = code[1]
        else:
          eastWest = 0
          enginePos = findEngine(code,codeFormat,instance,geomGrouped,recodedCodesList)
        if len(code) > 4:
          for i in range(int((len(code)-4)/3+1)): angleOrientCodes += list(code[(3*i+4):(3*i+6)])
      elif codeFormat == 'B':
        eastWest = code[1]
        enginePos = code[2]
        if len(code) > 7: 
          for i in range(int((len(code)-7)/5+1)): angleOrientCodes += list(code[(5*i+7):(5*i+9)])
      if eastWest: # West
        u,v,irot = geomTemp[['u','v','irot']].loc[geomTemp['isEngine']].iloc[0]
      else: # East
        uWest,vWest,irotWest = [int(x) for x in geomTempPartner[['u','v','irot']].loc[geomTempPartner['isEngine']].iloc[0]]
        u,v = findEastEngineModule(plane,uWest,vWest,irotWest)
        irot = geomTemp['irot'].loc[(geomTemp['u'] == u) & (geomTemp['v'] == v)].iloc[0]
        u,v,irot = [int(x) for x in [u,v,irot]]
    else: # HD
      if codeFormat == 'A':
        enginePos = code[1]
        if len(code) > 4: 
          for i in range(int((len(code)-4)/3+1)): angleOrientCodes += list(code[(3*i+4):(3*i+6)])
      elif codeFormat == 'B':
        enginePos = code[2]
        if len(code) > 7:
          for i in range(int((len(code)-7)/5+1)): angleOrientCodes += list(code[(5*i+7):(5*i+9)])
      u,v,irot = geomTemp[['u','v','irot']].loc[geomTemp['isEngine']].iloc[0]
 
    links = []
    if enginePos == 0: links.append(geomTemp[linkType].loc[(geomTemp['u'] == u) & (geomTemp['v'] == v)].iloc[0])
    else:
      #print(code)
      uPrev,vPrev,irotPrev = [u,v,irot]
      for i in reversed(range(enginePos)):
        angleRev,orientRev = reverseAngleOrient(int(code[5*i+7]),int(code[5*i+8])) if codeFormat == 'B' else reverseAngleOrient(int(code[3*i+4]),int(code[3*i+5]))
        uPrev,vPrev,irotPrev = nextModule(plane,uPrev,vPrev,irotPrev,angleRev,orientRev)
      links.append(geomTemp[linkType].loc[(geomTemp['u'] == uPrev) & (geomTemp['v'] == vPrev)].iloc[0])
      u,v,irot = uPrev,vPrev,irotPrev
      #print(plane,u,v,angleOrientCodes)
    uCurr,vCurr,irotCurr = [u,v,irot]
    for i in range(int(len(angleOrientCodes)/2)):
      uNext,vNext,irotNext = nextModule(plane,uCurr,vCurr,irotCurr,angleOrientCodes[2*i],angleOrientCodes[2*i+1])
      #print(code,plane,uCurr,vCurr,irotCurr,angleOrientCodes[2*i],angleOrientCodes[2*i+1],'next:',uNext,vNext,irotNext)
      links.append(geomTemp[linkType].loc[(geomTemp['u'] == uNext) & (geomTemp['v'] == vNext)].iloc[0])
      uCurr,vCurr,irotCurr = [uNext,vNext,irotNext]
      
    for i in range(len(maxLinksList)):
      if links[i] > maxLinksList[i]: maxLinksList[i] = links[i]

  maxLinksList = [int(x) for x in maxLinksList]

  return maxLinksList

##################################################
# MAIN
##################################################
def main():

  # Specify the geometry file to be used
  geomVersion = 'v16.6'
  geometryPath = '../hgcal_modmap/geometries/{}/'.format(geomVersion)
  geometryFile = 'geometry_sipmontile.hgcal'
  gitHash = subprocess.check_output('git -C ../hgcal_modmap/ rev-parse --short HEAD',shell=True).decode('utf-8')

  parser = argparse.ArgumentParser(description='Wagon Variety Analyzer')
  parser.add_argument('--geomVersion',type=str,default=geomVersion,help='Geometry version')
  parser.add_argument('--geomPath',type=str,default=geometryPath,help='Directory containing geometry file')
  parser.add_argument('--noImages',action='store_true',default=False,help='Turns off saving of wagon images')
  parser.add_argument('--noWagonDict',action='store_true',default=False,help='Turns off writing of wagon dictionary file (locations of all instances)')
  parser.add_argument('--noTables',action='store_true',default=False,help='Turns off writing of LaTeX tables with wagon info')
  args = parser.parse_args()
  
  geomVersion = args.geomVersion
  geometryPath = args.geomPath

  # Rounding (decimal places)
  dec = 3

  # Configuration parameters
  threesSeparate = False
  LDHalvesSemisFivesSame = True
  HDSemisSame = True
  LDHDBoth = 2

  # Extract required columns
  geom = pd.read_csv('{0}{1}.txt'.format(geometryPath,geometryFile),delim_whitespace=True)
  geomBasic = geom[['plane','u','v','x0','y0', 'vx_0', 'vy_0', 'vx_1', 'vy_1', 'vx_2', 'vy_2', 'vx_3', 'vy_3', 'vx_4', 'vy_4', 'vx_5', 'vy_5', 'vx_6', 'vy_6', 'itype','irot','MB','wagon','isEngine','HDorLD','trigLinks','dataLinks_ld','dataLinks_hd','icassette','engine_ctrl_fibres']].copy()
  geomBasic['itypeName'] = geomBasic['itype']

  # Remove tile modules (TM)
  geomBasic = geomBasic[~geomBasic['itype'].str.contains('TM')]

  geomBasic['irot'] = geomBasic['irot'].astype('int')

  if not threesSeparate: geomBasic = geomBasic[~geomBasic['itype'].str.contains('c')] # Threes don't affect wagon shape

  # Add distance from origin
  geomBasic['r'] = np.sqrt(geomBasic['x0']**2 + geomBasic['y0']**2)

  # HD
  geomBasic.loc[(geomBasic['HDorLD']) & (geomBasic['itype'].str.contains('aIe')),'irot'] += 3

  if LDHalvesSemisFivesSame:

    # LD Halves (a[O|M]e + T/B)
    geomBasic.loc[(geomBasic['itype'].str.contains('aOe|aMe')) & (geomBasic['itype'].str[-1] == 'B'),'irot'] += 5
    geomBasic.loc[(geomBasic['itype'].str.contains('aOe|aMe')) & (geomBasic['itype'].str[-1] == 'T'),'irot'] += 1
    geomBasic.loc[(geomBasic['itype'].str.contains('aOe|aMe')) & (geomBasic['itype'].str[-1] == 'B'),'itypeName'] = 'Half Bottom'
    geomBasic.loc[(geomBasic['itype'].str.contains('aOe|aMe')) & (geomBasic['itype'].str[-1] == 'T'),'itypeName'] = 'Half Top'

    # LD Semis (d[O|M]e + R/L)
    geomBasic.loc[(geomBasic['itype'].str.contains('dOe|dMe')) & (geomBasic['itype'].str[-1] == 'R'),'irot'] += 0
    geomBasic.loc[(geomBasic['itype'].str.contains('dOe|dMe')) & (geomBasic['itype'].str[-1] == 'L'),'irot'] += 3
    geomBasic.loc[(geomBasic['itype'].str.contains('dOe|dMe')) & (geomBasic['itype'].str[-1] == 'R'),'itypeName'] = 'Semi Right'
    geomBasic.loc[(geomBasic['itype'].str.contains('dOe|dMe')) & (geomBasic['itype'].str[-1] == 'L'),'itypeName'] = 'Semi Left'
  
    # LD Fives (b[O|M|OM]e + RL/LR)
    geomBasic.loc[(geomBasic['itype'].str.contains('bOe|bMe|bOMe')) & (geomBasic['itype'].str[-2:] == 'RL'),'irot'] += 3
    geomBasic.loc[(geomBasic['itype'].str.contains('bOe|bMe|bOMe')) & (geomBasic['itype'].str[-2:] == 'LR'),'irot'] += 3
    geomBasic.loc[(geomBasic['itype'].str.contains('bOe|bMe|bOMe')) & (geomBasic['itype'].str[-2:] == 'RL'),'itypeName'] = 'Five RL'
    geomBasic.loc[(geomBasic['itype'].str.contains('bOe|bMe|bOMe')) & (geomBasic['itype'].str[-2:] == 'LR'),'itypeName'] = 'Five LR'

    geomBasic.loc[geomBasic['itype'].str.contains('aOe|aMe'),'itype'] = 'd'
    geomBasic.loc[geomBasic['itype'].str.contains('bOe|bMe|bOMe'),'itype'] = 'd'

  if HDSemisSame:

    # HD Semis (dIe + R/L)
    geomBasic.loc[(geomBasic['itype'].str.contains('dIe')) & (geomBasic['itype'].str[-1] == 'R'),'irot'] += 0
    geomBasic.loc[(geomBasic['itype'].str.contains('dIe')) & (geomBasic['itype'].str[-1] == 'L'),'irot'] += 3

  else: 

    #geomBasic.loc[(geomBasic['itype'].str.contains('dIe')) & (geomBasic['itype'].str[-1] == 'R'),'itype'] = 'DIeR'
    geomBasic.loc[(geomBasic['itype'].str.contains('dIe')) & (geomBasic['itype'].str[-1] == 'R'),'irot'] += 0
    geomBasic.loc[(geomBasic['itype'].str.contains('dIe')) & (geomBasic['itype'].str[-1] == 'L'),'irot'] += 2

  # Reduce types to one character and standardize irot
  geomBasic['itype'] = geomBasic['itype'].str[0]
  geomBasic['irot'] %= 6


  #  Specify the file with the fiber counts
  fiberCountsFile = 'fiberCounts/fiberCounts_220221_163022.txt'
  fiberCounts = pd.read_csv(fiberCountsFile,delim_whitespace=True,dtype={'TlpGBT':'Int64'})
  geomBasic = pd.merge(geomBasic, fiberCounts,  how='left', on=['plane','MB'])

  # Get a subset (if needed)
  #geomBasic = geomBasic[(geomBasic['plane'] <= 28) | (geomBasic['plane'] >= 37)]
  if LDHDBoth == 0: 	geomBasic = geomBasic[geomBasic['HDorLD'] == 0]
  elif LDHDBoth == 1: 	geomBasic = geomBasic[geomBasic['HDorLD'] == 1]

  # Group modules by plane (layer), MB index, and wagon index
  geomGrouped = geomBasic.sort_values('r',ascending=True).groupby(['plane','MB','wagon'])

  #print(geomGrouped.get_group((1,3,0)))
  #print('#'*50)
  #print(geomGrouped.get_group((2,1,0)))

  wagonCodes = []
  wagonCodesDict = {}
  for name, group in geomGrouped:
    
    newCode = []

    # Put the engine first, then sort by distance from center
    group = group.sort_values(['isEngine','r'],ascending=[False,True])

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

  maxLinks = {x:maxLinksCalculation(x,'A','trigLinks',wagonCodesDict,geomGrouped,[]) for x in wagonCodesDict}

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
  maxLinks = {x:maxLinksCalculation(x,'A','trigLinks',wagonCodesDict,geomGrouped,recodedCodesList) for x in wagonCodesDict}

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

  # Finding engine pos. for east wagons
  eastEnginePositions = {x:findEngine(x,'A',wagonCodesDict[x][0],geomGrouped,recodedCodesList) for x in wagonCodesDict if x[1] == -1 and x[0] == 0}

  # Print message about total number of HD wagons with <= 14 trigger links
  #print(numTrigLinksHDLT15,'out of',numHD,'(','{:.1f}'.format(numTrigLinksHDLT15 * 100.0 / numHD),'%) HD wagons have <= 14 trigger links')

  # Remove empty Counter entries
  codeCounter = Counter({i:j for i,j in codeCounter.items() if j != 0})

  wagonNameDict = {
    # HD
    '1000F5000F7000Fb0'		: 'WH30A1',
    '1000F4000F5000F50'		: 'WH30B1',
    '1000F6000F7040F60'		: 'WH30C1',
    '1000F4000F5040F50'		: 'WH30D1',
    '1000F5000F7000F9005d70'	: 'WH31A1',
    '1000F5000F5000a4040F50'	: 'WH31B1',
    '1000F5000F50'		: 'WH20A1',
    '1000F6000F9000g80'		: 'WH21A1',
    # LD
    '0000F2000F2000F2000F11'	: 'WE40A1',
    '0000F2000F2000F2005d11'	: 'WE31A1',
    '0030d1152F2030F2030F20'	: 'WE31A2', # Merged into WE31A1
    '0030F2030F2022F1124F20'	: 'WE40A2',
    '0000F2014F2012F2015d11'	: 'WE31A3',
    '0101F2030F2030F20'		: 'WW30A1', # W3A
    '0100F3030F2031d20'		: 'WW21A1',
    '0001F2000F2005d20'		: 'WE21A1',
    '0000F2000F2000F20'		: 'WE30A1', # E3A
    '0001F3000F2005d10'		: 'WE21B1',
    '0000F3015d2000d20'		: 'WE12A1',
    '0100F3121d2030d20'		: 'WW12A1',
    '0010F2030F2022F20'		: 'WE30A2', 
    '0100F2014F2030F20'		: 'WW30B1', # Lefty python
    '0000F2014F2012F20'		: 'WE30A3', # East T
    '0101F2030F2031d20'		: 'WW21B1',
    '0000F2015d2001F20'		: 'WE21C1',
    '0100F2022F2024F20'		: 'WW30B2', # West T
    '0111F2000F2014F20'		: 'WW30A2',
    '0100F3014F2031d20'		: 'WW21C1',
    '0000F0022F0005d00'		: 'WE21D1',
    '0100F2020d2041d20'		: 'WW12B1', # Merged into WW12A1
    '0000F2010d2055d20'		: 'WE12B1', # Merged into WE12A1
    '0101F3030F2031d10'		: 'WW21D1',
    '0110d2044F2014F20'		: 'WW21E1',
    '0000F2010d2050F20'		: 'WE21C2', # Merged into WE21C1
    '0100F2020d2040F20'		: 'WW21E2',
    '0110F2000F2010d20'		: 'WW21E3',
    '0100F2030F2032d20'		: 'WW21E4', # Merged into WW21B1
    '0010F2030F2021d20'		: 'WE21C3',
    '0000F2014F2011d20'		: 'WE21C4',
    '0101F2010d2031d20'		: 'WW12C1',
    '0020d2052F2030F20'		: 'WE21C5', # Merged into WE21A1
    '0010d2052F2022F20'		: 'WE21C6',
    '0100F3130F41'		: 'WW20A1', # W2A
    '0000F3100F41'		: 'WE20A1', # E2A
    '0100F4031d20'              : 'WW11A1', # Used to be '0101F4031d20' before v16.3
    '0001F4005d20'		: 'WE11A1',
    '0001F3000F30'		: 'WE20B1', # E2B
    '0102F3030F20'		: 'WW20B1',
    '0100F4014F30'		: 'WW20C1',
    '0010d2052F20'		: 'WE11B1', # Merged into WE11A1
    '0101F3030F30'		: 'WW20D1',
    '0000F4021d20'		: 'WE11C1',
    '0100F2032d20'		: 'WW11B1', # Used to be '0101F2032d20' before v16.3, merged into WW11A1
    '0000F2015d20'		: 'WE11B2',
    '0002F3000F20'		: 'WE20E1',
    '0101F50'			: 'WW10A1', # W1A
    '0001F50'			: 'WE10A1', # E1A
    '0000F03'			: 'WE10B1',
    '0103F30'			: 'WW10B1', # Merged into WW10A1
  }    

  for tempCode,indices in wagonCodesDict.items():

    if tempCode[1] == -1: continue
    if not (len(tempCode) - 1) / 3 == 2: continue
    #print(tempCode)
    #print(indices)

    for index in indices:

      tempIndex = index

      geomTempIndex = geomBasic.loc[(geomBasic['plane'] == tempIndex[0]) & (geomBasic['MB']  == tempIndex[1]) & (geomBasic['wagon'] == tempIndex[2]) & (geomBasic['isEngine'])]
      u,v,irot = geomTempIndex[['u','v','irot']].iloc[0]

      angleCode,orientCode = tempCode[4],tempCode[5]
      angleCode = (angleCode + irot) % 6
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

    if not args.noImages: 
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

    # Change code[1] from engine position (or -1 for E, except for HD) to E/W + engine position
    if code[1] == -1 and code[0] == 0: # East LD wagons
      newCode[1] = 0
      newCode.insert(2,eastEnginePositions[code])
    elif code[0] == 1: # HD (always east) wagons
      newCode.insert(1,0)
    else: # W wagons
      newCode.insert(1,1)

    # Replace old with new code
    codeCounterCopy[tuple(newCode)] = codeCounterCopy[code] 
    del codeCounterCopy[code]
    wagonCodesDictCopy[tuple(newCode)] = wagonCodesDictCopy[code]
    del wagonCodesDictCopy[code]
    maxLinksCopy[tuple(newCode)] = maxLinks[code]
    del maxLinksCopy[code]
    recodedCodesList = [tuple(newCode) if x == tuple(code) else x for x in recodedCodesList]

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
      recodedCodesList = [tuple(newCode) if x == tuple(key) else x for x in recodedCodesList]

  # HD wagons, hard-code link compromises
  HDLinkCompomises = True
  if HDLinkCompomises:

    # Modify existing codes
    #wagonCodesDict[(1,0,0,0,'F','5',0,0,0,'F','7',0,0,0,'F','9',0,0,4,'d','7',0)] = wagonCodesDict.pop((1,0,0,0,'F','5',0,0,0,'F','7',0,0,0,'F','b',0,0,4,'d','7',0))
    #wagonCodesDict[(1,0,0,0,'F','5',0,0,0,'F','5',0,0,0,'a','4',0,4,0,'F','5',0)] = wagonCodesDict.pop((1,0,0,0,'F','5',0,0,0,'F','5',0,0,0,'a','5',0,4,0,'F','5',0))
    #wagonCodesDict[(1,0,0,0,'F','6',0,0,0,'F','9',0,0,0,'g','8',0)] = wagonCodesDict.pop((1,0,0,0,'F','6',0,0,0,'F','9',0,0,0,'g','a',0))
    
    # Add new codes
    wagonCodesDict[(1,0,0,0,'F','4',0,0,0,'F','5',0,0,0,'F','5',0)] = []
    wagonCodesDict[(1,0,0,0,'F','4',0,0,0,'F','5',0,4,0,'F','5',0)] = []
    wagonCodesDict[(1,0,0,0,'F','0',0,0,0,'F','0',0,0,0,'g','0',0)] = []

    unchangedHDCodes = [	'1000F5000F7000F9004d70',
				'1000F0000F0000F0005d00',
				'1000F5000F5000a4040F50',
				'1000F5000F50']
    wagonCodesDictCopy = copy.deepcopy(wagonCodesDict)
    for code,vals in wagonCodesDict.items():
      if code[0] == 0: continue # Ignore LD
      codeString = ''.join(str(x) for x in code)
      if codeString in unchangedHDCodes: continue
      for val in vals:

        geomTempIndex = geomGrouped.get_group((val[0],val[1],val[2]))
        plane,u,v,irot = geomTempIndex.loc[geomTempIndex['isEngine']][['plane','u','v','irot']].iloc[0]
        uLD,vLD,temp = nextModule(plane,u,v,irot,angle=3,orient=0)
        irotLD = geomBasic[(geomBasic['plane'] == plane) & (geomBasic['u'] == uLD) & (geomBasic['v'] == vLD)]['irot'].iloc[0]
        if irot == irotLD: engineType = 'half'
        elif (irot+3)%6 == irotLD: engineType = 'full'
        
        swapCode = None
        if codeString == '1000F5000F7000Fb0' and engineType == 'half': 		swapCode = (1,0,0,0,'F','4',0,0,0,'F','5',0,0,0,'F','5',0)
        elif codeString == '1000F6000F7040F60' and plane not in [1,3,5,7]: 	swapCode = (1,0,0,0,'F','4',0,0,0,'F','5',0,4,0,'F','5',0)
        elif codeString == '1000F6000F9000g80' and engineType == 'half': 	swapCode = (1,0,0,0,'F','0',0,0,0,'F','0',0,0,0,'g','0',0)

        if swapCode:
          wagonCodesDictCopy[code].remove(val)
          wagonCodesDictCopy[swapCode].append(val)

    wagonCodesDict = wagonCodesDictCopy  
    wagonCodesDict = {x:y for x, y in wagonCodesDict.items() if len(y) > 0} # Remove empty entries

  # Manually adjust routing
  # WE31A1: moving xover to module 4 rather than 1
  oldCode = (0,0,0,0,'F','1',1,0,0,'F','2',0,0,0,'F','2',0,0,5,'d','2',0)
  newCode = (0,0,0,0,'F','2',0,0,0,'F','2',0,0,0,'F','2',0,0,5,'d','1',1)
  if newCode not in wagonCodesDict: wagonCodesDict[newCode] = wagonCodesDict.pop(oldCode)
  else: print('ERROR: Attempting to replace {} with {} (manual adjustment), but the former already exists! Its information will be overwritten.'.format(oldCode,newCode))
  # WE31A3: moving xover to module 4 rather than 1
  oldCode = (0,0,0,0,'F','1',1,1,4,'F','2',0,1,2,'F','2',0,1,5,'d','2',0)
  newCode = (0,0,0,0,'F','2',0,1,4,'F','2',0,1,2,'F','2',0,1,5,'d','1',1)
  if newCode not in wagonCodesDict: wagonCodesDict[newCode] = wagonCodesDict.pop(oldCode)
  else: print('ERROR: Attempting to replace {} with {} (manual adjustment), but the former already exists! Its information will be overwritten.'.format(oldCode,newCode))
  # WE40A1: moving xover to module 4 rather than 1
  oldCode = (0,0,0,0,'F','1',1,0,0,'F','2',0,0,0,'F','2',0,0,0,'F','2',0)
  newCode = (0,0,0,0,'F','2',0,0,0,'F','2',0,0,0,'F','2',0,0,0,'F','1',1)
  if newCode not in wagonCodesDict: wagonCodesDict[newCode] = wagonCodesDict.pop(oldCode)
  else: print('ERROR: Attempting to replace {} with {} (manual adjustment), but the former already exists! Its information will be overwritten.'.format(oldCode,newCode))
  # WE40A2: moving xover to module 4 rather than 1
  oldCode = (0,0,3,0,'F','1',1,3,0,'F','2',0,2,2,'F','2',0,2,4,'F','2',0)
  newCode = (0,0,3,0,'F','2',0,3,0,'F','2',0,2,2,'F','1',1,2,4,'F','2',0)
  if newCode not in wagonCodesDict: wagonCodesDict[newCode] = wagonCodesDict.pop(oldCode)
  else: print('ERROR: Attempting to replace {} with {} (manual adjustment), but the former already exists! Its information will be overwritten.'.format(oldCode,newCode))

  # Compute useful objects
  codeCounter = Counter({tuple(key):len(val) for key,val in wagonCodesDict.items()})
  maxLinks = {x:maxLinksCalculation(x,'B','trigLinks',wagonCodesDict,geomGrouped,recodedCodesList) for x in wagonCodesDict}

  # Manual module index changes
  indexChanges = {
                        'WH31B1': [0,1,3,2],
			'WE40A2': [2,1,3,0],
			'WE31A2': [3,2,1,0],
			'WE30A2': [1,0,2],
			'WE21C3': [1,0,2],
			'WE21C5': [2,1,0],
			'WE21C6': [1,0,2],
			'WE11B1': [1,0],
			'WW21E3': [1,0,2],
			'WW21E1': [1,0,2],
			'WW30A2': [1,0,2],
			'WE12A1': [0,2,1],
                        'WE12B1': [0,2,1],
                        'WE21C1': [0,2,1],
                        'WE21C2': [0,2,1],
                        'WE21C4': [0,2,1],
                        'WE30A3': [0,2,1],
                        'WE31A3': [0,2,1,3],
                        'WW12A1': [0,2,1],
                        'WW12B1': [0,2,1],
                        'WW21E2': [0,2,1],
                        'WW30B2': [0,2,1],
		}

  # Compute partial and zipper info for LD wagons
  partialDict = {}
  partialNamesDict = {'Semi Right': 0,'Semi Left': 0,'Half Top': 0,'Half Bottom': 0,'Five LR': 0,'Five RL':0}
  partialZipperMap = {}
  zipperDict = {}
  zipperDictLocs = {}
  zipperTypeDict = {      'Semi Right':   'HS',
                          'Semi Left':    'HS',
                          'Half Top':     'HS',
                          'Half Bottom':  'HS',
                          'Five LR':      'LR',
                          'Five RL':      'RL',}

  for tempCode,indices in wagonCodesDict.items():
    tempCodeString = ''.join(str(x) for x in tempCode)
    wagonName = wagonNameDict[tempCodeString]
    isHD = int(tempCodeString[0])
    if isHD or (int(wagonName[3]) == 0): continue 
    partialDict[wagonName] = {i:partialNamesDict.copy() for i in range(int(wagonNameDict[tempCodeString][2]) + int(wagonNameDict[tempCodeString][3]))}
    #zipperDict[wagonName] = {i:zipperNamesDict.copy() for i in range(int(wagonNameDict[tempCodeString][2]) + int(wagonNameDict[tempCodeString][3]))}
    for index in indices:

      tempIndex = index
      geomTempIndex = geomGrouped.get_group((tempIndex[0],tempIndex[1],tempIndex[2]))

      geomTempPartnerIndex = geomGrouped.get_group((tempIndex[0],tempIndex[1],not tempIndex[2]))
      plane,icassette,MB,wagon = geomTempIndex[['plane','icassette','MB','wagon']].iloc[0]
      isWest = int(tempCodeString[1])
      if isWest: # West
        u,v,irot,x0,y0,trig0,daqLD0,daqHD0 = geomTempIndex[['u','v','irot','x0','y0','trigLinks','dataLinks_ld','dataLinks_hd']].loc[geomTempIndex['isEngine']].iloc[0]
      else: # East
        uWest,vWest,irotWest = [int(x) for x in geomTempPartnerIndex[['u','v','irot']].loc[geomTempPartnerIndex['isEngine']].iloc[0]]
        u,v = findEastEngineModule(plane,uWest,vWest,irotWest)
        irot,x0,y0,trig0,daqLD0,daqHD0 = geomTempIndex[['irot','x0','y0','trigLinks','dataLinks_ld','dataLinks_hd']].loc[(geomTempIndex['u'] == u) & (geomTempIndex['v'] == v)].iloc[0]
      u,v,irot = [int(x) for x in [u,v,irot]]
      uList = list('-'*4)
      vList = list('-'*4)
      irotList = list('-'*4)
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
      nModules = int((len(tempCodeString)-2)/5)
      nFull = int(wagonName[2])
      wagonRot = (irot + 3) % 6 if int(tempCodeString[1]) else irot

      # Record partial info across instances
      for i,(uTemp,vTemp) in enumerate(list(zip(uList,vList))):
        if uTemp == '-' or vTemp == '-': continue
        indexTemp = i
        if wagonName in indexChanges: indexTemp = indexChanges[wagonName][indexTemp]
        if geomTempIndex.loc[(geomTempIndex['u'] == uTemp) & (geomTempIndex['v'] == vTemp),'itype'].iloc[0][0] != 'F':
          pType = geomTempIndex.loc[(geomTempIndex['u'] == uTemp) & (geomTempIndex['v'] == vTemp),'itypeName'].iloc[0]
          partialDict[wagonNameDict[tempCodeString]][indexTemp][geomTempIndex.loc[(geomTempIndex['u'] == uTemp) & (geomTempIndex['v'] == vTemp),'itypeName'].iloc[0]] += 1 

          # Zippers
          if indexTemp != nFull and wagonName not in ['WE21C6','WW21E1']: zipperShape = 'N'
          elif isWest:
            if pType in ['Semi Right','Half Top','Five LR']: zipperShape = 'N'
            elif pType in ['Semi Left','Half Bottom','Five RL']: 
              if (tempCodeString[4] == 'F' and int(tempCodeString[7]) not in [0,3]) or wagonName == 'WW21E3': zipperShape = 'N'
              else: zipperShape = 'R'
            else: print('ERROR: Unexpected partial type: {}'.format(pType)) 
          else: # East
            if pType in ['Semi Right','Half Top','Five LR']: 
              if tempCodeString[4] == 'F' and int(tempCodeString[7]) not in [0,3]: zipperShape = 'N'
              else: zipperShape = 'L'
            elif pType in ['Semi Left','Half Bottom','Five RL']: zipperShape = 'N' 
            else: print('ERROR: Unexpected partial type: {}'.format(pType))
          # More special cases
          if [wagonName,indexTemp] in [['WW12B1',2],['WW21E2',2]]: zipperShape = 'L'
          elif [wagonName,indexTemp] in [['WE12B1',2],['WE21C2',2],['WW21E3',2],['WW12C1',1]]: zipperShape = 'R'
          zipperType = zipperTypeDict[pType] + zipperShape + ('G' if nModules == 4 else '0')
          if wagonName in zipperDict and indexTemp in zipperDict[wagonName] and zipperType in zipperDict[wagonName][indexTemp]: zipperDict[wagonName][indexTemp][zipperType] += 1
          else: zipperDict.setdefault(wagonName,{indexTemp:{zipperType:1}}).setdefault(indexTemp,{zipperType:1}).setdefault(zipperType,1)
          zipperDictLocs[tuple(tempIndex + [indexTemp])] = zipperType
          
          partialZipperMap.setdefault(wagonName,{indexTemp:{pType:zipperType}}).setdefault(indexTemp,{pType:zipperType}).setdefault(pType,zipperType)

  # WE40A1
  codeTemp = (0,0,0,0,'F','2',0,0,0,'F','2',0,0,0,'F','2',0,0,0,'F','1',1)
  partialDict['WE40A1'] = {3:{'Full':len(wagonCodesDict[codeTemp])}}
  zipperDict['WE40A1'] =  {3:{'HSNG':len(wagonCodesDict[codeTemp])}}
  partialZipperMap['WE40A1'] = {3:{'Full':'HSNG'}}
  for index in wagonCodesDict[codeTemp]:
    zipperDictLocs[tuple(index + [3])] = 'HSNG'
  # WE40A2
  codeTemp = (0,0,3,0,'F','2',0,3,0,'F','2',0,2,2,'F','1',1,2,4,'F','2',0)
  partialDict['WE40A2'] = {3:{'Full':len(wagonCodesDict[codeTemp])}}
  zipperDict['WE40A2'] =  {3:{'HSNG':len(wagonCodesDict[codeTemp])}}
  partialZipperMap['WE40A2'] = {3:{'Full':'HSNG'}}
  for index in wagonCodesDict[codeTemp]:
    zipperDictLocs[tuple(index + [3])] = 'HSNG'

  # Manual consolidations
  consolDict = {	(0,1,0,1,'F','5',0): 						[(0,1,0,3,'F','3',0)], 						# WW10A1 <-- WW10B1
			(0,0,0,1,'F','4',0,0,5,'d','2',0):				[(0,0,1,0,'d','2',0,5,2,'F','2',0)],				# WE11A1 <-- WE11B1
			(0,0,0,1,'F','2',0,0,0,'F','2',0,0,5,'d','2',0):		[(0,0,2,0,'d','2',0,5,2,'F','2',0,3,0,'F','2',0)],		# WE21A1 <-- WE21C5
			(0,0,0,0,'F','2',0,0,0,'F','2',0,0,0,'F','2',0,0,5,'d','1',1): 	[(0,0,3,0,'d','1',1,5,2,'F','2',0,3,0,'F','2',0,3,0,'F','2',0)],# WE31A1 <-- WE31A2
			(0,1,0,0,'F','4',0,3,1,'d','2',0): 				[(0,1,0,0,'F','2',0,3,2,'d','2',0)],				# WW11A1 <-- WW11B1
			(0,1,0,1,'F','2',0,3,0,'F','2',0,3,1,'d','2',0): 		[(0,1,0,0,'F','2',0,3,0,'F','2',0,3,2,'d','2',0)],		# WW21B1 <-- WW21E4
                        (0,0,0,0,'F','3',0,1,5,'d','2',0,0,0,'d','2',0):                [(0,0,0,0,'F','2',0,1,0,'d','2',0,5,5,'d','2',0)],              # WE12A1 <-- WE12B1
                        (0,0,0,0,'F','2',0,1,5,'d','2',0,0,1,'F','2',0):                [(0,0,0,0,'F','2',0,1,0,'d','2',0,5,0,'F','2',0)],              # WE21C1 <-- WE21C2
                        (0,1,0,0,'F','3',1,2,1,'d','2',0,3,0,'d','2',0):                [(0,1,0,0,'F','2',0,2,0,'d','2',0,4,1,'d','2',0)],              # WW12A1 <-- WW12B1
               }

  for targetCode,removingList in consolDict.items():
    targetName = wagonNameDict[''.join([str(x) for x in targetCode])]
    for removingCode in removingList:
      removingName = wagonNameDict[''.join([str(x) for x in removingCode])]
      wagonCodesDict[targetCode] += wagonCodesDict[removingCode]
      wagonCodesDict.pop(removingCode)
      if int(targetName[3]):
        for index,partialTypes in partialDict[removingName].items():
          for partial,count in partialTypes.items():
            partialDict[targetName][index][partial] = partialDict[targetName][index].get(partial,0) + count
        partialDict.pop(removingName)
        for index,zipperTypes in zipperDict[removingName].items():
          for zipper,count in zipperTypes.items():
            zipperDict[targetName][index][zipper] = zipperDict[targetName][index].get(zipper,0) + count
        zipperDict.pop(removingName)
        for index,partialMap in partialZipperMap[removingName].items():
          for partial,zipper in partialMap.items():
            if partial in partialZipperMap[targetName][index] and zipper != partialZipperMap[targetName][index][partial]:
              print('ERROR: Mapping of partial type to zipper types for module {} when merging {} ({}) into {} ({}) is not one-to-one'.format(index,removingName,zipper,targetName,partialZipperMap[targetName][index][partial]))
            partialZipperMap[targetName][index][partial] = zipper
        partialZipperMap.pop(removingName)
 
  # Final counts
  codeCounter = Counter({tuple(key):len(val) for key,val in wagonCodesDict.items()})
  maxLinks = {x:maxLinksCalculation(x,'B','trigLinks',wagonCodesDict,geomGrouped,recodedCodesList) for x in wagonCodesDict}
  maxDAQLinksLD = {x:maxLinksCalculation(x,'B','dataLinks_ld',wagonCodesDict,geomGrouped,recodedCodesList) for x in wagonCodesDict}
  maxDAQLinksHD = {x:maxLinksCalculation(x,'B','dataLinks_hd',wagonCodesDict,geomGrouped,recodedCodesList) for x in wagonCodesDict}
  maxDAQLinks = {}
  for key,val in maxDAQLinksLD.items():
    if key[0] == 0: maxDAQLinks[key] = maxDAQLinksLD[key]
    elif key[0] == 1: maxDAQLinks[key] = maxDAQLinksHD[key]
    else: print('ERROR: Unknown first code in {}'.format(key))

  # Print out forbidden/prohibited DC/DC locations
  #for code,indices in wagonCodesDict.items():
  #  wagonName = wagonNameDict[''.join([str(x) for x in code])]
  #  if wagonName in ['WE31A3','WE12A1','WW12A1','WE30A2','WW30B1','WE21C1','WW30A2','WW21C1','WE21D1','WW12B1','WE21C4','WE21C6','WW21E1','WE12B1','WE21C2','WW21E2','WW21E3','WE21C3','WW12C1','WW20C1','WE11C1','WE11B2']: 
  #    for index in indices:
  #      plane,MB,wagon = index
  #      geomTempIndex = geomGrouped.get_group((plane,MB,wagon))
  #      geomTempPartnerIndex = geomGrouped.get_group((plane,MB,not wagon))
  #      isWest = 'WW' in wagonName
  #      if isWest:
  #        u,v = geomTempIndex[['u','v']].loc[geomTempIndex['isEngine']].iloc[0]
  #      else: # East
  #        uWest,vWest,irotWest = [int(x) for x in geomTempPartnerIndex[['u','v','irot']].loc[geomTempPartnerIndex['isEngine']].iloc[0]]
  #        u,v = findEastEngineModule(plane,uWest,vWest,irotWest)
  #      print('{} {} {}'.format(plane,u,v))

  # ----------------------------------------------
  # Make LD wagon info tables
  # ----------------------------------------------

  # Crosspoint mapping for wagon link config file
  crosspointLinkOutputMap = {   'TRIG0':        3,
                                'TRIG1':        2,
                                'TRIG2':        1,
                                'TRIG3':        0,}
  crosspointLinkInputMap = {    'DAQ1':         2,
                                'DAQ0':         1,
                                'TRIG4':        0,}
  eastDAQMap = {4:0,5:1,6:2,3:4}

  if not args.noTables:

    trigRoutingGeomDict = {}
    xOverInRoutingGeomDict = {}
    DAQRoutingGeomDict = {}

    wagonLinkConfig = {}

    # Load information about wagon nicknames and resistors
    LDWagonIdentifiers = pd.read_csv('wagonInfo/LDWagonIdentifiers.txt')

    if not os.path.exists('output/latex/{}'.format(geomVersion)): os.makedirs('output/latex/{}'.format(geomVersion))
    f = open('output/latex/{}/LDWagonInfo.tex'.format(geomVersion),'w')

    f.write('\\documentclass[10pt]{article}\n')
    f.write('\\renewcommand{\\familydefault}{\\ttdefault}\n')
    f.write('\\usepackage[margin=1in]{geometry}\n')
    f.write('\\usepackage{hyperref}\n')
    f.write('\\usepackage{tikz}\n')
    f.write('\\usepackage{multicol}\n')
    f.write('\\usepackage{pdflscape}\n')
    f.write('\\setlength\columnsep{15pt}\n')
    f.write('\\usepackage{tocloft}\n')
    f.write('\\renewcommand{\cftsecleader}{\cftdotfill{\cftdotsep}}\n')
    f.write('\\setlength{\cftbeforesecskip}{0pt}\n')
    f.write('\\renewcommand{\contentsname}{}\n')
    f.write('\\setcounter{secnumdepth}{0}\n')
    f.write('\\setcounter{tocdepth}{2}\n')
    f.write('\\hypersetup{linktoc=all}\n')
    f.write('\\usepackage{graphicx}\n')
    f.write('\\parindent=0pt\n')
    f.write('\\parskip=15pt\n')
    f.write('\\begin{document}\n')
    f.write('\\begin{center}\n')
    f.write('{\huge LD Wagon Design Information}\n\n')
    f.write('\\vspace{-10pt}\n')
    f.write('{{Produced with Hgcal Modmap {} with git hash {}}}\n'.format(geomVersion.replace('_','\_'),gitHash))
    f.write('\\end{center}\n')
    f.write('\\begin{multicols}{2}\n')
    f.write('\\tableofcontents\n')
    f.write('\\end{multicols}\n')
    f.write('\\newpage\n')

    for key,_ in sorted(wagonCodesDict.items(),key=lambda x:(wagonNameDict[''.join([str(y) for y in x[0]])]),reverse=False):
      codeString = ''.join([str(x) for x in key])
      code = codeString
      wagonName = wagonNameDict[codeString]
      nFull = int(wagonNameDict[codeString][2])
      nPartials = int(wagonNameDict[codeString][3])
      nModules = nFull + nPartials
      if int(code[0]) != 0: continue
      nXin = int(code[3])
      isWest = int(code[1])
      code = code[5:]
      code = [code[i:i+2] for i in range(0, len(code), 5)]
      code = [[int(x[0]),int(x[1])] for x in code]

      f.write('\\begin{tikzpicture}[overlay, remember picture]\n')
      f.write('\\node[xshift=-2in,yshift=-1.75in] at (current page.north east) {{\IfFileExists{{/Users/devinmahon/Documents/CMS/wagonCounter/output/wagonImages/cartoons/{}.png}}{{\includegraphics[width=0.85in,height=0.85in,keepaspectratio]{{/Users/devinmahon/Documents/CMS/wagonCounter/output/wagonImages/cartoons/{}.png}}}}{{\includegraphics[width=0.85in,height=0.85in,keepaspectratio]{{/Users/devinmahon/Downloads/NotFound.png}}}}}};\n'.format(wagonNameDict[codeString],wagonNameDict[codeString]))
      f.write('\\node[xshift=-2in,yshift=-2.3in] at (current page.north east) {{Nickname: {}}};\n'.format(LDWagonIdentifiers[LDWagonIdentifiers['typecode'] == wagonName]['nickname'].iloc[0] if wagonName in LDWagonIdentifiers['typecode'].values else 'Not found'))
      f.write('\\node[xshift=-2in,yshift=-2.5in] at (current page.north east) {{ID Resistor: {} $\Omega$}};\n'.format('Not found' if wagonName not in LDWagonIdentifiers['typecode'].values or np.isnan(LDWagonIdentifiers[LDWagonIdentifiers['typecode'] == wagonName]['resistor'].iloc[0]) else LDWagonIdentifiers[LDWagonIdentifiers['typecode'] == wagonName]['resistor'].iloc[0]))
      f.write('\\node (rect) at ([xshift=-2in,yshift=-1.95in] current page.north east) [draw,thick,minimum width=2.0in,minimum height=1.5in] {};\n')
      f.write('\\end{tikzpicture}\n\n')

      f.write('\\section{{{} ({})}}\n\n'.format(wagonNameDict[codeString],codeString))
      f.write('\\vspace{-20pt}\n')
      f.write('N = {} full detector\n\n'.format(codeCounter[key] * 6))

      trigRouting  = []
      DAQRouting   = []
      xOverRouting = []

      linkList = maxLinks[key]
      if wagonNameDict[codeString] in indexChanges: 
        for i in range(len(linkList)):
          linkList[i] = linkList[indexChanges[wagonNameDict[codeString]][i]]
      for Mi,nT in enumerate(linkList):
         for Ti in range(nT):
           #if (Ti + 1) > code[Mi][0]: 	xOverRouting.append('M{}.{}'.format(Mi+1,Ti))
           if (Ti + 1) > code[indexChanges[wagonNameDict[codeString]].index(Mi) if wagonNameDict[codeString] in indexChanges else Mi][0]:  xOverRouting.append('M{}.{}'.format(Mi+1,Ti))
           else:			trigRouting.append('M{}.{}'.format(Mi+1,Ti))

      linkList = maxDAQLinks[key]
      if wagonNameDict[codeString] in indexChanges:
        for i in range(len(linkList)):
          linkList[i] = linkList[indexChanges[wagonNameDict[codeString]][i]]
      for Mi,nD in enumerate(linkList):
        for Di in range(nD):
          DAQRouting.append('M{}.{}'.format(Mi+1,Di))

      for i in range(nXin): trigRouting.append('X.{}'.format(i))

      trigRouting[len(trigRouting):]  = ['-' for x in range(7 - len(trigRouting))]
      if not isWest: trigRouting = list(reversed(trigRouting))
      if not isWest: DAQRouting = ['-'] * 3 + DAQRouting
      DAQRouting[len(DAQRouting):]   = ['-' for x in range(7 - len(DAQRouting))]
      xOverRouting[len(xOverRouting):] = ['-' for x in range(3 - len(xOverRouting))]
      if len(trigRouting) != 7 and DAQRouting != 7 and xOverRouting != 3: print('ERROR: Incorrect length of routing arrays')
      if not isWest: DAQRouting = [DAQRouting[i] for i in [0,1,2,6,3,4,5]]

      trigRoutingDict = {'TRIG\_ELINK{}\_{}'.format('W' if isWest else 'E',i):x for (i,x) in zip(np.arange(len(trigRouting)),trigRouting) if x != '-'}
      xOverOutRoutingDict = {'XING\_ELINK\_{}'.format(i):x for (i,x) in zip(np.arange(len(xOverRouting)),xOverRouting) if x != '-'}
      
      modTrigRoutingDict = {}
      xOverInRoutingDict = {}
      for link,mod in trigRoutingDict.items():
        if 'M' in mod: modTrigRoutingDict[mod] = link
        elif 'X' in mod: xOverInRoutingDict[mod] = link
      for link,mod in xOverOutRoutingDict.items():
        if 'M' in mod: modTrigRoutingDict[mod] = link
      modTrigRoutingDict = sorted(modTrigRoutingDict.items(),key=lambda x: x[0])
      xOverInRoutingDict = sorted(xOverInRoutingDict.items(),key=lambda x: x[0])

      modDAQRoutingDict = {x:'DAQ\_ELINK{}\_{}'.format('W' if isWest else 'E',i) for (i,x) in zip(np.arange(len(DAQRouting)),DAQRouting) if x != '-'}
      modDAQRoutingDict = sorted(modDAQRoutingDict.items(),key=lambda x: x[0])

      modTrigRoutingDict = [list(x) for x in modTrigRoutingDict]
      xOverInRoutingDict = [list(x) for x in xOverInRoutingDict]
      modDAQRoutingDict  = [list(x) for x in modDAQRoutingDict]

      # Save info for geometry file
      trigRoutingGeom = []
      xOverInRoutingGeom = []
      DAQRoutingGeom = []
      for mod,link in modTrigRoutingDict:
        if 'TRIG' in link: 	trigRoutingGeom.append('{}:T{}.{}'.format(mod,'W' if isWest else 'E',link[-1]))
        else: 			trigRoutingGeom.append('{}:X.{}'.format(mod,link[-1]))
      for mod,link in xOverInRoutingDict:
        xOverInRoutingGeom.append('{}:T{}.{}'.format(mod,'W' if isWest else 'E',link[-1]))
      for mod,link in modDAQRoutingDict:
        DAQRoutingGeom.append('{}:D1.{}'.format(mod,link[-1]))

      trigRoutingGeomDict[wagonName]  	= ','.join(trigRoutingGeom) if trigRoutingGeom else '-'
      xOverInRoutingGeomDict[wagonName]	= ','.join(xOverInRoutingGeom) if xOverInRoutingGeom else '-'
      DAQRoutingGeomDict[wagonName] 	= ','.join(DAQRoutingGeom) if DAQRoutingGeom else '-'

      f.write('Trig lpGBT\n\n\\vspace{-10pt}\n')
      headers = ['Index'] + list(np.arange(7))
      table = [[''] + trigRouting]
      f.write(tabulate(table,headers,tablefmt="latex_raw",))
      f.write('\n\n')

      f.write('DAQ lpGBT\n\n\\vspace{-10pt}\n')
      headers = ['Index (Wagon Label)'] + ['0(W0)','1(W1)','2(W2)','3(X)','4(E0)','5(E1)','6(E2)']
      table = [[''] + DAQRouting]
      f.write(tabulate(table,headers,tablefmt="latex_raw",))
      f.write('\n\n')

      f.write('Crossover\n\n\\vspace{-10pt}\n')
      headers = ['Index'] + list(np.arange(3))
      table = [[''] + xOverRouting]
      f.write(tabulate(table,headers,tablefmt="latex_raw"))
      f.write('\n\n')

      headers = ['Module Indices','Trigger Link Distribution','DAQ Link Distribution']
      table = [['\includegraphics[width=0.2\\textwidth]{{/Users/devinmahon/Documents/CMS/wagonCounter/output/wagonImages/indices/{}.jpg}}'.format(wagonNameDict[codeString]),'\includegraphics[width=0.2\\textwidth]{{/Users/devinmahon/Documents/CMS/wagonCounter/output/wagonImages/trig/{}.jpg}}'.format(wagonNameDict[codeString]),'\includegraphics[width=0.2\\textwidth]{{/Users/devinmahon/Documents/CMS/wagonCounter/output/wagonImages/DAQ/{}.jpg}}'.format(wagonNameDict[codeString])]]
      f.write(tabulate(table,headers,tablefmt="latex_raw"))
      f.write('\n\n')

      if wagonName in zipperDict:

        f.write('\\begin{multicols}{2}\n\n')
        f.write('\\raggedcolumns\n')
        f.write('Zipper Module Types\n\n\\vspace{-10pt}\n')
        for index,typeCounts in partialDict[wagonNameDict[codeString]].items():
          if sum([n for pType,n in typeCounts.items()]):
            indexTemp = index
            #if wagonNameDict[codeString] in indexChanges: indexTemp = indexChanges[wagonNameDict[codeString]][index]
            headers = ['Module {}'.format(indexTemp+1),'Zipper','N Full Detector']
            table = []
            for pType,pCount in typeCounts.items():
              if pCount == 0: continue
              table.append([pType,partialZipperMap[wagonName][indexTemp][pType],str(pCount * 6)])
            f.write(tabulate(table,headers,tablefmt="latex_raw"))
            f.write('\n\n')

        f.write('\\columnbreak\n')
        f.write('Zipper Types\n\n\\vspace{-10pt}\n')
        headers = ['Zipper','N']
        zipperCountsDict = {}
        table = []
        for index,typeCounts in zipperDict[wagonName].items():
          for zipperName,zipperCount in typeCounts.items():
            if zipperName in zipperCountsDict: zipperCountsDict[zipperName] += zipperCount
            else: zipperCountsDict[zipperName] = zipperCount
        for name,count in zipperCountsDict.items():
          table.append([name,count * 6])
        f.write(tabulate(table,headers,tablefmt="latex_raw"))
        f.write('\n\n')

        f.write('\\end{multicols}\n\n')

      f.write('\\begin{multicols}{2}\n\n')

      if modTrigRoutingDict:
        f.write('Trig links sorted by module\n\n\\vspace{-10pt}\n')
        headers = ['Module Trig Link','Trig Link']
        table = modTrigRoutingDict
        f.write(tabulate(table,headers,tablefmt="latex_raw"))
        f.write('\n\n')
      else:
        f.write('This wagon has no trig links\n\n')

      f.write('\\columnbreak\n')

      if modDAQRoutingDict: 
        f.write('DAQ links sorted by module\n\n\\vspace{-10pt}\n')
        headers = ['Module DAQ Link','DAQ Link']
        table = modDAQRoutingDict
        f.write(tabulate(table,headers,tablefmt="latex_raw"))
        f.write('\n\n')

      f.write('\\end{multicols}\n\n')

      if xOverInRoutingDict:
        f.write('Incoming crossover trig links sorted by link index\n\n\\vspace{-10pt}\n')
        headers = ['Crossover Trig Link','Trig Link']
        table = xOverInRoutingDict
        f.write(tabulate(table,headers,tablefmt="latex_raw"))
        f.write('\n\n')

      f.write('\n\\newpage\n')

      #------------------------
      # Wagon link config json
      #------------------------
      
      # Create actual dicts
      modTrigRoutingDictNew = {}
      for pair in modTrigRoutingDict: modTrigRoutingDictNew[pair[0]] = pair[1]
      modDAQRoutingDictNew = {}
      for pair in modDAQRoutingDict: modDAQRoutingDictNew[pair[0]] = pair[1]
      xOverInRoutingDictNew = {}
      for pair in xOverInRoutingDict: xOverInRoutingDictNew[pair[0]] = pair[1]

      wagonLinkConfig[wagonName] = {'IDResistor':'Unknown' if wagonName not in LDWagonIdentifiers['typecode'].values or np.isnan(LDWagonIdentifiers[LDWagonIdentifiers['typecode'] == wagonName]['resistor'].iloc[0]) else int(LDWagonIdentifiers[LDWagonIdentifiers['typecode'] == wagonName]['resistor'].iloc[0])}
      modTrigRoutingDict
      for iMod in np.arange(nModules) + 1:
        hasTrig4 = True if 'M{}.{}'.format(iMod,4) in modTrigRoutingDictNew.keys() else False
        nInputs = len([x for x in modDAQRoutingDictNew.keys() if 'M{}'.format(iMod) in x]) + (1 if hasTrig4 else 0)
        for iInput in range(nInputs):
          if iInput == 0 and hasTrig4:
            linkString = modTrigRoutingDictNew['M{}.4'.format(iMod)].replace('\\','')
            linkString = ''.join([x for i,x in enumerate(linkString.split('_')) if i in [0,2]])
            modLinkString = 'TRIG4'
            wagonLinkConfig[wagonName].setdefault('Mod{}'.format(iMod),{}).setdefault('Inputs',{}).setdefault(crosspointLinkInputMap[modLinkString],{'Eng_Elink':linkString,'Mod_Elink':modLinkString,'Invert':0})
          else:
            iDAQLink = iInput if not hasTrig4 else iInput-1
            linkString = modDAQRoutingDictNew['M{}.{}'.format(iMod,iDAQLink)].replace('\\','')
            linkString = ''.join([x for i,x in enumerate(linkString.split('_')) if i in [0,2]])
            if wagonName[1] == 'E': linkString = linkString[:-1] + str(eastDAQMap[int(linkString[-1])])
            modLinkString = 'DAQ{}'.format(iDAQLink)
            wagonLinkConfig[wagonName].setdefault('Mod{}'.format(iMod),{}).setdefault('Inputs',{}).setdefault(crosspointLinkInputMap[modLinkString],{'Eng_Elink':linkString,'Mod_Elink':modLinkString,'Invert':0})
        nOutputs = len([x for x in modTrigRoutingDictNew.keys() if 'M{}'.format(iMod) in x]) - (1 if hasTrig4 else 0)
        for iOutput in range(nOutputs):
          iTrigLink = iOutput
          linkString = modTrigRoutingDictNew['M{}.{}'.format(iMod,iTrigLink)].replace('\\','')
          linkString = ''.join([x for i,x in enumerate(linkString.split('_')) if i in [0,2]])
          modLinkString = 'TRIG{}'.format(iTrigLink)
          wagonLinkConfig[wagonName].setdefault('Mod{}'.format(iMod),{}).setdefault('Outputs',{}).setdefault(crosspointLinkOutputMap[modLinkString],{'Eng_Elink':linkString,'Mod_Elink':modLinkString,'Invert':0})

      # Add incoming trigger links
      if xOverInRoutingDictNew:
        for iXOver, (xOverString,trigLinkString) in enumerate(xOverInRoutingDictNew.items()):
          wagonLinkConfig[wagonName].setdefault('ModX',{}).setdefault('Inputs',{}).setdefault(iXOver,{'Eng_Elink':'XING{}'.format(xOverString.split('.')[-1]),'Mod_Elink':'Crossover','Invert':0})
          wagonLinkConfig[wagonName].setdefault('ModX',{}).setdefault('Outputs',{}).setdefault(iXOver,{'Eng_Elink':'TRIG{}'.format(trigLinkString.split('_')[-1]),'Mod_Elink':'Crossover','Invert':0})
      else:
        wagonLinkConfig[wagonName].setdefault('ModX',{})

    #------------------------------
    # Wagons by layer summary page
    #------------------------------
    f.write('\\begin{landscape}\n\n')
    f.write('\\section{{Wagons Per Layer}}\n\n')
    f.write('\\scalebox{0.55}{\n\n')
    layerList = np.arange(47) + 1
    headers = ['Wagon'] + [str(x) for x in layerList]
    table = []
    for code,indices in sorted(wagonCodesDict.items(),key=lambda x:(wagonNameDict[''.join([str(y) for y in x[0]])]),reverse=False):
      wagonName = wagonNameDict[''.join([str(x) for x in code])]
      layerCounts = [0] * len(layerList)
      for i,index in enumerate(indices): layerCounts[index[0] - 1] += 6
      table.append([wagonName] + [str(x) for x in layerCounts])
    f.write(tabulate(table,headers,tablefmt="latex_raw")) 
    f.write('\n}\n\n')
    f.write('\\end{landscape}\n\n')

    f.write('\n\\newpage\n')

    #------------------------------
    # Zippers by layer summary page
    #------------------------------
    if not os.path.exists('output/geometries/{}/geometry_simotherboards.hgcal.txt'.format(geomVersion)): 
      print('WARNING: You must re-run to get the zipper summary page in the LDWagonInfo.tex document!')
    else:
      geomFileData = pd.read_csv('output/geometries/{}/geometry_simotherboards.hgcal.txt'.format(geomVersion),sep=' ')
      zipperTable = geomFileData.set_index('plane')[['vx_4','vy_4','vx_5']].stack().reset_index(level=1,drop=True).reset_index(name='value')
      zipperTable = zipperTable[zipperTable['value'] != '-']
      zipperCountsByLayer = zipperTable.groupby(['value','plane']).size().unstack(fill_value=0).multiply(6)
      f.write('\\begin{landscape}\n\n')
      f.write('\\section{{Zippers Per Layer}}\n\n')
      f.write('\\scalebox{0.55}{\n\n')
      layerList = np.arange(47) + 1
      headers = ['Zipper'] + [str(x) for x in layerList]
      table = zipperCountsByLayer.reset_index().astype(str).to_numpy()
      f.write(tabulate(table,headers,tablefmt="latex_raw"))
      f.write('\n}\n\n')
      f.write('\\end{landscape}\n\n')

      f.write('\n\\newpage\n')

    #------------------------------
    # Parital/Zipper summary page
    #------------------------------
    f.write('\\section{{Total Partial and Zipper Counts}}\n\n')

    partialCounts = {}
    nPartialTotal = 0
    for name,indices in partialDict.items():
      for index,partialTypes in indices.items():
        for partialType,count in partialTypes.items():
          partialCounts[partialType] = partialCounts.get(partialType,0) + count * 6
          nPartialTotal += count * 6

    zipperCounts = {}
    nZipperTotal = 0
    for name,indices in zipperDict.items():
      for index,zipperTypes in indices.items():
        for zipperType,count in zipperTypes.items():
          zipperCounts[zipperType] = zipperCounts.get(zipperType,0) + count * 6
          nZipperTotal += count * 6

    f.write('\\begin{multicols}{2}\n\n')
    f.write('\\raggedcolumns\n')
    headers = ['Zipper Module Type','N Full Detector']
    table = []
    for partialType,count in partialCounts.items():
      table.append([partialType,count])
    table.append(['TOTAL',nPartialTotal])
    f.write(tabulate(table,headers,tablefmt="latex_raw"))
    f.write('\n\n')
    f.write('\\columnbreak\n')
    headers = ['Zipper Type','N Full Detector']
    table = []
    for zipperType,count in zipperCounts.items():
      table.append([zipperType,count])
    table.append(['TOTAL',nZipperTotal])
    f.write(tabulate(table,headers,tablefmt="latex_raw"))
    f.write('\n\n')
    
    f.write('\\end{multicols}\n\n')

    f.write('\\end{document}')
    f.close()

    with open('wagonInfo/wagonInfoHD.json','r') as fHDWagonInfo: 
      wagonInfoHD = json.load(fHDWagonInfo)
      for code in wagonCodesDict:
        wagonName = wagonNameDict[''.join([str(x) for x in code])]
        if 'WH' not in wagonName: continue
        infoTemp = {}
        for item in wagonInfoHD:
          if item['name'] == wagonName: infoTemp = item
        if not infoTemp: print('ERROR: {} does not exist in {}'.format(wagonName,'wagonInfo/wagonInfoHD.json'))
        trigString = ''
        for iTrig,modLinkList in enumerate(infoTemp['trigRouting']):
          for iTrigLink,modInfo in enumerate(modLinkList):
            if modInfo == '': continue
            trigString += '{}:T{}.{},'.format(modInfo,iTrig+1,iTrigLink)
        if trigString: trigString = trigString[:-1] # Remove last comma
        trigRoutingGeomDict[wagonName] = trigString
        DAQString = ''
        for iDAQ,modLinkList in enumerate(infoTemp['DAQRouting']):
          for iDAQLink,modInfo in enumerate(modLinkList):
            if modInfo == '': continue
            DAQString += '{}:D{}.{},'.format(modInfo,iDAQ+1,iDAQLink)
        if DAQString: DAQString = DAQString[:-1] # Remove last comma
        DAQRoutingGeomDict[wagonName] = DAQString
        xOverInRoutingGeomDict[wagonName] = '-'
        #print(wagonName)
        #print(trigString)
        #print(DAQString)

    #--------------------------------
    # Wagon link config json file
    #--------------------------------
    if not os.path.exists('output/wagonLinkConfig/{}'.format(geomVersion)): os.makedirs('output/wagonLinkConfig/{}'.format(geomVersion))
    f = open('output/wagonLinkConfig/{}/wagonConfig.json'.format(geomVersion),'w')
    json.dump(wagonLinkConfig,f,indent=4)
    f.close()

  # ----------------------------------------------
  # Output engine/wagon geometry file (by looping over wagons)
  # ----------------------------------------------
  if not os.path.exists('output/geometries/{}'.format(geomVersion)): os.makedirs('output/geometries/{}'.format(geomVersion))
  f = open('output/geometries/{}/geometry_simotherboards.hgcal.txt'.format(geomVersion),'w')

  f.write('plane u v itype typecode x0 y0 irot nvertices vx_0 vy_0 vx_1 vy_1 vx_2 vy_2 vx_3 vy_3 vx_4 vy_4 vx_5 vy_5 vx_6 vy_6 icassette trigRate trigLinks dataRate_ld dataLinks_ld dataRate_hd dataLinks_hd MB wagon isEngine nROCs power mrot phi HDorLD hash hash_hdld engine_trig_fibres engine_data_fibres engine_ctrl_fibres dataPp0 trigPp0 dataPp0_type trigPp0_type dataPp1 trigPp1 dataPp1_type trigPp1_type dataPp2 DAQ')

  # Construct wagonInfoLD and wagonInfoHD
  wagonInfoLD = []
  wagonInfoHD = []
  for code in wagonCodesDict:
    codeString = ''.join(str(x) for x in code)
    wagonName = wagonNameDict[codeString]
    if wagonName[1] == 'H': #HD
      # Trig
      trigStringTemp = trigRoutingGeomDict[wagonName]
      trigResultTemp = [['-' for _ in range(7)] for _ in range(max(int(pair.split(':')[1][1]) for pair in trigStringTemp.split(',') if pair.split(':')[1].startswith('T')))]
      pairs = trigStringTemp.split(',')
      for pair in pairs:
        MTemp,LTemp = pair.split(':')
        trigResultTemp[int(LTemp[1]) - 1][int(LTemp.split('.')[1])] = MTemp
      # DAQ
      DAQStringTemp = DAQRoutingGeomDict[wagonName]
      DAQResultTemp = [['-' for _ in range(7)] for _ in range(max(int(pair.split(':')[1][1]) for pair in DAQStringTemp.split(',') if pair.split(':')[1].startswith('D')))]
      pairs = DAQStringTemp.split(',')
      for pair in pairs:
        MTemp,LTemp = pair.split(':')
        DAQResultTemp[int(LTemp[1]) - 1][int(LTemp.split('.')[1])] = MTemp
      # Add to list
      wagonInfoHD.append({'name':wagonName,'code':codeString,'trigRouting':trigResultTemp,'DAQRouting':DAQResultTemp})
    else: # LD
      # Trig
      trigStringTemp = trigRoutingGeomDict[wagonName]
      trigResultTemp = [['-' for _ in range(7)]]
      xOverResultTemp = [['-' for _ in range(3)]]
      if trigStringTemp != '-': # Skip if wagon has no trigger links
        pairs = trigStringTemp.split(',')
        for pair in pairs:
          MTemp,LTemp = pair.split(':')
          if LTemp.startswith('T'): trigResultTemp[0][int(LTemp.split('.')[1])] = MTemp
          elif LTemp.startswith('X'): xOverResultTemp[0][int(LTemp.split('.')[1])] = MTemp
      # DAQ
      DAQStringTemp = DAQRoutingGeomDict[wagonName]
      DAQResultTemp = [['-' for _ in range(7)]]
      pairs = DAQStringTemp.split(',')
      for pair in pairs:
        MTemp,LTemp = pair.split(':')
        DAQResultTemp[0][int(LTemp.split('.')[1])] = MTemp
      # Xover
      xOverStringTemp = xOverInRoutingGeomDict[wagonName]
      if xOverStringTemp != '-':
        pairs = xOverStringTemp.split(',')
        for pair in pairs:
          MTemp,LTemp = pair.split(':')
          trigResultTemp[0][int(LTemp.split('.')[1])] = MTemp
      # Add to list
      wagonInfoLD.append({'name':wagonName,'code':codeString,'trigRouting':trigResultTemp,'DAQRouting':DAQResultTemp,'xoverRouting':xOverResultTemp})

  if not args.noTables:
    if not os.path.exists('output/wagonInfo/{}'.format(geomVersion)): os.makedirs('output/wagonInfo/{}'.format(geomVersion))
    fInfo = open('output/wagonInfo/{}/wagonInfoHD.tex'.format(geomVersion),'w')
    fInfo.write('\\begin{tabular}{|c|c|c|c|c|c|c|c|c|c|c|c|c|c|c|c|}')

  wagonNameStatus = {y:False for x,y in wagonNameDict.items()} # Track whether name has been used
  for tempCode,indices in wagonCodesDict.items():
    tempCodeString = ''.join(str(x) for x in tempCode)
    if tempCodeString in wagonNameDict: 
      wagonName = wagonNameDict[tempCodeString]
      wagonNameStatus[wagonName] = True 
    else: 
      print('ERROR: Wagon type code for {} not found'.format(tempCodeString))
      wagonName = 'XXXXXX'
    isHD = int(tempCodeString[0])
    nModules = int(wagonName[2]) + int(wagonName[3])
    for index in indices:

      tempIndex = index
      geomTempIndex = geomGrouped.get_group((tempIndex[0],tempIndex[1],tempIndex[2]))

      #-----------------------------------------
      # LD wagons
      #-----------------------------------------
      if not isHD:

        # Partner info
        tempPartnerIndex = [tempIndex[0],tempIndex[1],not tempIndex[2]]
        geomTempPartnerIndex = geomGrouped.get_group((tempIndex[0],tempIndex[1],not tempIndex[2]))
        for partnerCode,partnerIndices in wagonCodesDict.items():
          for partnerIndex in partnerIndices:
            if partnerIndex == tempPartnerIndex: 
              partnerCodeString = ''.join(str(x) for x in partnerCode)
              break
        if partnerCodeString in wagonNameDict: wagonPartnerName = wagonNameDict[partnerCodeString]
        else:
          print('ERROR: Wagon type code for {} not found'.format(partnerCodeString))
          wagonPartnerName = 'XXXXXX'

        # Wagon info
        plane,icassette,MB,wagon = geomTempIndex[['plane','icassette','MB','wagon']].iloc[0]
        if int(tempCodeString[1]): # West
          u,v,irot,x0,y0,trig0,daqLD0,daqHD0 = geomTempIndex[['u','v','irot','x0','y0','trigLinks','dataLinks_ld','dataLinks_hd']].loc[geomTempIndex['isEngine']].iloc[0]
          nDataTotal = 3
        else: # East
          uWest,vWest,irotWest = [int(x) for x in geomTempPartnerIndex[['u','v','irot']].loc[geomTempPartnerIndex['isEngine']].iloc[0]]
          u,v = findEastEngineModule(plane,uWest,vWest,irotWest)
          irot,x0,y0,trig0,daqLD0,daqHD0 = geomTempIndex[['irot','x0','y0','trigLinks','dataLinks_ld','dataLinks_hd']].loc[(geomTempIndex['u'] == u) & (geomTempIndex['v'] == v)].iloc[0]
          nDataTotal = 4

        #-----------------------------------------
        # Current wagon: matrices for active links
        #-----------------------------------------
        trigDim = 1 
        DAQDim = 1
        xoverDim = 1
        trigMat = np.empty((trigDim,7),dtype=object)
        DAQMat = np.empty((DAQDim,7),dtype=object)
        xoverMat = np.empty((xoverDim,3),dtype=object) # Outgoing xovers

        # Link routing for first module
        for index,x in enumerate(wagonInfoLD):
          if x['name'] == wagonName: iWagon = index
        for iTrig in range(int(trig0)):
          ilpGBT,iLink = np.where(np.array(wagonInfoLD[iWagon]['trigRouting']) == 'M{}.{}'.format(1,iTrig))
          if ilpGBT.size != 1 or iLink.size != 1:
            ilpGBT,iLink = np.where(np.array(wagonInfoLD[iWagon]['xoverRouting']) == 'M{}.{}'.format(1,iTrig))
            if ilpGBT.size != 1 or iLink.size != 1:
              print('ERROR: Module trigger link not found or duplicated in wagon routing. Wagon {}, layer {}, (u,v) = ({},{}), link {}'.format(wagonName,plane,u,v,'M{}.{}'.format(1,iTrig)))
            ilpGBT,iLink = ilpGBT[0],iLink[0]
            xoverMat[ilpGBT,iLink] = wagonInfoLD[iWagon]['xoverRouting'][ilpGBT][iLink]
          else:
            ilpGBT,iLink = ilpGBT[0],iLink[0]
            trigMat[ilpGBT,iLink] = wagonInfoLD[iWagon]['trigRouting'][ilpGBT][iLink]
        for iDAQ in range(int(daqLD0)):
          ilpGBT,iLink = np.where(np.array(wagonInfoLD[iWagon]['DAQRouting']) == 'M{}.{}'.format(1,iDAQ))
          if ilpGBT.size != 1 or iLink.size != 1:
            print('ERROR: Module DAQ link not found or duplicated in wagon routing. Wagon {}, layer {}, (u,v) = ({},{}), link {}'.format(wagonName,plane,u,v,'M{}.{}'.format(1,iDAQ)))
          ilpGBT,iLink = ilpGBT[0],iLink[0]
          DAQMat[ilpGBT,iLink] = wagonInfoLD[iWagon]['DAQRouting'][ilpGBT][iLink]

        # Info for first module
        u,v,irot = [int(x) for x in [u,v,irot]]
        uList = list('-'*4)
        vList = list('-'*4)
        irotList = list('-'*4)
        nActiveTrig = trig0
        nActiveData = daqLD0
        if int(tempCodeString[2]) == 0:
          uList[0],vList[0],irotList[0] = [u,v,irot]
        else:
          uPrev,vPrev,irotPrev = [u,v,irot]
          for i in reversed(range(int(tempCodeString[2]))):
            angleRev,orientRev = reverseAngleOrient(int(tempCodeString[5*i+7]),int(tempCodeString[5*i+8]))
            uPrev,vPrev,irotPrev = nextModule(plane,uPrev,vPrev,irotPrev,angleRev,orientRev)
          uList[0],vList[0],irotList[0] = [uPrev,vPrev,irotPrev]

        # Loop over all modules
        for i in range(len(tempCodeString)//5-1):
          uNext,vNext,irotNext = nextModule(plane,uList[i],vList[i],irotList[i],int(tempCodeString[5*i+7]),int(tempCodeString[5*i+8]))
          uList[i+1],vList[i+1],irotList[i+1] = uNext,vNext,irotNext
          trigTemp,daqLDTemp,daqHDTemp = geomTempIndex[['trigLinks','dataLinks_ld','dataLinks_hd']].loc[(geomTempIndex['u'] == uNext) & (geomTempIndex['v'] == vNext)].iloc[0]
          nActiveTrig += trigTemp
          nActiveData += daqLDTemp
          # Routing
          for index,x in enumerate(wagonInfoLD):
            if x['name'] == wagonName: iWagon = index
          for iTrig in range(int(trigTemp)):
            ilpGBT,iLink = np.where(np.array(wagonInfoLD[iWagon]['trigRouting']) == 'M{}.{}'.format(i+2,iTrig)) # Look in trigRouting
            if ilpGBT.size != 1 or iLink.size != 1:
              ilpGBT,iLink = np.where(np.array(wagonInfoLD[iWagon]['xoverRouting']) == 'M{}.{}'.format(i+2,iTrig)) # Looks in xoverRouting
              if ilpGBT.size != 1 or iLink.size != 1:
                print('ERROR: Module trigger link not found or duplicated in wagon routing. Wagon {}, layer {}, (u,v) = ({},{}), link {}'.format(wagonName,plane,u,v,'M{}.{}'.format(i+2,iTrig)))
              ilpGBT,iLink = ilpGBT[0],iLink[0]
              xoverMat[ilpGBT,iLink] = wagonInfoLD[iWagon]['xoverRouting'][ilpGBT][iLink] # Add it to outgoing xovers
            else:
              ilpGBT,iLink = ilpGBT[0],iLink[0]
              trigMat[ilpGBT,iLink] = wagonInfoLD[iWagon]['trigRouting'][ilpGBT][iLink]
          for iDAQ in range(int(daqLDTemp)):
            ilpGBT,iLink = np.where(np.array(wagonInfoLD[iWagon]['DAQRouting']) == 'M{}.{}'.format(i+2,iDAQ))
            if ilpGBT.size != 1 or iLink.size != 1:
              print('ERROR: Module DAQ link not found or duplicated in wagon routing. Wagon {}, layer {}, (u,v) = ({},{}), link {}'.format(wagonName,plane,u,v,'M{}.{}'.format(i+2,iDAQ)))
            ilpGBT,iLink = ilpGBT[0],iLink[0]
            DAQMat[ilpGBT,iLink] = wagonInfoLD[iWagon]['DAQRouting'][ilpGBT][iLink]
        
        xFX11,yFX11 = [61.2,23.0]
        x0FX11 = x0 + xFX11 * np.cos(np.pi/3*irot) + yFX11 * np.sin(np.pi/3*irot)
        y0FX11 = y0 + xFX11 * np.sin(np.pi/3*irot) - yFX11 * np.cos(np.pi/3*irot)
        nTrigTotal = int(tempCodeString[3]) + \
                     sum([int(tempCodeString[5*i+5],16) for i in range(len(tempCodeString)//5)]) + \
                     sum([int(tempCodeString[5*i+6],16) for i in range(len(tempCodeString)//5)])
        nTrigXOutTotal = sum([int(tempCodeString[5*i+6]) for i in range(len(tempCodeString)//5)])
        wagonRot = (irot + 3) % 6 if int(tempCodeString[1]) else irot
        if nActiveData > nDataTotal: print('WARNING: {} wagon (layer {}, MB {}) has >4 DAQ links, requiring the use of a xover, which is not expected!'.format('West' if int(tempCodeString[1]) else 'East',plane,MB))

        #-----------------------------------------
        # Partner wagon: matrices for active links
        #-----------------------------------------
        trigDim = 1 
        DAQDim = 1
        xoverDim = 1
        trigMatPartner = np.empty((trigDim,7),dtype=object)
        DAQMatPartner = np.empty((DAQDim,7),dtype=object)
        xoverMatPartner = np.empty((xoverDim,3),dtype=object)

        # Gather information about partner wagon for xover information
        if int(partnerCodeString[1]): # West
          uPartner,vPartner,irotPartner,trig0,daqLD0,daqHD0 = geomTempPartnerIndex[['u','v','irot','trigLinks','dataLinks_ld','dataLinks_hd']].loc[geomTempPartnerIndex['isEngine']].iloc[0]
          nDataTotalPartner = 3
        else: # East
          uWest,vWest,irotPartnerWest = [int(x) for x in geomTempIndex[['u','v','irot']].loc[geomTempIndex['isEngine']].iloc[0]]
          uPartner,vPartner = findEastEngineModule(plane,uWest,vWest,irotPartnerWest)
          irotPartner,trig0,daqLD0,daqHD0 = geomTempPartnerIndex[['irot','trigLinks','dataLinks_ld','dataLinks_hd']].loc[(geomTempPartnerIndex['u'] == uPartner) & (geomTempPartnerIndex['v'] == vPartner)].iloc[0]
          nDataTotalPartner = 4
        uPartner,vPartner,irotPartner = [int(x) for x in [uPartner,vPartner,irotPartner]]
        uListPartner = list('-'*4)
        vListPartner = list('-'*4)
        irotListPartner = list('-'*4)
        nActiveTrigPartner = trig0
        nActiveDataPartner = daqLD0
        if int(partnerCodeString[2]) == 0:
          uListPartner[0],vListPartner[0],irotListPartner[0] = [uPartner,vPartner,irotPartner]
        else:
          uPrev,vPrev,irotPrev = [uPartner,vPartner,irotPartner]
          for i in reversed(range(int(partnerCodeString[2]))):
            angleRev,orientRev = reverseAngleOrient(int(partnerCodeString[5*i+7]),int(partnerCodeString[5*i+8]))
            uPrev,vPrev,irotPrev = nextModule(plane,uPrev,vPrev,irotPrev,angleRev,orientRev)
          uListPartner[0],vListPartner[0],irotListPartner[0] = [uPrev,vPrev,irotPrev]

        # Link routing for first module
        for index,x in enumerate(wagonInfoLD):
          if x['name'] == wagonPartnerName: iWagon = index
        for iTrig in range(int(trig0)):
          ilpGBT,iLink = np.where(np.array(wagonInfoLD[iWagon]['trigRouting']) == 'M{}.{}'.format(1,iTrig))
          if ilpGBT.size != 1 or iLink.size != 1:
            ilpGBT,iLink = np.where(np.array(wagonInfoLD[iWagon]['xoverRouting']) == 'M{}.{}'.format(1,iTrig))
            if ilpGBT.size != 1 or iLink.size != 1:
              print('ERROR: Module trigger link not found or duplicated in wagon routing. Wagon {}, layer {}, (u,v) = ({},{}), link {}'.format(wagonName,plane,u,v,'M{}.{}'.format(1,iTrig)))
            ilpGBT,iLink = ilpGBT[0],iLink[0]
            xoverMatPartner[ilpGBT,iLink] = wagonInfoLD[iWagon]['xoverRouting'][ilpGBT][iLink]
          else:
            ilpGBT,iLink = ilpGBT[0],iLink[0]
            trigMatPartner[ilpGBT,iLink] = wagonInfoLD[iWagon]['trigRouting'][ilpGBT][iLink]
        for iDAQ in range(int(daqLD0)):
          ilpGBT,iLink = np.where(np.array(wagonInfoLD[iWagon]['DAQRouting']) == 'M{}.{}'.format(1,iDAQ))
          if ilpGBT.size != 1 or iLink.size != 1:
            print('ERROR: Module DAQ link not found or duplicated in wagon routing. Wagon {}, layer {}, (u,v) = ({},{}), link {}'.format(wagonName,plane,u,v,'M{}.{}'.format(1,iDAQ)))
          ilpGBT,iLink = ilpGBT[0],iLink[0]
          DAQMatPartner[ilpGBT,iLink] = wagonInfoLD[iWagon]['DAQRouting'][ilpGBT][iLink]

        # Loop over all modules
        for i in range(len(partnerCodeString)//5-1):
          uNext,vNext,irotNext = nextModule(plane,uListPartner[i],vListPartner[i],irotListPartner[i],int(partnerCodeString[5*i+7]),int(partnerCodeString[5*i+8]))
          uListPartner[i+1],vListPartner[i+1],irotListPartner[i+1] = uNext,vNext,irotNext
          trigTemp,daqLDTemp,daqHDTemp = geomTempPartnerIndex[['trigLinks','dataLinks_ld','dataLinks_hd']].loc[(geomTempPartnerIndex['u'] == uNext) & (geomTempPartnerIndex['v'] == vNext)].iloc[0]
          nActiveTrigPartner += trigTemp
          nActiveDataPartner += daqLDTemp
          # Routing
          for index,x in enumerate(wagonInfoLD):
            if x['name'] == wagonPartnerName: iWagon = index
          for iTrig in range(int(trigTemp)):
            ilpGBT,iLink = np.where(np.array(wagonInfoLD[iWagon]['trigRouting']) == 'M{}.{}'.format(i+2,iTrig)) # Look in trigRouting
            if ilpGBT.size != 1 or iLink.size != 1:
              ilpGBT,iLink = np.where(np.array(wagonInfoLD[iWagon]['xoverRouting']) == 'M{}.{}'.format(i+2,iTrig)) # Looks in xoverRouting
              if ilpGBT.size != 1 or iLink.size != 1:
                print('ERROR: Module trigger link not found or duplicated in wagon routing. Wagon {}, layer {}, (u,v) = ({},{}), link {}'.format(wagonName,plane,u,v,'M{}.{}'.format(i+2,iTrig)))
              ilpGBT,iLink = ilpGBT[0],iLink[0]
              xoverMatPartner[ilpGBT,iLink] = wagonInfoLD[iWagon]['xoverRouting'][ilpGBT][iLink] # Add it to outgoing xovers
            else:
              ilpGBT,iLink = ilpGBT[0],iLink[0]
              trigMatPartner[ilpGBT,iLink] = wagonInfoLD[iWagon]['trigRouting'][ilpGBT][iLink]
          for iDAQ in range(int(daqLDTemp)):
            ilpGBT,iLink = np.where(np.array(wagonInfoLD[iWagon]['DAQRouting']) == 'M{}.{}'.format(i+2,iDAQ))
            if ilpGBT.size != 1 or iLink.size != 1:
              print('ERROR: Module DAQ link not found or duplicated in wagon routing. Wagon {}, layer {}, (u,v) = ({},{}), link {}'.format(wagonName,plane,u,v,'M{}.{}'.format(i+2,iDAQ)))
            ilpGBT,iLink = ilpGBT[0],iLink[0]
            DAQMatPartner[ilpGBT,iLink] = wagonInfoLD[iWagon]['DAQRouting'][ilpGBT][iLink]

        for index,x in enumerate(wagonInfoLD):
          if x['name'] == wagonPartnerName: iWagon = index
        ixoverIns = np.where(np.array([x[0] for x in wagonInfoLD[iWagon]['trigRouting'][0]]) == 'X')[0]
        for ixoverIn in ixoverIns:
          ixoverOut = int(wagonInfoLD[iWagon]['trigRouting'][0][ixoverIn][-1])
          for index,x in enumerate(wagonInfoLD):
            if x['name'] == wagonName: iWagonPartner = index # The partner of the partner is the original!
          # Find MX.Y of outgoing xover on partner wagon if it is sent
          xoverOutLink = wagonInfoLD[iWagonPartner]['xoverRouting'][0][ixoverOut]
          if xoverOutLink != '-':
            iMod,iLink = [int(x) for x in xoverOutLink[1:].split('.')]
            # Look at that module and see how many trig links are active
            uTemp = uList[iMod - 1]
            vTemp = vList[iMod - 1]
            trigTemp = int(geomTempIndex[['trigLinks']].loc[(geomTempIndex['u'] == uTemp) & (geomTempIndex['v'] == vTemp)].iloc[0])
            # If it's >=Y, the xover is active, so add it to trigMat
            if trigTemp >= (iLink + 1): trigMatPartner[0][ixoverIn] = wagonInfoLD[iWagon]['trigRouting'][0][ixoverIn]

        #-----------------------------------------
        # Calculate global wagon info
        #-----------------------------------------
        nModulesPartner = int((len(partnerCodeString)-2)/5)
        nTrigTotalPartner = int(partnerCodeString[3]) + \
                     sum([int(partnerCodeString[5*i+5],16) for i in range(len(partnerCodeString)//5)]) + \
                     sum([int(partnerCodeString[5*i+6],16) for i in range(len(partnerCodeString)//5)])
        nTrigXOutTotalPartner = sum([int(partnerCodeString[5*i+6]) for i in range(len(partnerCodeString)//5)])
        nActiveTrigEngine = nActiveTrig + nActiveTrigPartner
        nActiveDataEngine = nActiveData + nActiveDataPartner
      
        for index,x in enumerate(wagonInfoLD):
          if x['name'] == wagonName: iWagon = index
        ixoverIns = np.where(np.array([x[0] for x in wagonInfoLD[iWagon]['trigRouting'][0]]) == 'X')[0]
        for ixoverIn in ixoverIns:
          ixoverOut = int(wagonInfoLD[iWagon]['trigRouting'][0][ixoverIn][-1])
          for index,x in enumerate(wagonInfoLD):
            if x['name'] == wagonPartnerName: iWagonPartner = index
          # Find MX.Y of outgoing xover on partner wagon if it is sent
          xoverOutLink = wagonInfoLD[iWagonPartner]['xoverRouting'][0][ixoverOut]
          if xoverOutLink != '-':
            iMod,iLink = [int(x) for x in xoverOutLink[1:].split('.')]
            # Look at that module and see how many trig links are active
            uTemp = uListPartner[iMod - 1]
            vTemp = vListPartner[iMod - 1]
            trigTemp = int(geomTempPartnerIndex[['trigLinks']].loc[(geomTempPartnerIndex['u'] == uTemp) & (geomTempPartnerIndex['v'] == vTemp)].iloc[0])
            # If it's >=Y, the xover is active, so add it to trigMat
            if trigTemp >= (iLink + 1): trigMat[0][ixoverIn] = wagonInfoLD[iWagon]['trigRouting'][0][ixoverIn]

        # Test printouts
        #if plane == 3 and MB == 5: print('-----\n',wagonName,'( partner: ',wagonPartnerName,')',plane,u,v,'\n-----\n',trigMat,'\n',DAQMat,'\n',xoverMat)
        #if plane == 3 and MB == 5: print('-----\n',wagonPartnerName,'\n-----\n',trigMatPartner,'\n',DAQMatPartner,'\n',xoverMatPartner)

      #-----------------------------------------
      # HD wagons
      #-----------------------------------------
      else: # HD wagons

        plane,icassette,MB,wagon,u,v,irot,x0,y0,trig0,daqLD0,daqHD0 = geomTempIndex[['plane','icassette','MB','wagon','u','v','irot','x0','y0','trigLinks','dataLinks_ld','dataLinks_hd']].loc[geomTempIndex['isEngine']].iloc[0]
        uLD,vLD,temp = nextModule(plane,u,v,irot,angle=3,orient=0)
        x0LD,y0LD,irotLD = geomBasic[(geomBasic['plane'] == plane) & (geomBasic['u'] == uLD) & (geomBasic['v'] == vLD)][['x0','y0','irot']].iloc[0]
        plane,icassette,MB,wagon,u,v,irot,trig0,daqLD0,daqHD0 = [int(x) for x in [plane,icassette,MB,wagon,u,v,irot,trig0,daqLD0,daqHD0]]

        if irot == irotLD: engineType = 'EH10H0'
        elif (irot+3)%6 == irotLD: engineType = 'EH10F0'
        else: print('ERROR: Unexpected relative rotations between HD and LD modules for HD engine (plane = {}, u = {}, v = {})'.format(plane,u,v))

        # Matrices for link routing
        if engineType == 'EH10F0':
          trigDim = 4
          DAQDim = 2
        elif engineType == 'EH10H0':
          trigDim = 2
          DAQDim = 1
        else: print('ERROR: Unexpected HD engine type when formatting link routing for HD engine (plane = {}, u = {}, v = {})'.format(plane,u,v))
        trigMat = np.empty((trigDim,7),dtype=object)
        DAQMat = np.empty((DAQDim,7),dtype=object)

        # Account for index changes
        newIndices = list(range(nModules)) if wagonName not in indexChanges else indexChanges[wagonName]

        # Link routing for first module
        for index,x in enumerate(wagonInfoHD):
          if x['name'] == wagonName: iWagon = index
        for iTrig in range(int(trig0)):
          ilpGBT,iLink = np.where(np.array(wagonInfoHD[iWagon]['trigRouting']) == 'M{}.{}'.format(newIndices[0]+1,iTrig))
          if ilpGBT.size != 1 or iLink.size != 1:
            print('ERROR: Module trigger link not found or duplicated in wagon routing. Wagon {}, layer {}, (u,v) = ({},{}), link {}'.format(wagonName,plane,u,v,'M{}.{}'.format(newIndices[0]+1,iTrig)))
          ilpGBT,iLink = ilpGBT[0],iLink[0]
          trigMat[ilpGBT,iLink] = wagonInfoHD[iWagon]['trigRouting'][ilpGBT][iLink]
        for iDAQ in range(int(daqHD0)):
          ilpGBT,iLink = np.where(np.array(wagonInfoHD[iWagon]['DAQRouting']) == 'M{}.{}'.format(newIndices[0]+1,iDAQ))
          if ilpGBT.size != 1 or iLink.size != 1:
            print('ERROR: Module DAQ link not found or duplicated in wagon routing. Wagon {}, layer {}, (u,v) = ({},{}), link {}'.format(wagonName,plane,u,v,'M{}.{}'.format(newIndices[0]+1,iDAQ)))
          ilpGBT,iLink = ilpGBT[0],iLink[0]
          DAQMat[ilpGBT,iLink] = wagonInfoHD[iWagon]['DAQRouting'][ilpGBT][iLink]

        nDataTotal = 7 if engineType == 'EH10H0' else 14
        uList = list('-'*4)
        vList = list('-'*4)
        irotList = list('-'*4)
        nActiveTrig = trig0
        nActiveData = daqHD0
        if int(tempCodeString[2]) == 0:
          uList[0],vList[0],irotList[0] = [u,v,irot]
        else:
          uPrev,vPrev,irotPrev = [u,v,irot]
          for i in reversed(range(int(tempCodeString[2]))):
            angleRev,orientRev = reverseAngleOrient(int(tempCodeString[5*i+7]),int(tempCodeString[5*i+8]))
            uPrev,vPrev,irotPrev = nextModule(plane,uPrev,vPrev,irotPrev,angleRev,orientRev)
          uList[newIndices[0]],vList[newIndices[0]],irotList[newIndices[0]] = [uPrev,vPrev,irotPrev]
        for i in range(len(tempCodeString)//5-1):
          uNext,vNext,irotNext = nextModule(plane,uList[newIndices[i]],vList[newIndices[i]],irotList[newIndices[i]],int(tempCodeString[5*i+7]),int(tempCodeString[5*i+8]))
          uList[newIndices[i+1]],vList[newIndices[i+1]],irotList[newIndices[i+1]] = uNext,vNext,irotNext
          trigTemp,daqLDTemp,daqHDTemp = geomTempIndex[['trigLinks','dataLinks_ld','dataLinks_hd']].loc[(geomTempIndex['u'] == uNext) & (geomTempIndex['v'] == vNext)].iloc[0]
          nActiveTrig += trigTemp
          nActiveData += daqHDTemp
          for index,x in enumerate(wagonInfoHD):
            if x['name'] == wagonName: iWagon = index
          for iTrig in range(int(trigTemp)):
            ilpGBT,iLink = np.where(np.array(wagonInfoHD[iWagon]['trigRouting']) == 'M{}.{}'.format(newIndices[i+1]+1,iTrig))
            if ilpGBT.size != 1 or iLink.size != 1:
              print('ERROR: Module trigger link not found or duplicated in wagon routing. Wagon {}, layer {}, (u,v) = ({},{}), link {}'.format(wagonName,plane,u,v,'M{}.{}'.format(newIndices[i+1]+1,iTrig)))
            ilpGBT,iLink = ilpGBT[0],iLink[0]
            trigMat[ilpGBT,iLink] = wagonInfoHD[iWagon]['trigRouting'][ilpGBT][iLink]
          for iDAQ in range(int(daqHDTemp)):
            ilpGBT,iLink = np.where(np.array(wagonInfoHD[iWagon]['DAQRouting']) == 'M{}.{}'.format(newIndices[i+1]+1,iDAQ))
            if ilpGBT.size != 1 or iLink.size != 1:
              print('ERROR: Module DAQ link not found or duplicated in wagon routing. Wagon {}, layer {}, (u,v) = ({},{}), link {}'.format(wagonName,plane,u,v,'M{}.{}'.format(newIndices[i+1]+1,iDAQ)))
            ilpGBT,iLink = ilpGBT[0],iLink[0]
            DAQMat[ilpGBT,iLink] = wagonInfoHD[iWagon]['DAQRouting'][ilpGBT][iLink]        
        nTrigTotal = int(tempCodeString[3]) + \
                     sum([int(tempCodeString[5*i+5],16) for i in range(len(tempCodeString)//5)]) + \
                     sum([int(tempCodeString[5*i+6],16) for i in range(len(tempCodeString)//5)])
        nTrigXOutTotal = sum([int(tempCodeString[5*i+6]) for i in range(len(tempCodeString)//5)])
        nTrigXInTotal = int(tempCodeString[3])
        if nTrigXInTotal != 0: print('ERROR: HD wagon somehow has incoming trigger links!!!')
        wagonRot = irot
        if nActiveData > nDataTotal and nActiveTrig != 0: print('WARNING: {} wagon (layer {}, MB {}) has too many DAQ links, {} counted, but only {} supported!'.format('West' if int(tempCodeString[1]) else 'East',plane,MB,nActiveData,nDataTotal))
        if tempCodeString in wagonNameDict: 
          wagonName = wagonNameDict[tempCodeString]
          wagonNameStatus[wagonName] = True
        else: 
          print('ERROR: Wagon type code for {} not found'.format(tempCodeString))
          wagonName = 'XXXXXX'
        nModules = int(wagonName[2]) + int(wagonName[3])
        nActiveTrigEngine = nActiveTrig
        nActiveDataEngine = nActiveData

      # Convert link routings to strings
      trigMatString = ''
      for ilpGBT in range(len(trigMat)):
        for iLink in range(len(trigMat[ilpGBT])):
          if trigMat[ilpGBT][iLink]:
            if isHD: lpGBTLabel = ilpGBT + 1
            elif wagonName[1] == 'E': lpGBTLabel = 'E'
            else: lpGBTLabel = 'W'
            trigMatString += 'T{}.{}:{},'.format(lpGBTLabel,iLink,trigMat[ilpGBT][iLink])
      if trigMatString == '': trigMatString = '-'
      if trigMatString[-1] == ',': trigMatString = trigMatString[:-1]

      DAQMatString = ''
      for ilpGBT in range(len(DAQMat)):
        for iLink in range(len(DAQMat[ilpGBT])):
          if DAQMat[ilpGBT][iLink]:
            DAQMatString += 'D{}.{}:{},'.format(ilpGBT+1,iLink,DAQMat[ilpGBT][iLink])
      if DAQMatString == '': DAQMatString = '-'
      if DAQMatString[-1] == ',': DAQMatString = DAQMatString[:-1]

      if isHD: xOverOutMatString = '-'
      else: 
        #for iLink in range(len(xOverOutMat)):
        #  xOverOutMatString = 'X.{}-{}'.format(iLink,xOverOutMat[iLink])
        xOverOutMatString = '-'

      # Convert to int
      nActiveTrig,nActiveData,nActiveTrigEngine,nActiveDataEngine = [int(x) for x in [nActiveTrig,nActiveData,nActiveTrigEngine,nActiveDataEngine]]    

      zipperTypes = list('-' * 4)
      if wagonName in zipperDict:
        for i in [0,1,2,3]:
          zipperTypes[i] = zipperDictLocs.get(tuple(tempIndex + [i]),'-')
        if zipperTypes[0] != '-': print('ERROR: Zipper for first module is not possible')

      # Append appropriate HD wagon suffix
      if not isHD:                        wagonNamePrint = wagonName
      elif plane <= 26 and not plane % 2: wagonNamePrint = wagonName[:-1] + 'D'
      else:                               wagonNamePrint = wagonName[:-1] + 'T'

      #-----------------------------------------
      # Write wagon info
      #-----------------------------------------
      f.write('\n{}'.format(' '.join(str(x) for x in [	plane,u,v,wagonNamePrint,wagonNamePrint,round(x0FX11,3) if not isHD else '-',				# 1-6
							round(y0FX11,3) if not isHD else '-',irot,nModules,uList[0],vList[0],				# 7-11
							uList[1],vList[1],uList[2],vList[2],uList[3],							# 12-16
							vList[3],zipperTypes[1],zipperTypes[2],zipperTypes[3],'-',					# 17-21
							'-','-',icassette,nTrigTotal,int(nActiveTrig),							# 22-26
							nDataTotal,int(nActiveData),int(tempCodeString[3]),nTrigXOutTotal,MB,				# 27-31
							wagon,0,0,'-',wagonRot,										# 32-36
							'-',isHD,'-','-',trigRoutingGeomDict[wagonName],				# 37-41
							DAQRoutingGeomDict[wagonName],tempCodeString,xOverInRoutingGeomDict[wagonName],trigMatString,DAQMatString,		# 42-46
							'-','-','-','-','-',										# 47-51
							'-','-'])))											# 52-53

      #-----------------------------------------
      # Engines
      #-----------------------------------------
      if (geomTempIndex['isEngine'] == True).any():

        plane,u,v,irot,icassette,x0,y0,isHD = geomTempIndex[geomTempIndex['isEngine'] == True][['plane','u','v','irot','icassette','x0','y0','HDorLD']].iloc[0]
        plane,u,v,irot,icassette,isHD = [int(x) for x in [plane,u,v,irot,icassette,isHD]]

        #-----------------------------------------
        # LD engines
        #-----------------------------------------
        if not isHD: # LD engines

          uEast,vEast = findEastEngineModule(plane,u,v,irot)
          x0East,y0East = geomBasic[(geomBasic['plane'] == plane) & (geomBasic['u'] == uEast) & (geomBasic['v'] == vEast)][['x0','y0']].iloc[0]
          uCenter = (u+uEast)/2
          vCenter = (v+vEast)/2
          x0Center = (x0+x0East)/2
          y0Center = (y0+y0East)/2
          nTrigTotal = 14
          nDataTotal = 7
          nTriglpGBT = '-'
          nVTRx = 1
          nDAQlpGBT = 1 if nActiveData > 0 else 0
          if irot == 0: engineType = 'EL10E0' if x0 > 0 else 'EL10W0'
          elif irot == 1 or irot == 2: engineType = 'EL10E0'
          elif irot == 3: engineType = 'EL10W0' if x0 > 0 else 'EL10E0'
          elif irot == 4 or irot ==  5: engineType = 'EL10W0'
          else: print('ERROR: Invalid irot for engine {}'.format(i))


        #-----------------------------------------
        # HD engines
        #-----------------------------------------          
        else: # HD engines

          nXWtoE = 0

          uLD,vLD,temp = nextModule(plane,u,v,irot,angle=3,orient=0)
          x0LD,y0LD,irotLD = geomBasic[(geomBasic['plane'] == plane) & (geomBasic['u'] == uLD) & (geomBasic['v'] == vLD)][['x0','y0','irot']].iloc[0]
          uCenter = (u+uLD)/2
          vCenter = (v+vLD)/2
          x0Center = (x0+x0LD)/2
          y0Center = (y0+y0LD)/2
          if irot == irotLD: 
            engineType = 'EH10H0'
            nTrigTotal = 14
            nDataTotal = 7
            nVTRx = 1
          elif (irot+3)%6 == irotLD: 
            engineType = 'EH10F0'
            nTrigTotal = 28
            nDataTotal = 14
            nVTRx = 0
            if sum([np.all(trigMat[i] == None) for i in [0,1]]) + sum([np.all(DAQMat[i] == None) for i in [0]]) != 3: nVTRx += 1
            else: print('ERROR: Somehow VTRx+ 1 is empty!')
            if sum([np.all(trigMat[i] == None) for i in [2,3]]) + sum([np.all(DAQMat[i] == None) for i in [1]]) != 3: nVTRx += 1
          else: print('ERROR: Unexpected relative rotations between HD and LD modules for HD engine (plane = {}, u = {}, v = {})'.format(plane,u,v))

          nTriglpGBT,nDAQlpGBT = [0,0]
          for i in range(trigMat.shape[0]):
            if not np.all(trigMat[i] == None): nTriglpGBT += 1
          for i in range(DAQMat.shape[0]):
            if not np.all(DAQMat[i] == None): nDAQlpGBT += 1

        nCtrlFibers = int(geomTempIndex[['engine_ctrl_fibres']].iloc[0])

        # Format active link mapping
        # Trig links for current wagon
        trigMatEngineString = ''
        for ilpGBT in range(len(trigMat)):
          for iLink in range(len(trigMat[ilpGBT])):
            if trigMat[ilpGBT][iLink] and 'X' not in trigMat[ilpGBT][iLink]:
              if isHD:                  
                lpGBTLabel = ilpGBT + 1
                modLabel = ''
              elif wagonName[1] == 'E': 
                lpGBTLabel = 'E'
                modLabel = 'E'
              else:                    
                lpGBTLabel = 'W'
                modLabel = 'W'
              trigMatEngineString += 'T{}.{}:{},'.format(lpGBTLabel,iLink,trigMat[ilpGBT][iLink].replace('M','{}M'.format(modLabel)))
        # Add any xovers
        if not isHD:
          # Outgoing xovers (read out by the opposite side)
          for iLink,link in enumerate(xoverMat[0]):
            if link:
              if wagonName[1] == 'E': 
                lpGBTLabel = 'W'
                modLabel = 'E'
              else:                   
                lpGBTLabel = 'E'
                modLabel = 'W'
              trigMatEngineString += 'T{}.{}:{},'.format(lpGBTLabel,iLink,link.replace('M','{}M'.format(modLabel)))
          # Trig links for partner wagon (LD only)
          for ilpGBT in range(len(trigMatPartner)):
            for iLink in range(len(trigMatPartner[ilpGBT])):
              if trigMatPartner[ilpGBT][iLink] and 'X' not in trigMatPartner[ilpGBT][iLink]:
                if wagonPartnerName[1] == 'E': 
                  lpGBTLabel = 'E'
                  modLabel = 'E'
                else:                    
                  lpGBTLabel = 'W'
                  modLabel = 'W'
                trigMatEngineString += 'T{}.{}:{},'.format(lpGBTLabel,iLink,trigMatPartner[ilpGBT][iLink].replace('M','{}M'.format(modLabel)))
        if trigMatEngineString == '': trigMatEngineString = '-'
        if trigMatEngineString[-1] == ',': trigMatEngineString = trigMatEngineString[:-1]
            
        #DAQ links for current wagon
        DAQMatEngineString = ''
        for ilpGBT in range(len(DAQMat)):
          for iLink in range(len(DAQMat[ilpGBT])):
            if DAQMat[ilpGBT][iLink]:
              if isHD:                  
                lpGBTLabel = ilpGBT + 1
                modLabel = ''
              elif wagonName[1] == 'E': 
                lpGBTLabel = ''
                modLabel = 'E'
              else:                    
                lpGBTLabel = ''
                modLabel = 'W'
              DAQMatEngineString += 'D{}.{}:{},'.format(lpGBTLabel,iLink,DAQMat[ilpGBT][iLink].replace('M','{}M'.format(modLabel)))
        # DAQ links for partner wagon (LD only)
        if not isHD:
          for ilpGBT in range(len(DAQMatPartner)):
            for iLink in range(len(DAQMatPartner[ilpGBT])):
              if DAQMatPartner[ilpGBT][iLink]:
                if wagonPartnerName[1] == 'E': 
                  lpGBTLabel = ''
                  modLabel = 'E'
                else:                    
                  lpGBTLabel = ''
                  modLabel = 'W'
                DAQMatEngineString += 'D{}.{}:{},'.format(lpGBTLabel,iLink,DAQMatPartner[ilpGBT][iLink].replace('M','{}M'.format(modLabel)))
        if DAQMatEngineString == '': DAQMatEngineString = '-'
        if DAQMatEngineString[-1] == ',': DAQMatEngineString = DAQMatEngineString[:-1]

        #-----------------------------------------
        # Write engine info
        #-----------------------------------------
        f.write('\n{}'.format(' '.join(str(x) for x in [plane,round(uCenter,1),round(vCenter,1),engineType,engineType,round(x0Center,3),	# 1-6
            						round(y0Center,3),irot,engineType[-2],u if isHD else uEast,v if isHD else vEast,	# 7-11
            						uLD if isHD else u,vLD if isHD else v,'-','-','-',					# 12-16
            						'-','-','-','-','-',									# 17-21
            						'-','-',icassette,nTrigTotal,nActiveTrigEngine,						# 22-26
            						nDataTotal,nActiveDataEngine,'-','-',MB,						# 27-31
            						'-',1,'-','-','-',									# 32-36
            						'-',isHD,'-','-',nTriglpGBT,								# 37-41
            						nDAQlpGBT,nCtrlFibers,nVTRx,trigMatEngineString,DAQMatEngineString,							# 42-46
            						'-','-','-','-','-',									# 47-51
            						'-','-'])))										# 52-53

    # Write tables
    if not args.noTables: fInfo.write('\\n{}\\\\'.format('&'.join([	wagonName,'-',
						'-','-','-',
                                                '-','-','-',
                                                '-','-','-',
                                                '-','-','-',
						tempCodeString,'-'])))
      
    # Delete variables to avoid accidental re-use on next iteration
    try: del trigMat,DAQMat
    except UnboundLocalError: pass

  f.close()
  if not args.noTables:
    fInfo.write('\\end{tabular}')
    fInfo.close()

  # Print warning if there's an unexpected unused wagon name
  knownMerged = ['WE31A2','WW12B1','WE12B1','WE21C2','WW21E4','WE21C5','WE11B1','WW11B1','WW10B1']
  for key,val in wagonNameStatus.items():
    if not val and key not in knownMerged: print('WARNING: Unused wagon name ({})'.format(key))

  # ----------------------------------------------
  # Print out counts
  # ----------------------------------------------
  #print(codeCounter)
  uniqueWagonCodes = [list(i) for i in set(tuple(i) for i in list(codeCounter.keys()))]
  uniqueWagonCodesHD = [i for i in uniqueWagonCodes if i[0] == 1]
  uniqueWagonCodesLD = [i for i in uniqueWagonCodes if i[0] == 0]
  print('Number of HD wagon types:',len(uniqueWagonCodesHD))
  #print(uniqueWagonCodesHD)
  print('Number of LD wagon types:',len(uniqueWagonCodesLD))
  #print(uniqueWagonCodesLD)

  # Save dictionary to file
  if not args.noWagonDict:
    with open('wagonDict/wagonDict_{}.txt'.format(geometryFile),'w') as f:
      print(wagonCodesDict,file=f)

  # Print LD wagons and zippers by locations
  #geomFileData = pd.read_csv('output/geometries/{}/geometry_simotherboards.hgcal.txt'.format(geomVersion),sep=' ')
  #geomFileDataGrouped = geomFileData.groupby(['plane','MB','wagon'])
  #print('Zipper counts (full detector):')
  #print(pd.concat([geomFileData['vx_4'],geomFileData['vy_4'],geomFileData['vx_5']],axis=0,ignore_index=True).value_counts().drop('-') * 6)
  #LDWagonDictSection = {}
  #zipperDictSection = {}
  #for code,indices in wagonCodesDict.items():
  #  wagonName = wagonNameDict[''.join([str(x) for x in code])]
  #  if code[0] != 0: continue
  #  if wagonName not in LDWagonDictSection: LDWagonDictSection[wagonName] = {'CE-E':0,'CE-H':0,'Preseries':0,'Preproduction':0,'Total':0}
  #  for layer,MB,wagon in indices:
  #    # Zippers
  #    z2,z3,z4 = geomFileDataGrouped.get_group((layer,MB,str(wagon)))[['vx_4','vy_4','vx_5']].iloc[0]
  #    z2 = None if z2 == '-' else z2
  #    z3 = None if z3 == '-' else z3
  #    z4 = None if z4 == '-' else z4
  #    if layer < 27: 
  #      LDWagonDictSection[wagonName]['CE-E'] += 1
  #      for z in [z2,z3,z4]:
  #        if z:
  #          if z not in zipperDictSection: zipperDictSection[z] = {'CE-E':1,'CE-H':0,'Preseries':0,'Preproduction':0,'Total':1}
  #          else: 
  #            zipperDictSection[z]['CE-E'] += 1
  #            zipperDictSection[z]['Total'] += 1
  #    else:
  #      LDWagonDictSection[wagonName]['CE-H'] += 1
  #      for z in [z2,z3,z4]:
  #        if z:
  #          if z not in zipperDictSection: zipperDictSection[z] = {'CE-E':0,'CE-H':1,'Preseries':0,'Preproduction':0,'Total':1}
  #          else:
  #            zipperDictSection[z]['CE-H'] += 1
  #            zipperDictSection[z]['Total'] += 1
  #    if layer in [25,26,44,45,46,47]: 
  #      LDWagonDictSection[wagonName]['Preproduction'] += 1
  #      for z in [z2,z3,z4]:
  #        if z:
  #          zipperDictSection[z]['Preproduction'] += 1
  #    if layer in [25,26,33,44,45,46,47] : 
  #      LDWagonDictSection[wagonName]['Preseries'] += 1
  #      for z in [z2,z3,z4]:
  #        if z:
  #          zipperDictSection[z]['Preseries'] += 1
  #    LDWagonDictSection[wagonName]['Total'] += 1
  #    
  #for name,sectionCounts in LDWagonDictSection.items():
  #  #if sectionCounts['CE-E'] == 0: print(name,'is only in CE-H')
  #  nCEE,nCEH,nPreseries,nPreproduction,n = np.array([sectionCounts['CE-E'],sectionCounts['CE-H'],sectionCounts['Preseries'],sectionCounts['Preproduction'],sectionCounts['Total']]) * 6
  #  print('{},{},{},{},{},{}'.format(name,nCEE,nCEH,nPreseries,nPreproduction,n))
  #for name,sectionCounts in zipperDictSection.items():
  #  nCEE,nCEH,nPreseries,nPreproduction,n = np.array([sectionCounts['CE-E'],sectionCounts['CE-H'],sectionCounts['Preseries'],sectionCounts['Preproduction'],sectionCounts['Total']]) * 6
  #  print('{},{},{},{},{},{}'.format(name,nCEE,nCEH,nPreseries,nPreproduction,n))

  # Count certain wagons
  #extraFibers = {}
  #for code,indices in wagonCodesDict.items():
  #  for index in indices:
  #    wagonName = wagonNameDict[''.join([str(x) for x in code])]
  #    if wagonName[0:2] == 'WH' or wagonName[2:4] not in ['31','40']: continue
  #    layer = index[0]
  #    icassette = geomGrouped.get_group(tuple(index))['icassette'].iloc[0]
  #    extraFibers[(layer,icassette,'DAQ')] = extraFibers.get((layer,icassette,'DAQ'),0) + 1
  #    extraFibers[(layer,icassette,'Trig')] = extraFibers.get((layer,icassette,'Trig'),0) + 1
  #extraFibersList = sorted([list(loc) + [count] for loc,count in extraFibers.items()])
  #layerCurr,cassetteCurr = extraFibersList[0][0],extraFibersList[0][1]
  #for i,item in enumerate(extraFibersList):
  #  layer,cassette,linkType,count = item
  #  if i == 0 or layer != layerCurr: 
  #    print('----------Layer {}----------'.format(layer))
  #    print('Cassette {}:'.format(cassette))
  #  elif cassette != cassetteCurr:
  #    print('Cassette {}:'.format(cassette))
  #  print('  {}: +{}'.format(linkType,count * 6))
  #  layerCurr,cassetteCurr = [layer,cassette]

  # Print wagon info
  #wagonCodesDict = dict(sorted(wagonCodesDict.items(),key=lambda x:(x[0][0],len(x[0]),len(x[1])),reverse=True))
  #with open('wagonInfo/wagonInfo_{}.txt'.format(geomVersion),'w') as f:
  #  for code,locs in wagonCodesDict.items():
  #    if len(locs) > 10: continue
  #    print('-'*20,''.join([str(x) for x in code]),'-'*20,file=f)
  #    print('No. of instances:',len(locs),file=f)
  #    print('Locations:',sorted(locs,key=lambda x:x[0]),file=f)
  #    partnerCodes = []
  #    for loc in locs:
  #      index = 99999
  #      for i,val in enumerate(wagonCodesDict.values()):
  #        if [loc[0],loc[1],int(not loc[2])] in val:
  #          index = i
  #      partnerCodes.append(''.join(str(i) for i in list(wagonCodesDict.keys())[index]))
  #    print('Partner codes and counts:',Counter(partnerCodes),file=f)
  #    print('-'*(40+len(''.join([str(x) for x in code]))),'\n',file=f)

  # Print max DAQ links
  #maxDAQLinks = {x:maxLinksCalculation(x,'B','dataLinks_ld',wagonCodesDict,geomGrouped,recodedCodesList) for x in wagonCodesDict}
  #for key,val in maxDAQLinks.items():
  #  keyString = ''.join([str(x) for x in key])
  #  if not keyString[0] == '0': continue
  #  print('{}: {} {}'.format(keyString,maxLinks[key],val))

  # Select only varieties with <= 10 instances
  #for key,val in list(wagonCodesDict.items()):
  #  if len(val) > 10: del wagonCodesDict[key]
  #codeCounter = Counter({tuple(key):len(val) for key,val in wagonCodesDict.items()})
  # maxLinks = {x:maxLinksCalculation(x,'B','trigLinks'wagonCodesDict,geomGrouped,recodedCodesList) for x in wagonCodesDict}

  # Select only wagons in certain layers/cassettes
  #wagonCodesSubDict = copy.deepcopy(wagonCodesDict)
  #for key,vals in wagonCodesDict.items():
  #  for val in vals:
  #    geomTemp = geomGrouped.get_group(tuple(val))
  #    if not (geomTemp['plane'].iloc[0] in [25,26] and geomTemp['icassette'].iloc[0] == 1) and \
  #       not (geomTemp['plane'].iloc[0] in [33]    and geomTemp['icassette'].iloc[0] in [1,2]) and \
  #       not (geomTemp['plane'].iloc[0] in [44]    and geomTemp['icassette'].iloc[0] in [3,4]): 
  #      wagonCodesSubDict[key].remove(val)
  #  wagonCodesSubDict[wagonNameDict[''.join(str(x) for x in key)]] = wagonCodesSubDict.pop(key)
  #wagonCodesSubDict = {key:val for key,val in wagonCodesSubDict.items() if len(val)}
  #codeCounterSubDict = dict(sorted(Counter({key:len(val) for key,val in wagonCodesSubDict.items()}).items(),key=lambda item: item[1],reverse=True))
  #print('-'*20)
  #print('{:<10}{:<10}'.format('Type','N'))
  #print('-'*20)
  #for key,val in codeCounterSubDict.items():
  #  print('{:<10}{:<10}'.format(key,val))

  # Sort by HD/LD then no. of modules then no. of instances 
  codeCounter = dict(sorted(codeCounter.items(), key=lambda item: (item[0][0],len(item[0]),item[1]), reverse=True))

  # Count no. of LD wagons with partials
  #NNoPart = 0
  #NPart = 0
  #for code,N in codeCounter.items():
  #  c = ''.join([str(x) for x in code])
  #  if c[0] != '0': continue
  #  if c[3] == '0': NNoPart += N
  #  else: NPart += N
  #print('Wagons with no partials:',NNoPart)
  #print('Wagons with partials:',NPart)

  #xoverOutWagons = {}
  #xoverInWagons = {}
  #for code,N in codeCounter.items():
  #  c = ''.join([str(x) for x in code])
  #  if int(c[3]) > 0: xoverInWagons['{} ({})'.format(wagonNameDict[c],c)] = N
  #  else:
  #    nX = sum([int(x) for x in c[6::5]])
  #    if nX > 0: xoverOutWagons['{} ({})'.format(wagonNameDict[c],c)] = N
  #print('LD wagons with incoming crossover links:')
  #for name,N in xoverInWagons.items():
  #  print(name.split('(')[0])
  #print('LD wagons with outgoing crossover links:')
  #for name,N in xoverOutWagons.items():
  #  print(name.split('(')[0])

  # Print out quantities
  #with open('output/wagonCounts/wagonCounts_{}.txt'.format(geomVersion),'w') as f:
  #  for key, item in codeCounter.items():
  #    f.write('{}:\t{}\n'.format(wagonNameDict[''.join(str(x) for x in key)],item))

  # Draw and save the wagon summary (see wagonDrawer.py)
  if not args.noImages: wagonDrawer.wagonDrawer(codeCounter,geomVersion,maxLinks,maxDAQLinks,wagonNameDict,indexChanges)

if __name__ == '__main__':
  main()
