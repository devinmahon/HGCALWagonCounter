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

##################################################
# MAIN
##################################################
def main():

  # Specify the geometry file to be used
  geomVersion = 'v15.3_NadjaOct2023'
  geometryPath = 'geometries/{}/'.format(geomVersion)
  geometryFile = 'geometry.hgcal'

  # Extract required columns
  geom = pd.read_csv('{0}{1}.txt'.format(geometryPath,geometryFile),delim_whitespace=True)
  geom = geom[['plane','u','v', 'itype','dataPp0','trigPp0','HDorLD']]

  # LD only
  geom = geom[geom['HDorLD'] == 0]

  # Count module types
  typeCounter = Counter(geom['itype'])
  typeCounter = dict(sorted(typeCounter.items()))
  print('-'*20)
  print('{:<10}{:<10}'.format('Type','N'))
  print('-'*20)
  for key,item in typeCounter.items():
    print('{:<10}{:<10}'.format(key,item))

  # Get unique dataPp0 and trigPp0 per layer
  if False:
    planesList = set(geom['plane'])
    #print('Layer','\t\t','N(unique dataPp0)','\t\t','N(unique trigPp0)')
    print('{:<20}{:<20}{:<20}'.format('Layer','N(unique dataPp0)','N(unique trigPp0)'))
    totalUniquesData = 0
    totalUniquesTrig = 0
    for i in planesList:

      uniquesData = set(geom[(geom['plane'] == i) & (geom['dataPp0'] != 'None')]['dataPp0'])
      nUniquesData = len(uniquesData)
      totalUniquesData += nUniquesData

      uniquesTrig = set(geom[(geom['plane'] == i) & (geom['trigPp0'] != 'None')]['trigPp0'])
      nUniquesTrig = len(uniquesTrig)
      totalUniquesTrig += nUniquesTrig

      #print(i,'\t\t',nUniquesData,'\t\t',nUniquesTrig)
      print('{:<20}{:<20}{:<20}'.format(i,nUniquesData,nUniquesTrig))

      #border = '#'*20 + ' Layer ' + str(i) + ' ' + '#'*20
      #print(border)
      #for key,item in dataCounter.items():
      #  print(key,':\t',item)
      #print('#'*len(border))
    #print('TOTAL','\t\t',totalUniquesData,'\t\t',totalUniquesTrig)
    print('{:<20}{:<20}{:<20}'.format('TOTAL',totalUniquesData,totalUniquesTrig))

if __name__ == '__main__':
  main()
