# csv_show_python
Utility for presenting CSV (Comma separated value) files in terminals with user-friendly formatting.  
The script provides query, grep, column selection, and user-extensibility.

Please use **csv_show.py -help** for the up-to-date description of all features.

## Example usages
Show all data and pipe output to "less" if it won't fit in the terminal.
```
csv_show.py data/cars.csv
```

Show only certain columns cap the width of some of them:
```
csv_show.py data/cars.csv   -columns Model,Year -max_width Model=5
```

Show only cars with Model=Ford
```
csv_show.py data/cars.csv  -select Make=Ford
```

Remove lines that look like comments:
```
csv_show.py data/tmp.csv  -grepv "^(//|#)"
```

Get the value of exactly one cell:
```
csv_show.py data/cars.csv  -lookup Model Make=Ford Year=1996
```
