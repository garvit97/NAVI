import vlc
import subprocess
import threading
class tts:
	class work(threading.Thread):
		def __init__(self,a,b,c):
			threading.Thread.__init__(self)
			self.s = a
			self.pla = b
			self.ins = c
		def run(self):
			subprocess.call('picospeaker -r -5 -o temp.wav "'+self.s+'"',shell=True)
			media = self.ins.media_new('temp.wav')
			self.pla.set_media(media)
			self.pla.play() 
	def __init__(self):
		self.instance = vlc.Instance()
		self.player = self.instance.media_player_new()
		self.player.set_equalizer(vlc.libvlc_audio_equalizer_new_from_preset(17))
	def speak(self,s):
		print s
		o = self.work(s,self.player,self.instance)
		o.start()
	def stop(self):
		self.player.stop()
	def wait(self):
		while 0<self.player.get_position()<0.9:
			pass
	
