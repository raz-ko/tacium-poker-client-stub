import json
import time
from threading import Thread

import websocket
import _thread


class PrintingMode:
    FullData = "full_data"
    PlayerActions = "player_actions"
    GameView = "game_view"


class LoginMethod:
    Token = "token"
    Guest = "guest"
    NoLogin = "no_login"


class WebSocket:

    printing_mode = PrintingMode.FullData
    login_method = LoginMethod.NoLogin
    stop = False
    counter = 0
    actions = {1: "", 2: "", 3: ""}
    next_seat = 0
    hole_cards = {}
    community_cards = ""


    @classmethod
    def on_message(cls, ws, message):
        text = message.decode("utf-8")
        if cls.printing_mode == PrintingMode.FullData:
            prefix = cls.get_prefix(text)
            print(f"{prefix.ljust(40, ' ')}{text}")
        elif cls.printing_mode == PrintingMode.PlayerActions:
            change = cls.update_player_action(text)
            if change:
                print(f" {cls.n(1)} {cls.actions[1].ljust(10)}| {cls.n(2)} {cls.actions[2].ljust(10)}| {cls.n(3)} {cls.actions[3]}")
        elif cls.printing_mode == PrintingMode.GameView:
            game_view_text = cls.get_game_view_text(text)
            if game_view_text:
                print(game_view_text)
        if 'over' in text.lower():
            cls.counter += 1
            if cls.counter >= 30:
                cls.stop = True

    @classmethod
    def n(cls, seat):
        return '*' if seat == cls.next_seat else ' '

    @classmethod
    def on_error(cls, ws, error):
        print(error)
        cls.stop = True

    @classmethod
    def on_close(cls, ws, close_status_code, close_msg):
        print("### closed ###")
        cls.stop = True

    @classmethod
    def on_open(cls, ws):
        if cls.login_method == LoginMethod.Token:
            data = '{"msg": "login","data": {"token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJOYW1lIjoiIiwiVXNlcklkIjoiNjU5MjY5MzciLCJBZGRyZXNzIjoiMHhjZTZlNzEwMGIxYzU2NjJkZDc4YzRmNDZlOTdlYWViNWMwNWU4ODc5IiwianRpIjoiMDFkZjAzZWUtYzMyNS00NTUxLWE0ZTYtYzNhNGE0NmQ3MWI5IiwiaHR0cDovL3NjaGVtYXMubWljcm9zb2Z0LmNvbS93cy8yMDA4LzA2L2lkZW50aXR5L2NsYWltcy9yb2xlIjpbIlVzZXIiLCJBZG1pbiJdLCJleHAiOjE2NTA4NjI4NTksImlzcyI6Imh0dHA6Ly9sb2NhbGhvc3Q6NjE5NTUiLCJhdWQiOiJodHRwOi8vbG9jYWxob3N0OjQyMDAifQ.aVhkn59eKY8jNaBZvhpO_RD6FX0XY_Z77o5bP04V3R0"}}'.encode("utf-8")
            ws.send(data, websocket.ABNF.OPCODE_BINARY)
        elif cls.login_method == LoginMethod.Guest:
            data = '{"msg": "guest","data": {"daemon": true}}'.encode("utf-8")
            ws.send(data, websocket.ABNF.OPCODE_BINARY)
        def run(*args):
            # for i in range(3):
            #     time.sleep(1)
            #     ws.send("Hello %d" % i)
            while not cls.stop:
                time.sleep(1)
            ws.close()
            print("thread terminating...")
        # message = '{"msg": "login","data": {}}'
        # ws.send(message.encode("utf-8"))
        _thread.start_new_thread(run, ())

    @classmethod
    def get_prefix(cls, text: str):
        try:
            obj = json.loads(text)
            p = obj['data']
            if p['events'][0] == 'NewGame':
                return f" --- New Game: {p['game']['id']}"
            if p['events'][0] == 'CardsDealt':
                return f"{p['cards']['private'][0]['seat']}: [{p['cards']['private'][0]['cards'][0]}{p['cards']['private'][0]['cards'][1]}]"
            if p['events'][0] == 'FlopDealt':
                return f" - Flop: [{p['cards']['public']['flop'][0]}{p['cards']['public']['flop'][1]}{p['cards']['public']['flop'][2]}]"
            if p['events'][0] == 'TurnDealt':
                return f" - Turn: [{p['cards']['public']['turn'][0]}]"
            if p['events'][0] == 'RiverDealt':
                return f" - River: [{p['cards']['public']['river'][0]}]"
            if p['events'][0] == 'PlayerActed':
                if p['actions'][0]['action']['type'].lower() in ['raise', 'bet']:
                    return f"{p['actions'][0]['seat']}: {p['actions'][0]['action']['type']} ({p['actions'][0]['action']['sum']})"
                else:
                    return f"{p['actions'][0]['seat']}: {p['actions'][0]['action']['type']}"
            if p['events'][0] == 'Showdown':
                return f"{p['cards']['private'][0]['seat']}: showdowns [{p['cards']['private'][0]['cards'][0]}{p['cards']['private'][0]['cards'][1]}]"
            if p['events'][0] == 'Collect':
                return f"{p['chips']['collects'][0]['seat']}: collects {p['chips']['collects'][0]['sum']}"
            if p['events'][0] == 'GameOver':
                return f" --- Game Over"
            return ""
        except Exception as e:
            return ""

    @classmethod
    def update_player_action(cls, text: str) -> bool:
        try:
            obj = json.loads(text)
            p = obj['data']
            res = False
            if 'actions' in p:
                for action in p['actions']:
                    cls.actions[action['seat']] = action['action']['type']
                    res = True
            if 'players_state' in p:
                if 'next_player' in p['players_state']:
                    cls.next_seat = p['players_state']['next_player']['seat']
                    res = True
            return res
        except Exception as e:
            return False

    @classmethod
    def get_game_view_text(cls, text: str):
        try:
            obj = json.loads(text)
            p = obj['data']
            if p['events'][0] == 'NewGame':
                cls.hole_cards.clear()
                return f"=============================="
            if p['events'][0] == 'CardsDealt':
                cls.hole_cards[p['cards']['private'][0]["seat"]] = p['cards']['private'][0]["cards"][0] + p['cards']['private'][0]["cards"][1]
                if len(cls.hole_cards) == 3:
                    return f"                [{cls.hole_cards[1]}]         [{cls.hole_cards[2]}]        [{cls.hole_cards[3]}]"
                return ""
            if p['events'][0] == 'FlopDealt':
                cls.community_cards = p['cards']['public']['flop'][0] + p['cards']['public']['flop'][1] + p['cards']['public']['flop'][2]
                return f"[{cls.community_cards}]"
            if p['events'][0] == 'TurnDealt':
                cls.community_cards += p['cards']['public']['turn'][0]
                return f"[{cls.community_cards}]"
            if p['events'][0] == 'RiverDealt':
                cls.community_cards += p['cards']['public']['river'][0]
                return f"[{cls.community_cards}]"
            if p['events'][0] == 'PlayerActed':
                if p['actions'][0]['action']['type'].lower() in ['raise', 'bet']:
                    action = f"{p['actions'][0]['action']['type']} ({p['actions'][0]['action']['sum']})"
                else:
                    action = f"{p['actions'][0]['action']['type']}"
                seat = p['actions'][0]['seat']
                if seat == 1:
                    return f"            {cls.wrap(action, 15)}"
                if seat == 2:
                    return f"                           {cls.wrap(action, 15)}"
                if seat == 3:
                    return f"                                          {cls.wrap(action, 15)}"
                return ""
            if p['events'][0] == 'Showdown':
                return ""
            if p['events'][0] == 'Collect':
                return ""
            if p['events'][0] == 'GameOver':
                return " "
            return ""
        except Exception as e:
            return ""

    @staticmethod
    def wrap(s: str, l: int):
        if len(s) >= l:
            return s
        return ' '*((l-len(s))//2) + s + ' '*((l-len(s))+1//2)

    @classmethod
    def run(cls, server, printing_mode, login_method):
        # websocket.enableTrace(True)
        cls.printing_mode = printing_mode
        cls.login_method = login_method
        ws = websocket.WebSocketApp(server,
                                    on_open=cls.on_open,
                                    on_message=cls.on_message,
                                    on_error=cls.on_error,
                                    on_close=cls.on_close)

        t = Thread(target=cls.get_commands, args=(ws,))
        t.start()
        ws.run_forever(ping_timeout=2)

    @classmethod
    def get_commands(cls, ws):
        while True:
            print("press 't' for more time, 'e' to exit, 'f' to fold, 'f' to fold, 'x' to check, 'c' to call, 'b<sum>' to bet, 'r<sum>' to raise")
            command = input()
            if command.lower().startswith('t'):
                data = '{"msg": "request_time","data": {}}'.encode("utf-8")
                ws.send(data, websocket.ABNF.OPCODE_BINARY)
                continue
            if command.lower().startswith('e'):
                break
            if command.lower().startswith('f'):
                data = '{"msg": "hero_action","data": {"action": {"type": "Fold","sum": 0}}}'.encode("utf-8")
                ws.send(data, websocket.ABNF.OPCODE_BINARY)
                continue
            if command.lower().startswith('x'):
                data = '{"msg": "hero_action","data": {"action": {"type": "Check","sum": 0}}}'.encode("utf-8")
                ws.send(data, websocket.ABNF.OPCODE_BINARY)
                continue
            if command.lower().startswith('c'):
                data = '{"msg": "hero_action","data": {"action": {"type": "Call","sum": 0}}}'.encode("utf-8")
                ws.send(data, websocket.ABNF.OPCODE_BINARY)
                continue
            if command.lower().startswith('b'):
                _sum = float(command[1:])
                data = ('{"msg": "hero_action","data": {"action": {"type": "Bet","sum": ' + str(_sum) + '}}}').encode("utf-8")
                ws.send(data, websocket.ABNF.OPCODE_BINARY)
                continue
            if command.lower().startswith('r'):
                _sum = float(command[1:])
                data = ('{"msg": "hero_action","data": {"action": {"type": "Raise","sum": ' + str(_sum) + '}}}').encode("utf-8")
                ws.send(data, websocket.ABNF.OPCODE_BINARY)
                continue


def input_or_preset(preset: list) -> str:
    if not preset:
        return input()
    res = preset[0]
    preset.pop(0)
    print(f"\033[1;32m{res}\033[1;0m")
    return res


presets = {
    "player": ["10", "1", "2"],
    "table": ["9", "1", "2"]
}


servers = {
    "local dev": "ws://localhost:5212/dev/ws",
    "local game": "ws://localhost:5212/game/ws",
    "local watch": "ws://localhost:5212/watch/ws",
    "public": "ws://ec2-18-159-141-70.eu-central-1.compute.amazonaws.com/dev/ws",
    "public ssl": "wss://poker.tacium.com/dev/ws",
    "website": "wss://showcase.tacium.com/watch/ws",
    "beta": "wss://beta1.tacium.com/game/ws",
    "demo": "wss://demo.tacium.com/game/ws",
    "table": "ws://localhost:5212/ws/table?id=1",
    "player": "ws://localhost:5212/ws/player",
    "error": "ws://localhost:5212/gggg/ws",
    "dev player": "wss://poker.tacium.com/ws/player"
}


def run():
    print()
    print("Please select a preset: (Enter for no preset)")
    preset_items = list(presets.items())
    index = 1
    for name, preset in preset_items:
        print(f"{str(index).rjust(3)}. {name}")
        index += 1
    selected_preset = []
    i = input()
    index = 1
    for name, preset in preset_items:
        if i.strip().lower() == name.lower() or i.strip() == str(index):
            selected_preset = preset
            break
        index += 1

    print()
    print("Please select the desired server:")
    server_items = list(servers.items())
    index = 1
    for name, server in server_items:
        print(f"{str(index).rjust(3)}. {name}  ({server})")
        index += 1
    selected_server = 0
    i = input_or_preset(selected_preset)
    index = 1
    for name, _ in server_items:
        if i.strip().lower() == name.lower() or i.strip() == str(index):
            selected_server = index
            break
        index += 1
    if not selected_server:
        print("Not a valid server")
        exit()

    server = server_items[selected_server-1][1]
    print()
    print(f"Connecting to websocket server on {server}")
    print()
    print()
    print("Please select printing mode:")
    print(f"  1. Full data")
    print(f"  2. Player actions")
    print(f"  3. Game view")
    i = input_or_preset(selected_preset)
    printing_mode = ""
    if i.strip() == "1":
        printing_mode = PrintingMode.FullData
    elif i.strip() == "2":
        printing_mode = PrintingMode.PlayerActions
    elif i.strip() == "3":
        printing_mode = PrintingMode.GameView
    else:
        print("Not a valid printing mode")
        exit()

    print()
    print("Perform select login method:? (Enter for no login)")
    print(f"  1. Login with token")
    print(f"  2. Play as a guest")
    print(f"  3. No login")
    i = input_or_preset(selected_preset)
    if i.strip() == "1":
        login_method = LoginMethod.Token
    elif i.strip() == "2":
        login_method = LoginMethod.Guest
    else:
        login_method = LoginMethod.NoLogin

    WebSocket.run(server, printing_mode, login_method)


if __name__ == "__main__":
    run()
