import sqlite3
import os
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.RunScriptAction import RunScriptAction


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
            return RenderResultListAction(self.get_action(arguments))

    def get_action(self, key_filter):
        connection = sqlite3.connect(_db_)
        items = []
        exists = 0
        statement = "SELECT key, value, tags from KV where key like '%{}%' or tags like '%{}%'".format(key_filter, key_filter)
        for row in connection.execute(statement):
            exists = 1
            key = row[0]
            value = row[1]
            tags = row[2]
            script_action  = 'sleep 0.02 && echo -n "' + value + '" | xclip -i -selection clipboard && sleep 0.02 && xdotool key --clearmodifiers ctrl+v &'
            item = ExtensionResultItem(
                icon=_icon_, 
                name="{}".format(key),
                description="{}".format(tags),
                on_enter=RunScriptAction(script_action, []))
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
