import pandas as pd
import numpy as np
from collections import Counter
import itertools
import wagonDrawer
import sys
import time
import copy
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

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

  #print(group)
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

##################################################
# MAIN
##################################################
def main():

  # Configuration parameters
  threesSeparate = False
  halvesSemisSame = False
  LDOnly = True

  # Specify the geometry file to be used
  geometryPath = 'geometries/v13.2/'
  geometryFile = 'geometry.hgcal'

  # Extract required columns
  geom = pd.read_csv('{0}{1}.txt'.format(geometryPath,geometryFile),delim_whitespace=True)
  geomBasic = geom[['plane','u','v','x0','y0','itype','irot','MB','wagon','isEngine','HDorLD','trigLinks','dataLinks_ld','dataLinks_hd']].copy()
  if not threesSeparate: geomBasic = geomBasic[~geomBasic['itype'].str.contains('c')] # Threes don't affect wagon shape
  geomBasic['itype'] = geomBasic['itype'].str[0]
  geomBasic['r'] = np.sqrt(geomBasic['x0']**2 + geomBasic['y0']**2)
  if halvesSemisSame: 
    #geomBasic.loc[geomBasic['itype'] == 'd','irot'] += 1
    geomBasic.loc[geomBasic['itype'] == 'd','itype'] = 'a'

  #  Specify the file with the fiber counts
  fiberCountsFile = 'fiberCounts/fiberCounts_220221_163022.txt'
  fiberCounts = pd.read_csv(fiberCountsFile,delim_whitespace=True,dtype={'TlpGBT':'Int64'})
  geomBasic = pd.merge(geomBasic, fiberCounts,  how='left', on=['plane','MB'])

  # Get a subset (if needed)
  #geomBasic = geomBasic[(geomBasic['plane'] <= 28) | (geomBasic['plane'] >= 37)]
  if LDOnly: geomBasic = geomBasic[geomBasic['HDorLD'] == 0]
  #geomBasic = geomBasic[(geomBasic['plane'] == 33) & (geomBasic['HDorLD'] == 0)]

  # Remove impossible wagons
  removeWagons = [[3,2,0],[3,102,0],[5,2,0],[5,102,0],[3,0,0],[3,100,0],[5,0,0],[5,100,0]]
  for w in removeWagons:
    geomBasic = geomBasic.drop(geomBasic[(geomBasic['plane'] == w[0]) & (geomBasic['MB'] == w[1]) & (geomBasic['wagon'] == w[2])].index)

  # Group modules by plane (layer), MB index, and wagon index
  geomGrouped = geomBasic.sort_values('r',ascending=True).groupby(['plane','MB','wagon'])

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

      irotCurr = row['irot']
      uCurr    = row['u']
      vCurr    = row['v']
 
      if i != 0:
        
        # Angle code
        deltaU = uCurr - uPrev
        deltaV = vCurr - vPrev

        if deltaU == 1 and deltaV == 0:
          angle = 0
        elif deltaU == 1 and deltaV == 1:
          angle = 1
        elif deltaU == 0 and deltaV == 1:
          angle = 2
        elif deltaU == -1 and deltaV == 0:
          angle = 3
        elif deltaU == -1 and deltaV == -1:
          angle = 4
        elif deltaU == 0 and deltaV == -1:
          angle = 5
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
 
  # Consolidating using Incoming Crossover Links
  wagonCodesDictCopy = copy.deepcopy(wagonCodesDict)
  incomingWagonCodesDict = {x:wagonCodesDictCopy[x] for x in wagonCodesDictCopy.keys() if x[2] <= 0}
  incomingWagonCodesCopy = copy.deepcopy(incomingWagonCodesDict)
  removedWagonsList = []
  for code, vals in incomingWagonCodesCopy.items():
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
          incomingWagonCodesDict[code].remove(loc)
          incomingWagonCodesDict[possibleCode].append(loc)
          codeCounter[code] -= 1
          codeCounter[possibleCode] += 1
          if codeCounter[code] == 0:
            removedWagonsList.append(code)
          break

  for key, val in incomingWagonCodesDict.items():
    wagonCodesDictCopy[key] = val
  
  wagonCodesDict = copy.deepcopy(wagonCodesDictCopy)

  # Consolidating using outgoing crossover links, taking into account wagon partners
  outgoingWagonCodesDict = {x:wagonCodesDictCopy[x] for x in wagonCodesDictCopy.keys() if x[2] >= 0}
  outgoingWagonCodesCopy = copy.deepcopy(outgoingWagonCodesDict)
  for key, val in outgoingWagonCodesCopy.items():
    for loc in val:
      wagonLoc = geomGrouped.get_group((loc[0], loc[1], loc[2]))
      wagonPartnerLoc = geomGrouped.get_group((loc[0], loc[1], int(not loc[2])))
      numLinks = sum([int(x) for x in wagonLoc['trigLinks'].tolist()])
      numOutgoingLinks = key[2]
      numPartnerLinks = sum([int(x) for x in wagonPartnerLoc['trigLinks'].tolist()])
      numAvailablePartnerLinks = 7 - numPartnerLinks
      acceptableRange = list(range(numAvailablePartnerLinks + 1, 0, -1))
      if key[2] == acceptableRange[0]:
        continue 
      for num in acceptableRange:
        possibleCode = list(key)
        possibleCode = possibleCode[:2] + [num] + possibleCode[3:]
        possibleCode = tuple(possibleCode)
        if possibleCode not in outgoingWagonCodesCopy:
          continue
        outgoingWagonCodesDict[key].remove(loc)
        outgoingWagonCodesDict[possibleCode].append(loc)
        codeCounter[key] -= 1
        codeCounter[possibleCode] += 1
        if codeCounter[key] == 0:
          removedWagonsList.append(key)
        break
        
  for key, val in outgoingWagonCodesDict.items():
    wagonCodesDictCopy[key] = val

  wagonCodesDict = copy.deepcopy(wagonCodesDictCopy)
  wagonCodesDict = {x:y for x, y in wagonCodesDict.items() if len(y) > 0}
 
  # Finding max. links on each module on each wagon type
  maxLinks = {x:[] for x in wagonCodesDict.keys()}
  for code, vals in wagonCodesDict.items():
    lenWagon = len(list(code[3::3]))
    maxLinksList = []
    for i in range(lenWagon):
      maxLinksList.append(0)
    for loc in vals:
      wagonLoc = geomGrouped.get_group((loc[0], loc[1], loc[2]))
      numTrigLinks = [int(x) for x in wagonLoc['trigLinks'].tolist()]
      for j in range(len(maxLinksList)):
        if numTrigLinks[j] > maxLinksList[j]:
          maxLinksList[j] = numTrigLinks[j]
    maxLinks[code] = maxLinksList

  # print(maxLinks)

  emptyCounter = Counter([tuple(i) for i in removedWagonsList])
  for wagon in removedWagonsList:
    emptyCounter[wagon] = 0
  
  geometryFile2 = 'removedWagons'
  with open('wagonDict/{}.txt'.format(geometryFile2), 'w') as f:
    print(removedWagonsList, file = f) 

  wagonDrawer.wagonDrawer(emptyCounter, geometryFile2)

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

  # Save dictionary to file
  with open('wagonDict/wagonDict_{}.txt'.format(geometryFile),'w') as f:
    print(wagonCodesDict,file=f)

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

  #print(codeCounter)
  uniqueWagonCodes = [list(i) for i in set(tuple(i) for i in list(codeCounter.keys()))]
  uniqueWagonCodesHD = [i for i in uniqueWagonCodes if i[0] == 1]
  uniqueWagonCodesLD = [i for i in uniqueWagonCodes if i[0] == 0]
  print('Number of HD wagon types:',len(uniqueWagonCodesHD))
  #print(uniqueWagonCodesHD)
  print('Number of LD wagon types:',len(uniqueWagonCodesLD))
  #print(uniqueWagonCodesLD)

  # Sort by HD/LD then no. of modules then no. of instances 
  codeCounter = dict(sorted(codeCounter.items(), key=lambda item: (item[0][0],len(item[0]),item[1]), reverse=True))

  # Draw and save the wagon summary (see wagonDrawer.py)
  wagonDrawer.wagonDrawer(codeCounter, geometryFile, maxLinks)

if __name__ == '__main__':
  main()
