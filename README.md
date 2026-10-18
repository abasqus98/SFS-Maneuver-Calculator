SFS Maneuver Calculator

A Python script to calculate the delta-V of a set of maneuvers.

There are two setups to configure
1.  Main Script
The main script needs two inputs, planet pack path and  maneuver list path.
If .env is not used, insert them as  planet_pack_path and maneuver_path, respectively. The lines for dotenv setup can be removed.
If .env is used, configure the path for each on the .env file.

2. Maneuver list
There are two examples of maneuver list file. The file uses .json formatting. "tripdefault" is the format for each type of maneuvers. There are 5 types, each with list of parameters
    1. Type 0
    2. Type 1
    3. Type 2
    4. Type 3
    5. Type 4
