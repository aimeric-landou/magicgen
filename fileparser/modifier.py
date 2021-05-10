import os
import re

from Entities import SpellModifier
from Entities.namecond import NameCond
from Exceptions.ParseError import ParseError

modifier_params_int = ["damage", "schools", "spelltype", "aoe", "power", "skipchance", "range", "precision", "nreff",
                       "pathlevel", "fatiguecost", "maxpower", "maxbounces", "casttime", "effect", "givecloudsfx",
                       "aicastmod", "reqdamaging", "spec"]
modifier_params_str = []
modifier_params_float = ["scalecost", "scalerate", "pathperresearch", "scalefatigueexponent"]


def readModifierFile(fp):
    "Read one file and return all the spell modifiers within."
    out = {}
    curreff = None
    with open(fp, "r") as f:
        for lineno, line in enumerate(f):
            line = line.strip()
            if line == "": continue
            if line.startswith("--"): continue

            if line.startswith("#newmodifier"):
                if curreff is not None:
                    raise ParseError(f"{fp} line {lineno}: Unexpected #newmodifier (still parsing previous effect)")
                m = re.match("#newmodifier\W+\"(.*)\"\W*$", line)
                if m is None:
                    raise ParseError(f"{fp} line {lineno}: Expected an effect name, none was found")
                curreff = SpellModifier.SpellModifier()
                curreff.name = m.groups()[0]

            else:
                if curreff is None:
                    raise ParseError(f"{fp} line {lineno}: Expected a #newmodifier line")

                sorted = False

                # Params to simply copy
                for simple in modifier_params_int:
                    m = re.match(f"#{simple}\\W+?([-0-9]*)\\W*$", line)
                    if m is not None:
                        pval = int(m.groups()[0])
                        setattr(curreff, simple, pval)
                        sorted = True
                        break

                if sorted: continue

                for simple in modifier_params_str:
                    m = re.match(f"#{simple}" + "\\W+?\"(.*)\"\\W*", line)
                    if m is not None:
                        pval = m.groups()[0]
                        setattr(curreff, simple, pval)
                        sorted = True
                        continue

                if sorted: continue

                for simple in modifier_params_float:
                    m = re.match(f"#{simple}\W+?([-.0-9]*)\W*$", line)
                    if m is not None:
                        pval = float(m.groups()[0])
                        setattr(curreff, simple, pval)
                        sorted = True
                        continue

                if sorted: continue

                if line.startswith("#descrcond"):
                    m = re.match('#descrcond2\\W+([0-9]*)[ \t]([<>=!]+)\\W+(.+)[ \t]+([<>=!]+)\\W*([0-9]*)\\W+"(.*)"',
                                 line)
                    if m is not None:
                        cond = NameCond()
                        cond.val2 = m.groups()[0]
                        cond.op2 = m.groups()[1]
                        cond.param = m.groups()[2]
                        cond.op = m.groups()[3]
                        cond.val = m.groups()[4]
                        cond.text = m.groups()[5]
                        curreff.descrconds.append(cond)
                        continue

                    m = re.match('#descrcond\\W+(.+)[ \t]+([<>&=!]+)\\W*([0-9]*)\\W+"(.*)"', line)
                    if m is None:
                        raise ParseError(f"{fp} line {lineno}: bad #descrcond")
                    cond = NameCond()
                    cond.param = m.groups()[0]
                    cond.op = m.groups()[1]
                    cond.val = m.groups()[2]
                    cond.text = m.groups()[3]
                    curreff.descrconds.append(cond)
                    continue

                if line.startswith("#descr"):
                    m = re.match('#descr\\W+"(.*)"', line)
                    if m is None:
                        raise ParseError(f"{fp} line {lineno}: bad #descr")
                    curreff.descrs.append(m.groups()[0])
                    continue

                if line.startswith("#req"):
                    m = re.match('#req2\\W+([0-9]*)[ \t]([<>=!]+)\\W+(.+)[ \t]+([<>=!]+)\\W*?([0-9]+)', line)
                    if m is not None:
                        cond = NameCond()
                        cond.val2 = m.groups()[0]
                        cond.op2 = m.groups()[1]
                        cond.param = m.groups()[2]
                        cond.op = m.groups()[3]
                        cond.val = m.groups()[4]
                        cond.text = ""
                        curreff.reqs.append(cond)
                        continue

                    m = re.match('#req\\W+(.+)[ \t]+([<>&=!]+)\\W*?([0-9]+)', line)
                    if m is None:
                        raise ParseError(f"{fp} line {lineno}: bad #req")
                    cond = NameCond()
                    cond.param = m.groups()[0]
                    cond.op = m.groups()[1]
                    cond.val = m.groups()[2]
                    cond.text = ""
                    curreff.reqs.append(cond)
                    continue

                if line.startswith("#set"):
                    m = re.match('#set\\W+(.*?)\\W*?([-0-9]+)', line)
                    if m is not None:
                        param = m.groups()[0]
                        val = int(m.groups()[1])
                        curreff.setcommands.append([param, val])
                        continue
                    raise ParseError(f"{fp} line {lineno}: bad #set")

                if line.startswith("#mult"):
                    m = re.match('#mult\\W+(.*?)\\W*?([-0-9.]+)', line)
                    if m is not None:
                        param = m.groups()[0]
                        val = float(m.groups()[1])
                        curreff.multcommands.append([param, val])
                        continue
                    raise ParseError(f"{fp} line {lineno}: bad #mult")

                if line == "#nobattlefield":
                    curreff.nobattlefield = True
                    continue

                if line.startswith("#end"):
                    out[curreff.name] = curreff
                    curreff = None
                    continue

                raise ParseError(f"{fp} line {lineno}: Unrecognised content: {line}")
    return out


def readModifiersFromDir(dir):
    from Services.utils import modifiers
    out = modifiers
    for f in os.listdir(dir):
        if f.endswith(".txt"):
            c = readModifierFile(os.path.join(dir, f))
            for key in c:
                if key in out:
                    raise ParseError(f"SpellModifier named {key} already exists and was redefined in {f}")
                out[key] = c[key]
