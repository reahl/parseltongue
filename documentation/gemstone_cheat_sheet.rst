======================
Gemstone Cheat Sheet
======================
terminal commands
----------------------------------------

- Stone commands:

    Start stone:
    startstone - start the GemStone repository monitor process

    $ startstone

    Stop stone:
    stopstone - conduct an orderly shutdown of a running GemStone repository monitor process

    $ stopstone

- NetLDI:

    Start netldi in guest mode:
    startnetldi - start the GemStone network server process

    $ startnetldi -g -a vagrant -l /tmp/netldi.log

    Stop netldi
    stopnetldi - gracefully stop a GemStone network server

    $ stopnetldi 

- Gemstone:
  gslist - List GemStone server processes

  $ gslist

- Run topaz:
  topaz - linear GemStone Programming Environment

  $ topaz

Gemstone Login Details:
---------------------------------------------

=============  ============  ============
login details  Host          Gemstone
=============  ============  ============
Username       vagrant       DataCurator
Password       vagrant       swordfish
=============  ============  ============