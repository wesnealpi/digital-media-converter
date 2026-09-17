"""dmc: digital media converter.

Pipeline stages, each a small module with no side effects beyond what its name says:

- ``probe``     read stream metadata from a file with ffprobe
- ``classify``  decide which source class a file is (bluray, dvd, dvd_grainy, phone)
- ``profiles``  the HandBrake settings for each source class, from Wes's notes
- ``handbrake`` build and run a HandBrakeCLI command for a file and a profile
- ``naming``    Plex movie file names: ``Title (Year) {imdb-ttNNNNNNN}.mkv``
- ``pipeline``  glue: walk an inbox, classify, encode, move
"""

__version__ = "0.1.0"
