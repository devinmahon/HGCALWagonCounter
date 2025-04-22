import ast
import glob
import os
from sys import argv
from collections import Counter

wagonNameDict = {
  # HD
  '1000F5000F7000Fb0'         : 'WH30A1',
  '1000F4000F5000F50'         : 'WH30B1',
  '1000F6000F7040F60'         : 'WH30C1',
  '1000F4000F5040F50'         : 'WH30D1',
  '1000F5000F7000F9005d70'    : 'WH31A1',
  '1000F5000F5000a4040F50'    : 'WH31B1',
  '1000F5000F50'              : 'WH20A1',
  '1000F6000F9000g80'         : 'WH21A1',
  # LD
  '0000F1100F2000F2000F20'    : 'WE40A1',
  '0000F2000F2000F2005d11'    : 'WE31A1',
  '0030d1152F2030F2030F20'    : 'WE31A2',
  '0030F2030F2022F1124F20'    : 'WE40A2',
  '0000F2014F2012F2015d11'    : 'WE31A3',
  '0101F2030F2030F20'         : 'WW30A1', # W3A
  '0100F3030F2031d20'         : 'WW21A1',
  '0001F2000F2005d20'         : 'WE21A1',
  '0000F2000F2000F20'         : 'WE30A1', # E3A
  '0001F3000F2005d10'         : 'WE21B1',
  '0000F3015d2000d20'         : 'WE12A1',
  '0100F3121d2030d20'         : 'WW12A1',
  '0010F2030F2022F20'         : 'WE30A2',
  '0100F2014F2030F20'         : 'WW30B1', # Lefty python
  '0000F2014F2012F20'         : 'WE30A3', # East T
  '0101F2030F2031d20'         : 'WW21B1',
  '0000F2015d2001F20'         : 'WE21C1',
  '0100F2022F2024F20'         : 'WW30B2', # West T
  '0111F2000F2014F20'         : 'WW30A2',
  '0100F3014F2031d20'         : 'WW21C1',
  '0000F0022F0005d00'         : 'WE21D1',
  '0100F2020d2041d20'         : 'WW12B1',
  '0000F2010d2055d20'         : 'WE12B1',
  '0101F3030F2031d10'         : 'WW21D1',
  '0110d2044F2014F20'         : 'WW21E1',
  '0000F2010d2050F20'         : 'WE21C2',
  '0100F2020d2040F20'         : 'WW21E2',
  '0110F2000F2010d20'         : 'WW21E3',
  '0100F2030F2032d20'         : 'WW21E4',
  '0010F2030F2021d20'         : 'WE21C3',
  '0000F2014F2011d20'         : 'WE21C4',
  '0101F2010d2031d20'         : 'WW12C1',
  '0020d2052F2030F20'         : 'WE21C5',
  '0010d2052F2022F20'         : 'WE21C6',
  '0100F3130F41'              : 'WW20A1', # W2A
  '0000F3100F41'              : 'WE20A1', # E2A
  '0100F4031d20'              : 'WW11A1', # Used to be '0101F4031d20' before v16.3
  '0001F4005d20'              : 'WE11A1',
  '0001F3000F30'              : 'WE20B1', # E2B
  '0102F3030F20'              : 'WW20B1',
  '0100F4014F30'              : 'WW20C1',
  '0010d2052F20'              : 'WE11B1',
  '0101F3030F30'              : 'WW20D1',
  '0000F4021d20'              : 'WE11C1',
  '0100F2032d20'              : 'WW11B1', # Used to be '0101F2032d20' before v16.3
  '0000F2015d20'              : 'WE11B2',
  '0002F3000F20'              : 'WE20E1',
  '0101F50'                   : 'WW10A1', # W1A
  '0001F50'                   : 'WE10A1', # E1A
  '0000F03'                   : 'WE10B1',
  '0103F30'                   : 'WW10B1',
}

def findCode(wagonDict,loc):

  for i,val in enumerate(wagonDict.values()):
    if loc in val:
      index = i

  return ''.join(str(i) for i in list(wagonDict.keys())[index])

def main():

  # Find the most recent file
  filesList = glob.glob('wagonDict/*txt')
  latestFile = max(filesList,key=os.path.getctime)
  print('Reading from most recent wagon dictionary file:',latestFile)
  with open(latestFile) as f:
    wagonDict = f.read()
  wagonDict = ast.literal_eval(wagonDict)

  if ',' in argv[1]: 

    arg = [int(i) for i in argv[1].split(',')] + [0]
    argPartner = [arg[0],arg[1],1]

    print(arg,'is a',wagonNameDict[''.join([str(x) for x in findCode(wagonDict,arg)])],'(',findCode(wagonDict,arg),')')
    print(argPartner,'is a',wagonNameDict[''.join([str(x) for x in findCode(wagonDict,argPartner)])],'(',findCode(wagonDict,argPartner),')')

  else: 

    if argv[1][0] == 'W':
      for key,item in wagonNameDict.items():
        if item == argv[1]:
          arg = tuple([int(i) if i.isdigit() else i for i in list(key)])
          break
      try: arg
      except UnboundLocalError: 
        print('ERROR: Wagon type {} not found'.format(argv[1]))
        quit()
    else: arg = tuple([int(i) if i.isdigit() else i for i in list(argv[1])])

    isDash = 0
    code = []
    for i,x in enumerate(arg):
      if x == '-':
        isDash = 1
        continue
      if isDash:
        code.append(-1 * x)
        isDash = 0
      elif len(code) and isinstance(code[-1],str) and code[-1].isalpha() and isinstance(x,int) and not isinstance(code[-2],str):
        code.append(str(x))
      else:
        code.append(x)
    code = tuple(code)

    print('Wagon locations:')
    print('[layer,MB,wagon]:',sorted(wagonDict[code],key = lambda x: x[0]))

    # Print partners for LD
    if code[0] == 0:

      partnerCodes = []
      for loc in wagonDict[code]:
        partnerCodes.append(wagonNameDict[''.join([str(x) for x in findCode(wagonDict,[loc[0],loc[1],int(not loc[2])])])])

      print('Partner codes and counts:')
      print(Counter(partnerCodes))

if __name__ == '__main__':
  main()
