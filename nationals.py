import copy
import csv
import re

from spellstructures import utils

nationals = {}
nationinfo = {}

spellids = []
weaponids = []
monsterids = []


class Nation(object):
    "Container for modded nation info, used for the UI only"
    def __init__(self, id):
        self.era = None
        self.name = None
        self.epithet = None
        self.id = id


class NationalMage(object):
    "Container for a single national mage and its path access"
    def __init__(self):
        self.guaranteedpaths = 0
        self.randompaths = 0
        self.allpaths = 0

    def update(self):
        self.allpaths = 0
        # get rid of holy levels
        if self.guaranteedpaths & 256: self.guaranteedpaths -= 256
        if self.randompaths & 256: self.randompaths -= 256
        for flag in utils.breakdownflag(self.guaranteedpaths) + utils.breakdownflag(self.randompaths):
            if not self.allpaths & 2 ** flag:
                self.allpaths += 2 ** flag


def readVanilla():
    nationalunits = {}
    with open("fort_leader_types_by_nation.csv", "r") as datacsv:
        reader = csv.DictReader(datacsv, delimiter="\t")
        for line in reader:
            nation = int(line["nation_number"])
            unit = int(line["monster_number"])
            if nation not in nationalunits:
                nationalunits[nation] = []
            nationalunits[nation].append(unit)

    # Get their info
    unitdata = {}
    with open("BaseU.csv", "r") as datacsv:
        reader = csv.DictReader(datacsv, delimiter="\t")
        for line in reader:
            unitdata[int(line["id"])] = copy.copy(line)

    for nation, units in nationalunits.items():
        if nation not in nationals:
            nationals[nation] = []
        for unitid in units:
            if unitid in unitdata:
                dataline = unitdata[unitid]
                obj = NationalMage()
                for index, key in enumerate(["F", "A", "W", "E", "S", "D", "N", "B", "H"]):
                    if dataline[key] != "":
                        obj.guaranteedpaths += 2 ** index

                for n in range(1, 5):
                    if dataline[f"mask{n}"] == "":
                        break
                    mask = int(dataline[f"mask{n}"])
                    for exponent in range(7, 16):
                        val = 2 ** exponent
                        if mask & val:
                            zeroedval = 2 ** (exponent - 7)
                            if not (obj.randompaths & zeroedval):
                                obj.randompaths += zeroedval

                # get rid of holy levels and calc obj.allpaths
                obj.update()

                if obj.guaranteedpaths > 0 or obj.randompaths > 0:
                    nationals[nation].append(obj)


def readMods(modstring):
    global monsterids, weaponids, spellids
    mods = modstring.strip().split(",")
    monsterids = [3499]
    weaponids = [799]
    spellids = [1299]
    for mod in mods:
        mod = mod.strip()
        if mod.strip() == "":
            continue
        with open(mod, "r") as f:
            lastnation = None
            foundnationend = True
            lastunit = None
            lastsite = None
            lastobj = None
            units = {}
            siteunits = {}
            sitenames = {}
            startsites = {}
            nationalunits = {}

            for line in f:
                if line.strip() == "": continue
                line = line.strip()
                m = re.match("#newmonster (\\d*)", line)
                if m is None:
                    m = re.match("#selectmonster (\\d*)", line)
                if m is not None:
                    if lastunit is not None:
                        units[lastunit] = lastobj
                    print(f"Parsed newmonster {m.groups()[0]}")

                    lastunit = int(m.groups()[0])
                    monsterids.append(int(m.groups()[0]))
                    lastobj = NationalMage()
                elif line.startswith("#newmonster"):
                    newid = max(monsterids) + 1
                    monsterids.append(newid)



                m = re.match("#newspell (\\d*)", line)
                if m is None:
                    m = re.match("#selectspell (\\d*)", line)
                if m is not None:
                    newid = int(m.groups()[0])
                    spellids.append(newid)
                    print(f"Parsed spell {newid}")
                elif line.startswith("#newspell"):
                    newid = max(spellids) + 1
                    print(f"Parsed spell with implied id {newid}")
                    spellids.append(newid)

                m = re.match("#newweapon (\\d*)", line)
                if m is None:
                    m = re.match("#selectweapon (\\d*)", line)
                if m is not None:
                    print(m.groups())
                    print(line)
                    newid = int(m.groups()[0])
                    weaponids.append(newid)
                elif line.startswith("#newweapon"):
                    newid = max(weaponids) + 1
                    weaponids.append(newid)


                m = re.match("#selectnation (\\d*)", line)
                if m is not None:
                    print(f"Parsed selectnation {m.groups()[0]}")
                    lastnation = int(m.groups()[0])
                    foundnationend = False
                    nationals[lastnation] = []
                    nationinfo[lastnation] = Nation(lastnation)

                m = re.match("#newsite (\\d*)", line)
                if m is not None:
                    print(f"Parsed newsite {m.groups()[0]}")
                    lastsite = int(m.groups()[0])

                m = re.match("#name [\"](.*)[\"]", line)
                if m is not None:
                    if m.groups()[0] not in sitenames:
                        print(f"Attach site name {m.groups()[0]} to {lastsite}")
                        sitenames[m.groups()[0]] = lastsite

                    if not foundnationend:
                        nationinfo[lastnation].name = m.groups()[0]

                m = re.match("#era (.*)", line)
                if m is not None:
                    nationinfo[lastnation].era = int(m.groups()[0])

                m = re.match("#homecom (\\d*)", line)
                if m is not None:
                    if lastsite not in siteunits:
                        siteunits[lastsite] = []
                    siteunits[lastsite].append(int(m.groups()[0]))
                    print(f"Assign Commander {m.groups()[0]} to site {lastsite}")

                m = re.match("#startsite [\"](.*)[\"]", line)
                if m is not None:
                    if lastnation not in startsites:
                        startsites[lastnation] = []
                    print(f"Assign startsite {m.groups()[0]} as belonging to {lastnation}")
                    startsites[lastnation].append(m.groups()[0])

                m = re.match("#addreccom (\\d*)", line)
                if m is not None:
                    if lastnation not in nationalunits:
                        nationalunits[lastnation] = []
                    print(f"{m.groups()[0]} is a recruitable commander of {lastnation}")
                    nationalunits[lastnation].append(int(m.groups()[0]))

                if line.strip() == "#disableoldnations":
                    print(f"found disableoldnations")
                    for x in range(0, 120):
                        if x in nationals:
                            if x not in nationinfo:
                                del nationals[x]

                if line.strip() == "#end":
                    if not foundnationend:
                        print(f"found nation end")
                        foundnationend = True

                m = re.match("#magicskill (\\d*) (\\d*)", line)
                if m is not None:
                    path = int(m.groups()[0])
                    if path not in utils.breakdownflag(lastobj.guaranteedpaths):
                        print(f"Give guaranteed path {path} to current commander")
                        lastobj.guaranteedpaths += 2 ** path

                m = re.match("#custommagic (\\d*) (\\d*)", line)
                if m is not None:
                    mask = int(m.groups()[0])
                    for path in [0, 1, 2, 3, 4, 5, 6, 7, 8]:
                        if mask & 2 ** (path + 7):
                            if path not in utils.breakdownflag(lastobj.randompaths):
                                print(f"Give random path {path} to current commander")
                                lastobj.randompaths += 2 ** path

        for nation, sitelist in startsites.items():
            for sitename in sitelist:
                site = sitenames[sitename]
                if site in siteunits:
                    for unit in siteunits[site]:
                        obj = units[unit]
                        obj.update()
                        if obj.guaranteedpaths > 0 or obj.randompaths > 0:
                            nationals[nation].append(obj)

        for nation, unitlist in nationalunits.items():
            for unit in unitlist:
                obj = units[unit]
                obj.update()
                if obj.guaranteedpaths > 0 or obj.randompaths > 0:
                    nationals[nation].append(obj)
