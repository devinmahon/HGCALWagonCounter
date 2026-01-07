import pandas as pd
import numpy as np

version = 'v16.6'

fECON 	= f'output/geometriesECOND/{version}/geometryECOND.txt'
fTID 	= f'data/hirschauer_tid_map_fixed.csv'
fModmap	= f'../hgcal_modmap/geometries/{version}/geometry_sipmontile.hgcal.txt'

modmap 	= pd.read_csv(fModmap,sep=' ')
econ	= pd.read_csv(fECON,sep=' ')
tid	= pd.read_csv(fTID,sep=',')

# Reformat tid
cols = tid.columns.drop('type (from HGCAL geom)')
tid[cols] = tid[cols].apply(pd.to_numeric, errors='coerce')

# HD
#modmap 	= modmap[(modmap['typecode'].str[0] == 'M') & (modmap['HDorLD'] == 1)]
#tid 	= tid[tid['HDorLD (HD=1)'] == 1]
econHD = econ[econ['typecode'].str[0:2] == 'WH']

# LD
econLD = econ[econ['typecode'].str[0:2] != 'WH']

# Get rid of tile modules
modmap = modmap[(modmap['typecode'].str[0] == 'M')]

# Convert to Mrad
tid['fluence [Gray]'] = tid['fluence [Gray]'] / 10**4

# Rename columns
tid = tid.rename(columns={'layer':'plane','fluence [Gray]':'fluence [Mrad]'})

# Minimum radii per wagon per module index across all instances
#print(econ.groupby(['typecode','modIndex'])['r'].min())

econHD = pd.merge(econHD,tid,on=['plane','u','v'],how='inner')
econLD = pd.merge(econLD,tid,on=['plane','u','v'],how='inner')

# Maximum fluence per wagon per module index across all instances
#print(econ.groupby(['typecode','modIndex'])['fluence [Mrad]'].max())

#----------
# HD
#----------
# Compute fluence bin
fluenceRangesHD = 	[
			(econHD['fluence [Mrad]'] >= 0) & (econHD['fluence [Mrad]'] < 10),
                        (econHD['fluence [Mrad]'] >= 10) & (econHD['fluence [Mrad]'] < 50),
                        (econHD['fluence [Mrad]'] >= 50) & (econHD['fluence [Mrad]'] < 100),
                        (econHD['fluence [Mrad]'] >= 100) & (econHD['fluence [Mrad]'] < 140),
			]
fluenceBinsHD = ['D','C','B','A']
econHD['fluence bin'] = np.select(fluenceRangesHD,fluenceBinsHD,default='N/A')

#table = econHD.groupby(['typecode','modIndex'])['fluence bin'].value_counts().to_latex()
#print(table)

econHD['grades'] = econHD.sort_values('modIndex').groupby(['plane','MB','wagon'])['fluence bin'].transform(lambda x: ''.join(x))
econHD['fluences'] = econHD.sort_values('modIndex').groupby(['plane','MB','wagon'])['fluence [Mrad]'].transform(lambda x: ' '.join(f'{v:.3f}' for v in (list(x) + [-1] * (4 - len(x)))[:4]))

f = open(f'output/geometriesECOND/{version}/HDWagonECONDGradesHist.txt','w')
# Counts of grades by wagon type
for name,group in econHD.groupby(['typecode']):
  f.write('-'*10 + '\n')
  f.write(name + '\n')
  f.write('-'*10 + '\n')
  vals, counts = np.unique(group['grades'],return_counts=True)
  counts = counts / (int(name[2]) + int(name[3]))
  counts = [int(x) for x in counts]
  for i,val in enumerate(vals):
    f.write('{}: {}\n'.format(val,counts[i]))

econHD = econHD.sort_values(['plane','MB','wagon','modIndex'])
f = open(f'output/geometriesECOND/{version}/geometryHDWagonByECONDGrades.txt','w')
f.write('plane MB typecode fluenceMod1 fluenceMod2 fluenceMod3 fluenceMod4\n')
for name,mods in econHD.groupby(['plane','MB','wagon']):
  f.write('{} {} {} {}\n'.format(name[0],name[1],*mods[['typecode','fluences']].iloc[0].values))
f.close()

#----------
# LD
#----------
# Compute fluence bin
fluenceRangesLD = 	[
			(econLD['fluence [Mrad]'] >= 0) & (econLD['fluence [Mrad]'] < 0.5),
                        (econLD['fluence [Mrad]'] >= 0.5) & (econLD['fluence [Mrad]'] < 1),
                        (econLD['fluence [Mrad]'] >= 1) & (econLD['fluence [Mrad]'] < 5),
                        (econLD['fluence [Mrad]'] >= 5) & (econLD['fluence [Mrad]'] < 10),
                        (econLD['fluence [Mrad]'] >= 10) & (econLD['fluence [Mrad]'] < 25),
                        (econLD['fluence [Mrad]'] >= 25),
			]
fluenceBinsLD = ['F','E','D','C','B','A']
econLD['fluence bin'] = np.select(fluenceRangesLD,fluenceBinsLD,default='N/A')

#table = econLD.groupby(['typecode','modIndex'])['fluence bin'].value_counts().to_latex()
#print(table)

econLD['grades'] = econLD.sort_values('modIndex').groupby(['plane','MB','wagon','modIndex'])['fluence bin'].transform(lambda x: ''.join(x))

f = open(f'output/geometriesECOND/{version}/LDWagonECONDGradesHist.txt','w')
# Counts of grades by wagon type
for name,group in econLD.groupby(['typecode']):
  f.write('-'*10 + '\n')
  f.write(name + '\n')
  f.write('-'*10 + '\n')
  vals, counts = np.unique(group['grades'],return_counts=True)
  counts = [int(x) for x in counts]
  for i,val in enumerate(vals):
    f.write('{}: {}\n'.format(val,counts[i]))

econLD = econLD.sort_values(['plane','u','v'])
f = open(f'output/geometriesECOND/{version}/geometryLDECONDGrades.txt','w')
f.write('plane u v typecode grade fluence \n')
for name,mods in econLD.groupby(['plane','u','v']):
  f.write('{} {} {} {} {} {:.3f}\n'.format(name[0],name[1],name[2],*mods[['typecode','grades','fluence [Mrad]']].iloc[0].values))
f.close()
