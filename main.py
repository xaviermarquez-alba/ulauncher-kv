import sqlite3
import os
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.RunScriptAction import RunScriptAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction


_icon_ = "images/icon.svg"
_db_ = os.getenv("HOME") + "/.kv.db"
_name_ = "Kv"


class KvExtension(Extension):

    def __init__(self):
        super(KvExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())
        connection = sqlite3.connect(_db_)
        statement = '''CREATE TABLE IF NOT EXISTS KV ( KEY TEXT NOT NULL, VALUE TEXT NOT NULL,  TAGS TEXT NOT NULL );'''
        connection.execute(statement)


class KeywordQueryEventListener(EventListener):

    def on_event(self, event, extension):
        arguments = (event.get_query().get_argument() or "")
        if arguments != "":
            list_arguments = arguments.split()
            return RenderResultListAction(self.get_action(arguments, list_arguments))

    def get_action(self, key_filter, list_arguments):
        connection = sqlite3.connect(_db_)
        items = []
        exists = 0
        tags_filter = ''
        args_wthout_tags = ''
        for arg in list_arguments:
            if arg[:3] == "tg:":
                tags_comma = arg[3:].split(',')
                for t in tags_comma:
                    tags_filter += t + " "
                tags_filter = tags_filter[:-1]
            else:
                args_wthout_tags += arg + " "

        if tags_filter:
            tags_filter_instr = ''
            for tag in tags_filter.split():
                tags_filter_instr += "instr(LOWER(tags), '" + tag.lower() + "') > 0 and "
            tags_filter_instr = tags_filter_instr[:-4]
    

            if args_wthout_tags:
                key_filter_string = ''
                for arg in args_wthout_tags.split():
                    key_filter_string += "instr(LOWER(key), '" + arg.lower() + "') > 0 and "
                key_filter_string = key_filter_string[:-4]

                statement = "SELECT key, value, tags from KV where {} and {}".format(tags_filter_instr, key_filter_string)
            else:
                statement = "SELECT key, value, tags from KV where {}".format(tags_filter_instr)
        else:
            key_filter_string = ''
            for arg in list_arguments:
                key_filter_string += "instr(LOWER(key), '" + arg.lower() + "') > 0 and "
            key_filter_string = key_filter_string[:-4]
            statement = "SELECT key, value, tags from KV where {}".format(key_filter_string)

        
        for row in connection.execute(statement):
            exists = 1
            key = row[0]
            value = row[1]
            tags = row[2]
            value_fix = value.strip().replace('$','\$').replace('"','\\"').replace('`','\\`') + '\n'
            script_action  = 'sleep 0.02 && echo -n "' + value_fix + '" | xclip -i -selection clipboard && sleep 0.02 && xdotool key --clearmodifiers ctrl+v &'
            item = ExtensionResultItem(
                icon=_icon_, 
                name="{}".format(key),
                description="{}".format(tags),
                on_alt_enter=RunScriptAction(script_action, []),
                on_enter=CopyToClipboardAction(value))
            items.append(item)

        if not exists:
            item = ExtensionResultItem(icon=_icon_, name=_name_)
            if key_filter == "":
                item._description = "It looks like you have nothing stored"
            else:
                item._description = "No VALUE for KEY: '{}'".format(key_filter)
            items.append(item)

        return items

class ItemEnterEventListener(EventListener):

    def on_event(self, event, extension):
        return RenderResultListAction(
            [ExtensionResultItem(
                icon=_icon_,
                name=_name_,
                description="Fist fill up the sqlite3 database $HOME/.kv.db with snippets")])


if __name__ == '__main__':
    KvExtension().run()
