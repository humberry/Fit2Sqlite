Fit2Sqlite
==========

Convert your .fit file to Sqlite (earth.db), so they can be rendered by ShapeRender. With all the other shapes.<br />
<br />
You need the python-fitparse module (I use the version 2016-05-04) from [here][]. And the six module (version 1.10.0) from [there][].<br />
<br />
Every valid record (every record with lat/lon value) will be stored in one PolyLine. Fit file name => shape name (no .fit ending).
[here]: https://github.com/K-Phoen/python-fitparse/
[there]: https://pypi.python.org/pypi/six/
