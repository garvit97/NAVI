import time
import RPi.GPIO as pins
import numpy as np
import vlc
class input:
	def __init__(self):
		self.instance = vlc.Instance()
		self.player = self.instance.media_player_new()
		self.player.set_equalizer(vlc.libvlc_audio_equalizer_new_from_preset(17))
		self.r = 4
		self.c = 3 
		self.row = [16,20,21,22]
		self.col = [27,17,4]
		self.keys = [[[1,1],['a',3],['d',3]],[['g',3],['j',3],['m',3]],[['p',4],['t',3],['w',4]],[[2,1],[' ',1],[4,1]]]
		pins.setmode(pins.BCM)
		pins.setwarnings(0)
	def setout(self,set):
		for i in set:
			pins.setup(i,pins.OUT)
			pins.output(i,1)
	def setin(self,set):
		for i in set:
			pins.setup(i,pins.IN,pull_up_down=pins.PUD_DOWN)
	def key(self):
		o = np.zeros((self.r,self.c),dtype=bool)
		self.setout(self.col)
		self.setin(self.row)
		for i in range(self.r):
			if pins.input(self.row[i])==1:
				self.setin(self.col)
				pins.setup(self.row[i],pins.OUT)
				pins.output(self.row[i],1)
				for j in range(self.c):
					if pins.input(self.col[j])==1:
						o[i,j]=True
				pins.setup(self.row[i],pins.IN,pull_up_down=pins.PUD_DOWN)
				self.setout(self.col)
		return o		
	def pressed(self,a,b):
		check = np.zeros((self.r,self.c),dtype=bool)
		check[a,b]=True
		o=False
		if (self.key()==check).all():
			while (self.key()==check).all():
				time.sleep(0.01)
			if (self.key()==False).all():
				o = True
		return o

	def text(self):
		def pressedintime(a,b):
			curtime = time.time()*1000
			while time.time()*1000-curtime<=300:
				if self.pressed(a,b)==True:
					return True
				time.sleep(0.01)
			return False	
		exit = False
		words = ""
		while 1:
			for i in range(4):
				for j in range(3):
					time.sleep(0.01)
					if self.pressed(i,j)==True:
						self.player.stop()
						temp = self.keys[i][j][0]
						for m in range(1,self.keys[i][j][1]):
							if pressedintime(i,j)==True:
								temp=chr(ord(temp)+1)
								continue
							break
						if type(temp)!=int:
							words+=temp
							exit=False
						if temp==1:
							exit=False
							wait=True
							while wait:
								for m in range(4):
									for n in range(3):
										time.sleep(0.01)
										if self.pressed(m,n)==True:	
											temp = self.keys[m][n][0]
											if (type(temp)==str or temp == 1) and temp!=' ':
												wait=False
												words+=str(m*3+n+1)
												break
											elif temp==' ':
												wait=False
												words+=str(0)
												break
											else:
												wait=False
												break
						if temp == 2:
							if words=="":
								exit=True
								print "Press Enter to exit"
								media =self.instance.media_new('audios/a1.wav')
								self.player.set_media(media)
								self.player.play()							
								break
							words = words[0:len(words)-1]
							print "delete"
							media =self.instance.media_new('audios/a5.wav')
							self.player.set_media(media)
							self.player.play()
							break
						elif temp == 4:
							if exit==True:
								return words
							if words == "":
								print "Nothing typed to save"
								media =self.instance.media_new('audios/a2.wav')
								self.player.set_media(media)
								self.player.play()
								break
							if len(words)>0:
								print "Press again to save"
								media =self.instance.media_new('audios/a3.wav')
								self.player.set_media(media)
								self.player.play()
								exit = True
								break
						else:
							if words[-1]==' ':
								print "Space"
								media =self.instance.media_new('audios/a4.wav')
								self.player.set_media(media)
								self.player.play()
							else:
								print words[-1].upper()
								media =self.instance.media_new('audios/'+words[-1].upper()+'.wav')
								self.player.set_media(media)
								self.player.play()







		
