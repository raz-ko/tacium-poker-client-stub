import json
from threading import Thread

import websocket
import _thread


class WebSocket:

    stop = False
    counter = 0

    @classmethod
    def on_message(cls, ws, message):
        text = message.decode("utf-8")
        prefix = cls.get_prefix(text)
        print(f"{prefix.ljust(40, ' ')}{text}")
        if 'over' in text.lower():
            cls.counter += 1
            if cls.counter >= 3:
                cls.stop = True

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
    def run(cls):
        # websocket.enableTrace(True)
        # url = "ws://echo.websocket.org/"
        # url = "ws://localhost:5286/dev/ws/"
        url = "ws://ec2-18-159-141-70.eu-central-1.compute.amazonaws.com/dev/ws"
        ws = websocket.WebSocketApp(url,
                                    on_open=cls.on_open,
                                    on_message=cls.on_message,
                                    on_error=cls.on_error,
                                    on_close=cls.on_close)

        t = Thread(target=cls.get_commands, args=(ws,))
        t.start()
        ws.run_forever()

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
                _sum = int(command[1:])
                data = ('{"msg": "hero_action","data": {"action": {"type": "Bet","sum": ' + str(_sum) + '}}}').encode("utf-8")
                ws.send(data, websocket.ABNF.OPCODE_BINARY)
                continue
            if command.lower().startswith('r'):
                _sum = int(command[1:])
                data = ('{"msg": "hero_action","data": {"action": {"type": "Raise","sum": ' + str(_sum) + '}}}').encode("utf-8")
                ws.send(data, websocket.ABNF.OPCODE_BINARY)
                continue


if __name__ == "__main__":
    print()
    print("Connecting to websocket server on ws://ec2-18-159-141-70.eu-central-1.compute.amazonaws.com")
    print()
    print()
    import time
    time.sleep(1)
    WebSocket.run()
