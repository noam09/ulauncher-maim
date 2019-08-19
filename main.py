import os
import logging
import distutils.spawn
from datetime import datetime
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.RunScriptAction import RunScriptAction

logging.basicConfig()
logger = logging.getLogger(__name__)

icon_path = "images/icon.svg"

maim_bin = ""
xdotool_bin = ""
convert_bin = ""
# Locate maim binary
maim_bin = distutils.spawn.find_executable('maim')
convert_bin = distutils.spawn.find_executable('convert')
xdotool_bin = distutils.spawn.find_executable('xdotool')
# This extension is useless without maim
if maim_bin is None or maim_bin == "":
    logger.error("maim executable path could not be determined")
    exit()
if xdotool_bin is None or xdotool_bin == "":
    logger.error("xdotool executable path could not be determined, no active window for you")
    exit()
if convert_bin is None or convert_bin == "":
    logger.error("convert executable path could not be determined, no fancy for you")
    fancy = ""
else:
    fancy = " | {convert} - \( +clone -background black -shadow 80x3+5+5 \) +swap -background none -layers merge +repage".format(convert=convert_bin)

global output_path, delay, hide_cursor, extra_args
output_path = "/tmp/"
delay = 3
extra_args = "--hidecursor"
timestr = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def base_cmd():
    return 'sleep {delay} && {bin} {extra}'.format(bin=maim_bin,
                                                   delay=delay,
                                                   extra=extra_args)


def commands():
    c = {
        "area": {
            "name": "Area",
            "desc": "Select area to capture",
            "icon": "images/icon.svg",
            "run":  "{base_cmd} --select".format(base_cmd=base_cmd())
        },
        "window": {
            "name": "Select Window",
            "desc": "Capture selected window",
            "icon": "images/icon.svg",
            # "run":  "{base_cmd} -i $({xdotool} selectwindow)".format(base_cmd=base_cmd(), xdotool=xdotool)
            "run":  "{base_cmd} --select --tolerance=9999999".format(base_cmd=base_cmd())
        },
        "window_active": {
            "name": "Active Window",
            "desc": "Capture active window",
            "icon": "images/icon.svg",
            "run":  "{base_cmd} -i $({xdotool} getactivewindow)".format(base_cmd=base_cmd(), xdotool=xdotool_bin)
            # "run":  "{base_cmd} --select --tolerance=9999999".format(base_cmd=base_cmd())
        },
        "full": {
            "name": "Fullscreen",
            "desc": "Capture entire screen",
            "icon": "images/icon.svg",
            "run":  "{base_cmd}".format(base_cmd=base_cmd())
        },
        "area_fancy": {
            "name": "Fancy Area",
            "desc": "Select area to capture and apply shadow",
            "icon": "images/icon.svg",
            "run":  "{base_cmd} --hidecursor --select {fancy} ".format(base_cmd=base_cmd(), fancy=fancy)
        },
        "window_fancy": {
            "name": "Fancy Window",
            "desc": "Capture active window and apply shadow",
            "icon": "images/icon.svg",
            # "run":  "{base_cmd} -i $({xdotool} selectwindow)".format(base_cmd=base_cmd(), xdotool=xdotool)
            "run":  "{base_cmd} --select --tolerance=9999999 {fancy} ".format(base_cmd=base_cmd(), fancy=fancy)
        },
    }
    return c


def outputs(d=None):
    global output_path
    timestr = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = "screenshot_{}.png".format(timestr)
    r = {
            "clipboard": " | xclip -selection clipboard -t image/png",
            "file": '"{}"'.format(os.path.join(output_path, filename))
        }
    if d:
        return r[d]
    return r


class MaimExtension(Extension):

    def __init__(self):
        super(MaimExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())


class KeywordQueryEventListener(EventListener):
    def on_event(self, event, extension):
        global output_path, delay, extra_args
        output_path = os.path.expanduser(extension.preferences["output"])
        try:
            if isinstance(int(extension.preferences["delay"]), (int, long)):
                delay = int(extension.preferences["delay"])
            else:
                delay = 0
        except Exception as e:
            logger.error("Delay setting is not an integer: {}".format(str(e)))
        extra_args = extension.preferences["extra"]
        fullquery = event.query.split(" ")
        fullquery = filter(None, fullquery)
        items = []

        if len([fullquery]) > 0:
            c = commands()
            for cmd in commands():
                if len([fullquery]) == 1 or any(word in str(c[cmd]["name"]).lower() for word in fullquery):
                    for output in outputs():
                        # if len(fullquery) == 1 or \
                        #    (len(fullquery) > 2 and any(o in output.lower() for o in fullquery[2:])):
                        items.append(run_cmd(cmd, output))
            return RenderResultListAction(items)


def run_cmd(cmd, output):
    c = commands()
    # logger.debug('\n\n{} {}\n\n'.format(c[cmd]["run"], outputs(output)))
    if output == "clipboard":
        i = output
    else:
        i = cmd
    return ExtensionResultItem(icon=icon(i),
                               name="{} to {}".format(c[cmd]["name"], output),
                               description=c[cmd]["desc"],
                               on_enter=RunScriptAction('{} {}'.format(c[cmd]["run"], outputs(output)), None))


def icon(i):
    c = commands()
    if i == "clipboard":
        return "images/clipboard.svg"
    if "area" in c[i]["name"].lower():
        return "images/crop.svg"
    if "window" in c[i]["name"].lower():
        return "images/window.svg"
    return c[i]["icon"]


if __name__ == "__main__":
    MaimExtension().run()
