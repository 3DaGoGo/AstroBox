# coding=utf-8
__author__ = "AstroPrint Product Team <product@astroprint.com>"
__license__ = 'GNU Affero General Public License http://www.gnu.org/licenses/agpl.html'
__copyright__ = "Copyright (C) 2016-2017 3DaGoGo, Inc - Released under terms of the AGPLv3 License"

from octoprint.events import eventManager, Events

from astroprint.plugin.providers.printer_comms import PrinterState

class SystemListener(object):
	def __init__(self, weakRefBoxRouter):
		self._weakRefBoxRouter = weakRefBoxRouter

		em = eventManager()

		#register for print_capture events
		em.subscribe(Events.CAPTURE_INFO_CHANGED, self._onCaptureInfoChanged)
		em.subscribe(Events.CLOUD_DOWNLOAD, self._onDownload)
		em.subscribe(Events.FILAMENT_CHANGE, self._filamentChanged)

	def cleanup(self):
		em = eventManager()

		em.unsubscribe(Events.CAPTURE_INFO_CHANGED, self._onCaptureInfoChanged)
		em.unsubscribe(Events.CLOUD_DOWNLOAD, self._onDownload)

	def sendHistoryData(self, data):
		pass

	def addTemperature(self, data):
		payload = {}

		if data:
			for key in sorted(data.keys()):
				if key == 'bed' or key[:4] == 'tool':
					payload[key] = data[key]

		router = self._weakRefBoxRouter()
		if router:
			router.broadcastEvent('temp_update', payload)

	def addLog(self, data):
		pass

	def addMessage(self, data):
		pass

	def sendCurrentData(self, data):
		state = data['state']
		flags = state['flags']

		printing = flags['printing'] or flags['paused']
		operational = flags['operational']

		payload = {
			'operational': operational,
			'printing': printing,
			'ready_to_print': operational and not printing and state['state'] != PrinterState.STATE_NOT_READY_TO_PRINT,
			'paused': flags['paused'],
			'camera': flags['camera'],
			'heatingUp': flags['heatingUp'],
			'state': state['text'].lower(),
			'tool': data['tool']
		}

		router = self._weakRefBoxRouter()
		if router:
			router.broadcastEvent('status_update', payload)

			if payload['printing']:
				router.broadcastEvent('printing_progress', data['progress'])

			else:
				router.broadcastEvent('printing_progress', None)

	def sendEvent(self, type):
		pass

	def sendFeedbackCommandOutput(self, name, output):
		pass

	def _filamentChanged(self, event, payload):
		router = self._weakRefBoxRouter()
		if router:
			router.broadcastEvent('filament_update', payload)

	## Additional Event listeners

	def _onCaptureInfoChanged(self, event, payload):
		router = self._weakRefBoxRouter()
		if router:
			router.broadcastEvent('print_capture', payload)

	def _onDownload(self, event, payload):
		data = {
			'id': payload['id'],
			'selected': False
		}

		if payload['type'] == 'error':
			data['error'] = True
			data['message'] = payload['reason'] if 'reason' in payload else 'Problem downloading'

		elif payload['type'] == 'cancelled':
			data['cancelled'] = True

		else:
			data['progress'] = 100 if payload['type'] == 'success' else payload['progress']

		router = self._weakRefBoxRouter()
		if router:
			router.broadcastEvent('print_file_download', data)
