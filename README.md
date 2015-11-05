PySeis
======

Open source pure-python siesmic processing

Goals:

Develop seismic processing code as a learning tool. 

All algorithms will be linked to peer-reviewed articles.

All modules will be commented and documented/

Philosophy:

Dont recreate the wheel. 

Leverage new technologies.

Flexible

Open and shared

=========

currently focused on filetype IO and trialing pytables/HDF5. 

=========


data format using [pytables](http://www.pytables.org/) 

![PyTables](http://www.pytables.org/moin/PyTables?action=AttachFile&do=get&target=pytables-powered.png)

segd/segy/su object management

matplotlib/mayavi visualisation

I've backed away from using EPD somewhat.  I dont want to have to install a huge IDE just to get numpy.

EPD free == convenient. EPD canopy == bloat.

pip + virtualenvs == better.