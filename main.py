import datetime
from flask import Flask, Response, session, redirect, url_for
from controller import StreamController
from signal import signal, SIGINT
import irc_listener

app = Flask(__name__)

if __name__ == '__main__':
    signal(SIGINT, int_handler)
    get_app('test_key', 'testjax', 'irc.servercentral.net', ['#flood'])
    app.run()

def get_app(key, irc_user, irc_server, irc_channels):
    global irc
    app.secret_key = key
    app.config['SESSION_COOKIE_SAMESITE'] = "None"
    app.config['SESSION_COOKIE_SECURE'] = True
    irc = irc_listener.Connection(controllers, irc_user, irc_server, irc_channels)
    irc.start()
    return app

controllers = {}

@app.route('/')
def main_page():
    return '<html><body><a href="button"><img src="sax.png"></a></body></html>'

@app.route('/test')
def test():
    return 'test'

@app.route('/controllers')
def list_controllers():
    return ', '.join([str(x) for x in controllers.keys()])

@app.route('/button')
def button():
    if 'clicktime' in session:
        lasttime = session['clicktime']
        now = datetime.datetime.now()
        if now - lasttime < datetime.timedelta(seconds=5):
            toggle_mode()
        session['clicktime'] = now
    else:
        session['clicktime'] = datetime.datetime.now()

    if get_mode() == 'chat':
        event_type = StreamController.EventType.CLICK
        if 'controller' in session:
            controller = session['controller']
            if controller in controllers:
                controllers[controller].trigger_event((event_type, ))
                #controllers[controller].trigger_event((StreamController.EventType.MESSAGE, "username", "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Curabitur mollis porta urna non iaculis. Integer euismod tortor vitae interdum tincidunt. Sed ut dui tincidunt, mollis elit at, dictum tortor. Vestibulum accumsan, elit eu blandit ultricies, nisi nisl lobortis purus, sed dapibus metus risus eget orci."))
            else:
                print('unknown controller')
        else:
            print('no controller in session')
    return ''

def close(uuid):
    if uuid in controllers:
        controller = controllers.pop(uuid)
        controller.trigger_event((StreamController.EventType.CLOSE, ))
        print('client disconnected')

def get_mode():
    if 'mode' in session:
        return session['mode']
    else:
        session['mode'] = None
    return None

def toggle_mode():
    mode = get_mode()
    if mode == None:
        session['mode'] = 'chat'
    elif mode == 'chat':
        session['mode'] = None

@app.route('/sax.png')
def main():
    if get_mode() == 'chat':
        controller = StreamController(870, 44)
        controllers[controller.uuid] = controller
        if 'controller' in session:
            print('closing existing controller')
            close(session['controller'])
        session['controller'] = controller.uuid
        response = Response(controller.generate_stream(), mimetype='image/apng')
        print(response.call_on_close(lambda: close(controller.uuid)))
        return response
    return redirect(url_for('static', filename='default.png'))

def int_handler(a, b):
    irc.shutdown()
    raise KeyboardInterrupt
