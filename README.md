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
