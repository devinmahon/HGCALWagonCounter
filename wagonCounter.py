import pandas as pd
import numpy as np
from collections import Counter
import itertools
import wagonDrawer
import sys
import time
import matplotlib.pyplot as plt

def checkContiguity(group):

  group = group[['u','v']].diff()
  group['diff'] = list(zip(group.u,group.v))
  group['touchPrev'] = group['diff'].apply(lambda x: True if x in [(1,0),(1,1),(0,1),(-1,0),(-1,-1),(0,-1)] else False)
  group.loc[group.index[0],'touchPrev'] = True

  if group['touchPrev'].all():
    return True, -1
  else:
    return False, group.index.get_loc(group[group.touchPrev == False].iloc[0].name) # Index of first non-touching module

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

def all_pairs(lst):
  if len(lst) < 2:
    yield []
    return
  if len(lst) % 2 == 1:
    # Handle odd length list
    for i in range(len(lst)):
      for result in all_pairs(lst[:i] + lst[i+1:]):
         yield result
  else:
    a = lst[0]
    for i in range(1,len(lst)):
      pair = (a,lst[i])
      for rest in all_pairs(lst[1:i]+lst[i+1:]):
        yield [pair] + rest

def main():

  geometryPath = '/Users/devinmahon/Documents/CMS/hgcal_modmap/maps/'
  geometryFile = '220120_104521_fullGeom'
  #geometryPath = '/Users/devinmahon/Documents/CMS/hgcal_modmap/geometries/v13.2/'
  #geometryFile = 'geometry.hgcal'

  # Extract required columns
  #geom = pd.read_csv('geometries/v11.6/geometry.hgcal.txt',delim_whitespace=True)
  #geom = pd.read_csv('/Users/devinmahon/Documents/CMS/hgcal_modmap/maps/210927_151335_fullGeom_v2.txt',delim_whitespace=True)
  geom = pd.read_csv('{0}{1}.txt'.format(geometryPath,geometryFile),delim_whitespace=True)
  geomBasic = geom[['plane','u','v','x0','y0','itype','irot','MB','wagon','isEngine','HDorLD','trigLinks','dataLinks_ld','dataLinks_hd']]
  geomBasic = geomBasic[~geomBasic['itype'].str.contains('c')] # Threes don't affect wagon shape
  geomBasic['itype'] = geomBasic['itype'].str[0]
  geomBasic['r'] = np.sqrt(geomBasic['x0']**2 + geomBasic['y0']**2)

  fiberCountsFile = '/Users/devinmahon/Documents/CMS/hgcal_modmap/maps/fiberCounts_220221_163022.txt'
  fiberCounts = pd.read_csv(fiberCountsFile,delim_whitespace=True,dtype={'TlpGBT':'Int64'})
  geomBasic = pd.merge(geomBasic, fiberCounts,  how='left', on=['plane','MB'])
  #geomBasic = geomBasic[geomBasic['plane'] == 1]
  #print(geomBasic[['plane','u','v','MB','TlpGBT']][0:50])
  #sys.exit()

  # Get a subset
  #geomBasic = geomBasic[(geomBasic['plane'] <= 28) | (geomBasic['plane'] >= 37)]
  geomBasic = geomBasic[geomBasic['HDorLD'] == 1]

  # Consolidate partials
  #geomBasic.loc[geomBasic['itype'] == 'b','itype'] = 'F'

  geomGrouped = geomBasic.sort_values('r',ascending=True).groupby(['plane','MB','wagon'])

  wagonCodes = []
  wagonCodesDict = {}
  for name, group in geomGrouped:

    newCode = []
    #print(name)

    # Ensure that ordering of modules is contiguous
    #if name != (1,109,1):
    #  continue
    group = makeContiguous(group)    

    #if name in [(35,9,0),(35,9,1),(36,2,0),(36,2,1),(37,10,0),(37,10,1)]: print(group)

    #nModules = group.shape[0]
    #nomSequence = list(range(nModules - 1) + np.ones(nModules - 1,dtype=int))
    #orderings = list(itertools.permutations(nomSequence))
    #orderings = orderings[1:] # First one is the nominal ordering
    #groupTemp = group.copy()
    #for ordering in orderings:
    #  isContiguous, badIndex = checkContiguity(groupTemp)
    #  if isContiguous:
    #    break
    #  else:
    #    groupTemp.iloc[nomSequence] = group.iloc[list(ordering)]
    #group = groupTemp.copy()
    ##print(checkContiguity(group))
    ##print(checkContiguity(group)[0])
    #if not checkContiguity(group)[0]:
    #  print('ERROR: Could not make wagon contiguous')

    # Add code for HD/LD
    if group['HDorLD'].astype(bool).all():
      newCode.append(1)
    elif (~group['HDorLD'].astype(bool)).all():
      newCode.append(0)
    else:
      print('ERROR: Train contains both HD and LD modules. MB:',group.loc[0,'MB'])

    # Add code for isEngine (direction)
    #newCode.append(1) if (group['isEngine'] == True).any() else newCode.append(0)
    try: enginePos = list(group['isEngine'] == True).index(True)
    except ValueError: enginePos = -1
    newCode.append(enginePos)   

    # Add placeholder code for crossover trigger links
    newCode.append(0)
    #totTrigLinks = sum([int(x) for x in group['trigLinks'].tolist()])
    #if newCode[0] == 0 and totTrigLinks > 7:
    #  x1 = totTrigLinks - 7
    #  x2 = -x1
    #  
    #  wagonTempPartner = geomBasic[(geomBasic['plane'] == group['plane'].iloc[0]) & (geomBasic['MB'] == group['MB'].iloc[0]) & (geomBasic['wagon'] == int(not group['wagon'].iloc[0])) ]
 
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
        #orientCode = -1 if not 'F' in row['itype'] else (irotCurr - irotPrev) % 6 # Orientation of non-full modules contains no information since modules can only attach to neighbors in one way based on angle
        newCode.append(orientCode)

      newCode.append(row['itype'])
      
      irotPrev = irotCurr
      uPrev    = uCurr
      vPrev    = vCurr
      i += 1
   
    #print(group)
    #print(newCode)
    # If the first module is non-full, orientation wrt second module contains no information
    #if len(newCode) > 3 and newCode[2] != 'F': newCode[4] = -1

    #if newCode == [0,-1,'F',1,0,'d',5,1,'b']:
    #  print(group)    
    
    wagonCodes.append(newCode)
    wagonCodesDict.setdefault(tuple(newCode),[]).append([row['plane'],row['MB'],row['wagon']])

  # Get all unique wagons
  codeCounter = Counter([tuple(i) for i in wagonCodes])
  #print(dict(codeCounter))
  #print('-------')
  # Consolidate 180 degree rotations
  duplicateCodes = []
  for wagon in list(codeCounter.keys()):
    if len(wagon) == 4:
      continue
    #print('original:',wagon)
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
      codeCounter[wagon] += codeCounter[wagonRot]
      duplicateCodes.append(wagon)
      codeCounter.pop(wagonRot,None)

      wagonCodesDict[wagon] = wagonCodesDict[wagon] + wagonCodesDict[wagonRot]
      wagonCodesDict.pop(wagonRot)

  numTrigLinksHDLT15 = 0
  numHD = 0
  wagonCodesDictCopy = wagonCodesDict.copy()
  for key, value in wagonCodesDictCopy.items():
    maxTrigLinks = []
    numDataLinksHDGT7 = 0
    #print(key)
    for id in value:
      #if id == [3,2,0] or id == [3,102,0] or id == [5,2,0] or id == [5,102,0] or id == [3,0,0] or id == [3,100,0] or id == [5,0,0] or id == [5,100,0]: continue
      wagonTemp = geomBasic[(geomBasic['plane'] == id[0]) & (geomBasic['MB'] == id[1]) & (geomBasic['wagon'] == id[2])]#.sort_values('r',ascending=True)
      #print(wagonTemp)
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
        wagonTempPartner = geomBasic[(geomBasic['plane'] == id[0]) & (geomBasic['MB'] == id[1]) & (geomBasic['wagon'] == int(not id[2]))]
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
            wagonCodesDict[newCode2] = wagonCodesDict[newCode2] + [id]
          else:
            codeCounter[newCode2] = 1
            wagonCodesDict[newCode2] = [id]

      # Trigger links
      if not len(maxTrigLinks): maxTrigLinks = numTrigLinks
      else: 
        maxTrigLinks = np.maximum(maxTrigLinks,numTrigLinks)
      # Check number of links on individual MBs
      #if key == (1, 2, 0, 'g', 3, 3, 'F', 0, 0, 'F'):
      #  if sum(numTrigLinks) >= 24: print(id,numTrigLinks)
      #if key == (1, 3, 0, 'd', 4, 4, 'F', 0, 0, 'F', 0, 0, 'F'):
      #  if sum(numTrigLinks) > 28: print(id,numTrigLinks)
      #if sum(numTrigLinks) > 28: print(id,numTrigLinks)
        #if numTrigLinks[0] > 6:
        #  print(id,numTrigLinks)
        #if numTrigLinks[1] > 3:
        #  print(id,numTrigLinks)
    #print(maxTrigLinks)
    # Print messages about link distribution on LD wagons
    #if key[0] == 0 and sum(maxTrigLinks) > 7: print('Wagon',key,'has maxTrigLinks with total > 7. maxTrigLinks = ',maxTrigLinks)
    # Print messages about HD links
    #if key[0] == 1: print('Wagon',key,'has maxTrigLinks = ',maxTrigLinks)
    # Print message about how many HD wagons has more than 7 DAQ links
    #if key[0] == 1: print(numDataLinksHDGT7,'/',len(value),'('+'{:.1f}'.format(100 * numDataLinksHDGT7 / len(value)),'%) HD wagons with code',key,'have more than 7 DAQ links')

  #print(numTrigLinksHDLT15,'out of',numHD,'(','{:.1f}'.format(numTrigLinksHDLT15 * 100.0 / numHD),'%) HD wagons have <= 14 trigger links')

  # Remove empty Counter entries
  codeCounter = Counter({i:j for i,j in codeCounter.items() if j != 0})

  # Save dictionary to file
  with open('wagonDict/wagonDict_{}.txt'.format(geometryFile),'w') as f:
    print(wagonCodesDict,file=f)

  # Count no. of TlpGBTs required per variety
  lpGBTCounts = {} 
  for key, value in wagonCodesDict.items():
    if key[0] != 1: continue
    lpGBTCounts[key] = []
    for id in value:
      numlpGBT = geomBasic[(geomBasic['plane'] == id[0]) & (geomBasic['MB'] == id[1]) & (geomBasic['wagon'] == id[2])]['TlpGBT'].iloc[0]
      if not pd.isna(numlpGBT) and numlpGBT != 0: lpGBTCounts[key].append(numlpGBT)
  for key,value in lpGBTCounts.items():
    plt.hist(value,bins=[1,2,3,4,5])
    plt.xlabel('No. of Required Trigger lpGBTs')
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

  # Sort by HD/LD then number of wagons
  #codeCounter = dict(sorted(codeCounter.items(), key=lambda item: (item[0][0],item[1]), reverse=True))
  # Sort by
  codeCounter = dict(sorted(codeCounter.items(), key=lambda item: (item[0][0],len(item[0]),item[1]), reverse=True))

  wagonDrawer.wagonDrawer(codeCounter,geometryFile)
  #wagonDrawer.wagonDrawer(dict(sorted(codeCounter.items(), key=lambda item: item[1],reverse=True)),geometryFile)

if __name__ == '__main__':
  main()
