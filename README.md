# SFS Maneuver Calculator

A Python script to calculate the ΔV of a set of maneuvers. There are two setups to configure: file paths and maneuver list file.

1.  Main Script

    The main script, `main.py` needs three inputs, path of planet pack, path of maneuver, and plot maneuver toggle. If .env is not used, insert the path to `planet_pack_path` and `maneuver_path`, respectively. The lines for dotenv setup can be removed. If .env is used, configure the path for each on the .env file. Set `plot_maneuver` to `True` if one wants to see the plot of the trajectory.

    Setup if .env is used:
    
    ```
    from dotenv import dotenv_values
    paths=dotenv_values('.env')
    maneuver_path=paths['path_maneuver']
    planet_pack_path=paths['path_planetpack']
    ```
    
    Setup if .env is not used:
    
    ```
    maneuver_path=\path\to\your\maneuver.txt
    planet_pack_path=\path\to\your\planetpack    
    ```
2. Maneuver list file

   There are thee examples of maneuver list file. The file uses .json formatting. "maneuverdefault" is the format for each type of maneuvers. There are 5 types, each with a list of required parameters.

    * Type 0

      This is just an addition of ΔV to the calculation. For example, gravity assist correction burns, RCS offset, extra margin, landing maneuver, etc.
        ```
        Required parameters:
        -  type    : 0
        -  DV      : the amount of ΔV
        -  margin  : the margin of ΔV
        ```
        The format for margin is as follows: if starting with "+" will adds the value to ΔV, while plain numbers will be multiplied to ΔV. For example, for ΔV = "100", margin = "+10" will result in 110 m/s, while margin = "1.04" will result in 104 m/s.
    - Type 1

      This maneuver is an apsis change maneuver. For example, from low orbit to high elliptic orbit.
        ```
        Required parameters:
        -  type    : 1
        -  b       : The celestial body the spacecraft is orbiting
        -  A1      : The apsis where the burn is performed
        -  A21     : Initial opposite apsis
        -  A22     : Final opposite apsis
        -  margin
        ```
        For apsides, the format is either "LO", "####", "###h". Numbers must be in meters. LO is low orbit, set at 2 km above minimum timewarp speed height. "####" is distance from the center of the celestial body. "####h" is the height from the surface of the celestial body. For example, in Normal Mode at Earth, LO is 32 km in game value, 500000 is around 185,9 km in game value (500000 - Earth Radius), and 50000h is 50 km in game value.
    - Type 2
      
      This maneuver only calculates ΔV of an escape maneuver. Typically for planning a flyby.
    - Type 3
      
      This maneuver only calculates ΔV of a capture maneuver. Typically for calculating capture maneuver from an arbitrary orbit.
    - Type 4
      
      A fully Hohmann transfer maneuver. Calculates both the escape and capture ΔV
        ```
        For maneuver type 2,3,4, the required parameters are:
        -  type    : 2/3/4
        -  b1      : Inital celestial body
        -  A1      : Apoapsis at b1
        -  P1      : Periapsis at b1
        -  argP1   : argument of periapsis, in degrees
        -  margin1 : margin for the first maneuver
        -  b2      : Final celestial body
        -  A2      : Apoapsis at b2
        -  P2      : Periapsis at b2
        -  argP2   : argument of periapsis at b2
        -  margin2 : margin for the second maneuver
        -  scenario: the value is "max" or "min", depending on one's needs
        ```
        Eventhough maneuver 2 and 3 seems to have redundant requirements, for example a flyby from Low Earth Orbit to Venus doesn't require the apsides at Venus to be defined, it would need to be defined if the flyby is, for example, from Low Moon Orbit to Low Earth Orbit.

    <details>
    <summary>Maneuver format</summary>
        
    ```json
    "maneuver_default": {
        "maneuver_type0": {
            "type": 0,
            "DV": 100,
            "margin": "1"
        },
        "maneuver_type1_justburn": {
            "type": 1,
            "b": "body1",
            "A1": "LO/100/100h",
            "A21": "LO/100/100h",
            "A22": "LO/100/100h",
            "margin": "1"
        },
        "maneuver_type2_escape2flyby": {
            "type": 2,
            "b1": "body1",
            "A1": "LO/100/100h",
            "P1": "LO/100/100h",
            "argP1": "0",
            "margin1": "1",
            "b2": "body2",
            "A2": "LO/100/100h",
            "P2": "LO/100/100h",
            "argP2": "0",
            "scenario": "max/min"
        },
        "maneuver_type3_flyby2capture": {
            "type": 3,
            "b1": "body1",
            "A1": "LO/100/100h",
            "P1": "LO/100/100h",
            "argP1": "0",
            "b2": "body2",
            "A2": "LO/100/100h",
            "P2": "LO/100/100h",
            "argP2": "0",
            "margin2": "1",
            "scenario": "max/min"
        },
        "maneuver_type4_fullhohmann": {
            "type": 4,
            "b1": "body1",
            "A1": "LO/100/100h",
            "P1": "LO/100/100h",
            "argP1": "0",
            "margin1": "1",
            "b2": "body2",
            "A2": "LO/100/100h",
            "P2": "LO/100/100h",
            "argP2": "0",
            "margin2": "1",
            "scenario": "max/min"
        }
    }
    ```
    
    </details>
After both is set up, hit run on `main.py` and the script will print out the calculating process, and finally will print out the summary of the ΔV for each maneuver and the total ΔV.

## Limitations:
1.  Limited to up to 3 level planet systems: central body (level 1), orbiting central body (level 2), orbiting level 2 (level 3).
2.  The script does not compute when to do the maneuver. It is assumed the planet positions are already aligned.
3.  As for now, in the case of calculation between a higher level body and a lower level body, for example from Sun orbit to Mercury capture, if the Sun orbit and Mercury orbit crosses, there are possibility where the calculation could go wrong.

## Examples
Example process print out:

<img src="images/process.png" width="600" alt="demo">

Example summary print out:

<img src="images/summary.png" width="600" alt="demo">
