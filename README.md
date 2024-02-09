PySeis
======
One of the big issues I had was handling non-standard headers. A static dtype is kind of difficult to manipulate.

The problem then compounds when dealing with some of the segd header types, e.g. bcd, 4 bit ints etc. 

As a result I'm completely changing the IO methodologies, with the goal of being able to read and write -ANY- file format, not just SU.

Current proof of concepts have working examples of segd3.0, SU, javaseis and xml.

I'm coding to master. shoot me! but pyseis up to this point has basically been part time experimentation into IO and has never been stable enough to push a release.

My current goals are:

* get the IO sorted (finally)
* re-write the basic processing tools to handle the new IO. The internal data format will either be SU or SEGY with little endian IEEE floats
* re-write/streamline the viewing tools. A lot of work was put into them back in the day, and being able to view any filetype directly with matplotlib and do introspection on headers is the main draw of pyseis right now.

Dependencies
==========

As the data is now stored as classes it naturally calls to dataclasses. This means we're python 3.7+ now.
