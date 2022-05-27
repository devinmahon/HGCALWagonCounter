# Setup

Create the necessary directories. 

```bash
mkdir -p output/wagonSummaries output/fiberHistograms wagonDict
```

# Usage

## Wagon Counting

```bash
python wagonCounter.py
```

## Wagon Drawing

```bash
python wagonDrawer.py
```

## Finding Wagons in Mapper

```bash
# python findWagon.py [WAGON CODE]
# For example:
python findWagon.py 000F30F30F
```

The output will be a list of all instances of the specified code for which each element indicates the layer, MB index, and wagon index of each instance.

# Wagon Code Format

The `wagonCounter.py` script works by determing a code, represented by a string, that uniquely identifies a wagon variety.
With this code, the type, shape, and orientation of all modules in a wagon can be reconstructed. 
The meaning of each part of the code is described below/ 

## General Structure

The first part of a code consists of the first 3 elemtns and is general to all wagon varieties. 

* Index 0 (first element): LD (`0`) or HD (`1`). 

* Index 1: enigine position, as indicated by the ordering of the modules in the second part of the code. 
If it's a "west" wagon, this element will tell you which module has the engine on it. 
If it's an east wagon, this element is set to `-1`.
The way the geometry file is structured, the position of the engine on east wagons is not specified and must be determine by hand. 

* Index 2: number of outgoing trigger links, i.e. the number than go out over the crossover links.
A negative value indicates that the links are incoming rather than outgoing. 

The second part of the code tells you how to iterate over modules in order, placing them in the right relative positions and orientations. 

* Index 3: the character indicating the type of the first module to be considered, e.g. `F` for a full module. 

After this (if there is more than one module), codes come in groups of 3: 

* The first element in a group indicates the placement of the next module relative to the first. 
Here, we consider the first module pointing "downwards", i.e. with it's DCDC module in the south position. 
This element will be a number `0` through `5`, standing for the number of 60-degree rotations from 0 degrees horizontal (east).
So, for example, if the value is `3`, this means that the next module will be placed directly to the left (180 degrees) of the current module. 
* The second element in a group indicates the orientation of the module relative to the downward orientation of the previous module. 
Again, this will be a value between `0` and `6` for the number of 60-degree rotations from the dowward position. 
So, for example, if the calue is `1`, this means that the next module will have it's DCDC module pointing 60 degrees counterclockwise from the previous one. 
* The third and final element in a group indicates the type of module with a single character, as before. 
