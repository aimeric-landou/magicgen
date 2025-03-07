import copy
import csv
import re

from typing import (
    Dict,
    List, Union,
)

from DataObject.MagePathRandom import MagePathRandom
from Entities.nationalsite import Site

from Entities.nation import Nation
from Entities.nationalmage import NationalMage

nations: Dict[int, Nation] = {}  # map nation id to nation

vanillamages: Dict[int, NationalMage] = {} # map unit id to NationalMage object

spellids = []
weaponids = []
siteids = []
monsterids: List[int] = []
eventcodes = []
montagids = []


def _read_vanilla_unit_nation_map_file(path:str, nationalunits):
    with open(path, "r") as datacsv:
        reader = csv.DictReader(datacsv, delimiter="\t")
        for line in reader:
            nationid = int(line["nation_number"])
            unitid = int(line["monster_number"])
            if nationid not in nationalunits:
                nationalunits[nationid] = []
            nationalunits[nationid].append(unitid)

def _read_vanilla_cap_only_site_recruits(nationalunits):
    startsites_to_nations: Dict[int, List[int]] = {}
    with open("data/attributes_by_nation.csv") as datacsv:
        reader = csv.DictReader(datacsv, delimiter="\t")
        for line in reader:
            # attrib 52 is starting site
            attrib_int = int(line["attribute"])
            if attrib_int == 52:
                siteid = int(line["raw_value"])
                nationid = int(line["nation_number"])
                if siteid not in startsites_to_nations:
                    startsites_to_nations[siteid] = []
                startsites_to_nations[siteid].append(nationid)

    with open("data/MagicSites.csv") as datacsv:
        reader = csv.DictReader(datacsv, delimiter="\t")
        for line in reader:
            siteid = int(line["id"])
            if siteid in startsites_to_nations:
                for n in range(1, 6):
                    key = f"hcom{n}"
                    if len(line[key]) == 0:
                        break
                    if siteid not in startsites_to_nations:
                        continue
                    unitid = int(line[key])
                    for nationid in startsites_to_nations[siteid]:
                        nationalunits[nationid].append(unitid)



def read_vanilla():
    nationalunits = {}
    _read_vanilla_unit_nation_map_file("data/VanillaLeaderMaps/fort_leader_types_by_nation.csv", nationalunits)
    _read_vanilla_unit_nation_map_file("data/VanillaLeaderMaps/coast_leader_types_by_nation.csv", nationalunits)
    _read_vanilla_unit_nation_map_file("data/VanillaLeaderMaps/nonfort_leader_types_by_nation.csv", nationalunits)

    _read_vanilla_cap_only_site_recruits(nationalunits)

    # Get their info
    unitdata = {}
    with open("data/BaseU.csv", "r") as datacsv:
        reader = csv.DictReader(datacsv, delimiter="\t")
        for line in reader:
            unitdata[int(line["id"])] = copy.copy(line)

    for nationid, units in nationalunits.items():
        if nationid not in nations:
            nations[nationid] = Nation(nationid)
        for unitid in units:
            if unitid in unitdata:
                dataline = unitdata[unitid]
                mage: NationalMage = NationalMage()
                for index, key in enumerate(["F", "A", "W", "E", "S", "D", "N", "B"]):
                    if dataline[key] != "":
                        mage.add_magic_path(2 ** index, int(dataline[key]))

                for n in range(1, 7):
                    if dataline[f"mask{n}"] == "":
                        break
                    mask = int(dataline[f"mask{n}"]) >> 7
                    chance = int(dataline[f"rand{n}"])
                    instances = int(dataline[f"nbr{n}"])
                    link = int(dataline[f"link{n}"])
                    for i in range(instances):
                        mage.add_magic_random(MagePathRandom(chance=chance, link=link, paths=mask))

                mage.name = dataline[f"name"]

                if mage.is_mage():
                    nations[nationid].add_mage(mage)
                    vanillamages[unitid] = mage


def read_mods(modstring):
    global monsterids, weaponids, spellids, eventcodes, montagids, siteids
    mods = modstring.strip().split(",")
    monsterids = [3499]
    weaponids = [799]
    siteids = [1499]
    spellids = [1299]
    eventcodes = [-299]
    montagids = [1000]
    for mod in mods:
        mod = mod.strip()
        if mod == "":
            continue
        with open(mod, "r", encoding="u8") as f:
            currentsite: Union[Site, None] = None
            sites: Dict[int, Site] = {}
            sitenames: Dict[str, int] = {}
            # TODO Sites that are defined after nations with them as startsite

            nationstartsites: Dict[Nation, List[Union[int, str]]] = {}
            sitecommanders: Dict[Site, List[Union[int, str]]] = {}

            currentnation: Union[Nation, None] = None
            currentunit: Union[NationalMage,None] = None

            units: Dict[int, NationalMage] = {}

            for line in f:
                if "--" in line:
                    line = line[0:line.find("--")].strip()
                line = line.strip()
                if line == "": continue

                m = re.match("#newmonster (\\d+)", line)
                if m is None:
                    m = re.match("#selectmonster (\\d+)", line)
                if m is not None:
                    unitid = int(m.groups()[0])
                    print(f"Parsed newmonster {unitid}")
                    if unitid not in units:
                        units[unitid] = NationalMage()
                        units[unitid].id = unitid
                        monsterids.append(unitid)
                    currentunit = units[unitid]
                elif line.startswith("#newmonster"):
                    newid = max(monsterids) + 1
                    units[newid] = NationalMage()
                    monsterids.append(newid)
                    currentunit = units[newid]
                    currentunit.id = newid

                m = re.match("#montag (\\d+)", line)
                if m is not None:
                    newid = int(m.groups()[0])
                    montagids.append(newid)
                    print(f"Parsed montag {newid}")

                m = re.match("#code (.+)", line)
                if m is None:
                    m = re.match("#code2 (.+)", line)
                if m is None:
                    m = re.match("#codedelay (.+)", line)
                if m is None:
                    m = re.match("#codedelay2 (.+)", line)
                if m is not None:
                    newid = int(m.groups()[0])
                    eventcodes.append(newid)
                    print(f"Parsed event code {newid}")

                m = re.match("#newspell (\\d+)", line)
                if m is None:
                    m = re.match("#selectspell (\\d+)", line)
                if m is not None:
                    newid = int(m.groups()[0])
                    spellids.append(newid)
                    print(f"Parsed spell {newid}")
                elif line.startswith("#newspell"):
                    newid = max(spellids) + 1
                    print(f"Parsed spell with implied id {newid}")
                    spellids.append(newid)

                m = re.match("#newweapon (\\d+)", line)
                if m is None:
                    m = re.match("#selectweapon (\\d+)", line)
                if m is not None:
                    newid = int(m.groups()[0])
                    weaponids.append(newid)
                elif line.startswith("#newweapon"):
                    newid = max(weaponids) + 1
                    weaponids.append(newid)

                m = re.match("#newsite\\W+(\\d+)", line)
                if m is None:
                    m = re.match("#selectsite\\W+(\\d+)", line)
                if m is not None:
                    newid = int(m.groups()[0])
                    if newid not in sites:
                        sites[newid] = Site(newid)
                        sites[newid].id = newid
                        siteids.append(newid)
                    currentsite = sites[newid]
                elif line.startswith("#newsite"):
                    newid = max(siteids) + 1
                    sites[newid] = Site(newid)
                    sites[newid].id = newid
                    siteids.append(newid)
                    currentsite = sites[newid]

                m = re.match("#selectnation (\\d+)", line)
                if m is not None:
                    nationid = int(m.groups()[0])
                    print(f"Parsed selectnation {nationid}")
                    if nationid not in nations:
                        nations[nationid] = Nation(nationid)
                    currentnation = nations[nationid]

                m = re.match("#newnation", line)
                if m is not None:
                    newid = -1
                    while newid in nations:
                        newid -= 1
                    print(f"Parsed newnation, assigned id {newid}")
                    if newid not in nations:
                        nations[newid] = Nation(newid)
                    currentnation = nations[newid]

                m = re.match("#name [\"](.+)[\"]", line)
                if m is not None:
                    name = m.groups()[0]
                    if currentsite is not None:
                        print(f"Attach site name {name} to {currentsite}")
                        currentsite.name = name
                        sitenames[name] = currentsite.id
                    elif currentnation is not None:
                        print(f"Attach nation name {name} to {currentnation}")
                        currentnation.name = name
                    elif currentunit is not None:
                        print(f"Attach unit name {name} to {currentunit}")
                        currentunit.name = name

                m = re.match("#era\\W+(.+)", line)
                if m is not None:
                    currentnation.era = int(m.groups()[0])
                    print(f"Set Era for nation {currentnation.id} to {currentnation.era}")

                m = re.match("#homecom (\\d+)", line)
                if m is not None:
                    unitid = int(m.groups()[0])
                    if currentsite is None:
                        raise ValueError(f"Attempt to assign home com {unitid} to nonexistent site")
                    if currentsite not in sitecommanders:
                        sitecommanders[currentsite] = []
                    sitecommanders[currentsite].append(unitid)
                    print(f"Assign Commander {unitid} to site {currentsite}")

                m = re.match("#startsite [\"](.+)[\"]", line)
                if m is not None:
                    name = m.groups()[0]
                    if currentnation not in nationstartsites:
                        nationstartsites[currentnation] = []
                    nationstartsites[currentnation].append(name)

                    print(f"Assign startsite {name} as belonging to {currentnation}")

                m = re.match("#addreccom (\\d+)", line)
                if m is not None:
                    unitid = int(m.groups()[0])
                    print(f"{unitid} is a recruitable commander of {currentnation}")
                    if currentnation is None:
                        print(f"Warning: {unitid} is set as a recruited commander, but no nation selected - ignored as"
                              f" this is likely a poptype addition")
                    else:
                        if unitid in units:
                            currentnation.add_mage(units[unitid])
                        else:
                            if unitid in vanillamages:
                                currentnation.add_mage(vanillamages[unitid])
                            else:
                                print(f"{unitid} appears to be a non-mage non-modded unit, ignored")

                if line.strip() == "#disableoldnations":
                    print(f"found disableoldnations")
                    for x in range(0, 120):
                        if x in nations:
                            del nations[x]

                if line.strip() == "#end":
                    print(f"Found #end")
                    currentnation = None
                    currentsite = None
                    currentunit = None

                m = re.match("#magicskill (\\d+) (\\d+)", line)
                if m is not None:
                    # In normal dominions modding, path flags are 0-7, just for this I converted them into their
                    # 2^n bitmask form
                    path = 2**int(int(m.groups()[0]))
                    level = int(m.groups()[1])
                    print(f"Give guaranteed path {path} of strength {level} to current commander")
                    currentunit.add_magic_path(path, level)

                m = re.match("#custommagic (\\d+) (\\d+)", line)
                if m is not None:
                    mask = int(m.groups()[0]) >> 7
                    chancemask = int(m.groups()[1])
                    if chancemask > 100:
                        chance = 100
                        link = int(chancemask / 100)
                    else:
                        link = 1
                        chance = chancemask
                    random = MagePathRandom(paths=mask, chance=chance, link=link)
                    print(f"Give random path {mask} to current commander")
                    currentunit.add_magic_random(random)

            for nation in nationstartsites:
                for siteid in nationstartsites[nation]:
                    if siteid in sitenames:
                        nation.sites.append(sites[sitenames[siteid]])
                    else:
                        if siteid in sites:
                            nation.sites.append(sites[siteid])
                        else:
                            print(f"Nation has start site with ID {siteid}, this site was not found, ignored")

            for site in sitecommanders:
                 for unitid in sitecommanders[site]:
                    if unitid in units:
                        site.mages.append(units[unitid])
                    elif unitid in vanillamages:
                        site.mages.append(vanillamages[unitid])
                    else:
                        print(f"Site {site} had commander {unitid} added, but this seems to not be a mage: skipped")



