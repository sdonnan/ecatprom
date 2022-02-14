An EtherCAT SII PROM Tool
=========================

A library and Tk GUI for editing SII PROM files.

Installation
------------

    pip install .

Usage
-----

    $ ecatprom somefile.bin             # opens GUI for viewing / editing
    $ ecatprom --no-gui somefile.bin    # just prints parsed file contents to terminal and exits

To Do
-----

* [x] `setup.py` installer
* Calculate CRC for Config Data in Info section
* Make the GUI not look like a train wreck
* More thorough testing on less used categories
