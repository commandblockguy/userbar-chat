import threading
import irc.bot
from controller import StreamController

class Connection(threading.Thread):
	def __init__(self, controllers, username, server, channels):
		self.username = username
		self.shutdown_event = threading.Event()
		self.controllers = controllers
		self.server = server
		self.channels = channels
		super().__init__()

	def shutdown(self):
		self.shutdown_event.set()

	def run(self):
		def on_message(connection, event):
			username = event.source.split('!')[0]
			message = event.arguments[0]
			try:
				if username == 'saxjax' or username == 'saxjax_':
					username = message.split('<')[1].split('> ')[0]
					message = '> '.join(message.split('> ')[1:])
			except:
				pass
			print(username, message)
			for controller in self.controllers.values():
				controller.trigger_event((StreamController.EventType.MESSAGE, username, message))

		def on_welcome(connection, event):
			for channel in self.channels:
				self.bot.connection.join(channel)
			print('joined channels')

		def check_exit():
			if self.shutdown_event.is_set():
				print('shutting down irc')
				self.bot.die('Smell ya later nerds')

		self.bot = irc.bot.SingleServerIRCBot([irc.bot.ServerSpec(self.server)], self.username, 'test')
		self.bot.reactor.add_global_handler("pubmsg", on_message)
		self.bot.reactor.add_global_handler("privmsg", on_message)
		self.bot.reactor.add_global_handler("welcome", on_welcome)
		#self.bot.reactor.add_global_handler("all_events", lambda _, x: print(x))
		self.bot.reactor.scheduler.execute_every(period=3, func=check_exit)
		self.bot.start()
