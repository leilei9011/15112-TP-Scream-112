from cmu_112_graphics import *
from tkinter import *
import webrtcvad
import collections
import sys
import signal
import pyaudio
from PIL import Image 
import random
from array import array
import time
import math
import struct
import aubio
import numpy as num
from os import path
from pygame import mixer 

#cite code
#https://github.com/wangshub/python-vad
#https://github.com/kidscancode/pygame_tutorials/tree/master/platform/part%208
#Animation framework by David Kosbie
#music by MorningLightMusic

highestScore = "highestscore.txt"


class SplashScreenMode(Mode):
    def appStarted(mode):
        cursor = Cursor(mode)
        mode.cursor = cursor.sprite
        mode.mouseX = mode.width//2
        mode.mouseY = mode.height//2
        
        mode.screen = mode.loadImage("screen.png")

        startButton = mode.loadImage("startButton.gif")
        mode.startButton = mode.scaleImage(startButton, 1/4)
        mode.startButtonCX = mode.width//2
        mode.startButtonCY = mode.height*4//5
        mode.startButtonW = mode.startButton.size[0]
        mode.startButtonH = mode.startButton.size[1]

        mode.playerSprite = mode.loadImage("ezgif.com-apng-to-gif.gif")
        mode.player = Player2(mode, mode.playerSprite)

        #get past highest score fro  highestscore.txt
        SplashScreenMode.loadData(mode) 
    
    def loadData(mode):
        mode.dir = path.dirname(__file__)
        with open(path.join(mode.dir, highestScore), 'r+') as f:
            try:
                mode.highestScore = int(f.read())
            except: 
                mode.highestScore = 0

    def timerFired(mode):
        mode.player.spriteCounter = ((1+mode.player.spriteCounter)% 
        len(mode.player.sprites))

    def mousePressed(mode, event):
        if (abs(event.x - mode.startButtonCX) < mode.startButtonW//2
            and abs(event.y - mode.startButtonCY) < mode.startButtonH//2):
            mode.app.setActiveMode(mode.app.helpMode)

    def mouseMoved(mode, event):
        mode.mouseX = event.x
        mode.mouseY = event.y
    
    def getCachedPhotoImage(mode, image):
        if ('cachedPhotoImage' not in image.__dict__):
            image.cachedPhotoImage = ImageTk.PhotoImage(image)
        return image.cachedPhotoImage
    
    def redrawAll(mode, canvas):
        canvas.create_image(mode.width//2, mode.height*3//5, 
        image = ImageTk.PhotoImage(mode.screen))

        canvas.create_image(mode.startButtonCX, mode.startButtonCY, 
        image = ImageTk.PhotoImage(mode.startButton))

        sprite = mode.player.sprites[mode.player.spriteCounter]
        sprite = mode.scaleImage(sprite, 1.5)
        canvas.create_image(mode.width//2, mode.height//2 + 50, 
        image= ImageTk.PhotoImage(sprite))

        canvas.create_text(mode.width//2, mode.height//3 + 20, 
        text = f'BEST SCORE  {mode.highestScore}', 
                    font = "FreeMono 36 bold", 
                    fill = "light grey")

        canvas.create_image(mode.mouseX, mode.mouseY, 
        image = mode.cursor)

class startVoiceDemo(Mode):

    def appStarted(mode):
        mode.start = 0
        mic = mode.loadImage("microphone.gif")
        mode.mic = mode.scaleImage(mic, 1/2)
    
    def keyPressed(mode, event):
        if event.key == "s":
            mode.app.setActiveMode(mode.app.voiceDemoMode)

    def redrawAll(mode, canvas):
        canvas.create_rectangle(0,0, mode.width, mode.height, fill = "light blue")
        canvas.create_text(mode.width//3, mode.height//2, 
                            text = """
                            Press "s" to start voice detection test.
                            Please speak in a volume 
                            that you are most comfortable with
                            for five seconds.

                            Thank you!
                            """,
                            font = "FreeMono 25 bold", fill = "white")
        canvas.create_image(mode.width*3//4, mode.height//2, 
                            image = ImageTk.PhotoImage(mode.mic))

class VoiceDemoMode(Mode):

    def appStarted(mode):
        mode.message = 6
        mode.volumeSet = set()
        mode.timerDelay = 5

        mic = mode.loadImage("microphone.gif")
        mode.mic = mode.scaleImage(mic, 1/2)
    
    def timerFired(mode):

        if mode.message == 0:
            return 
        data = VoiceDemoMode.voiceDetection(mode, sys.argv)
        mode.message -= 1

        maxVolume = max(mode.volumeSet)
        mode.maxVolume = float(maxVolume) * (10**4) 
        #return a non decimal maxVolume number to improve UI

        mode.restart = False

    def keyPressed(mode, event):
        if event.key == "Enter":
            mode.threshold = 0
            mode.app.setActiveMode(mode.app.gameMode)

    def voiceDetection(mode, args):
        BUFFER_SIZE             = 2048
        CHANNELS                = 1
        FORMAT                  = pyaudio.paFloat32
        METHOD                  = "default"
        SAMPLE_RATE             = 44100
        HOP_SIZE                = BUFFER_SIZE//2
        PERIOD_SIZE_IN_FRAME    = HOP_SIZE

        leave = False
        gotVoice = False

        # Initiating PyAudio object.
        pA = pyaudio.PyAudio()
        # Open the microphone stream.
        mic = pA.open(format=FORMAT, channels=CHANNELS,
            rate=SAMPLE_RATE, input=True,
            frames_per_buffer=PERIOD_SIZE_IN_FRAME)

        while not leave:
            StartTime = time.time()

            while not gotVoice and not leave:
                TimeUsed = time.time() - StartTime
                # Always listening to the microphone.
                data = mic.read(PERIOD_SIZE_IN_FRAME)
                # Convert into number that Aubio understand.
                samples = num.fromstring(data,
                    dtype=aubio.float_type)
                # Compute the energy (volume)
                # of the current frame.
                volume = num.sum(samples**2)/len(samples)
                # Format the volume output so it only
                # displays at most six numbers behind 0.
                volume = "{:6f}".format(volume)
                #the volume.
    
                mode.volumeSet.add(volume)

                if TimeUsed > 1: #escape loop after 1 second
                    gotVoice = True
                    leave = True
        
        mic.stop_stream()

    def mousePressed(mode, event):
        if mode.restart:
            VoiceDemoMode.appStarted(mode)
        if mode.message == 0:
            mode.app.setActiveMode(mode.app.gameMode)

    def redrawAll(mode, canvas):
        canvas.create_rectangle(0,0, mode.width, mode.height, 
                                fill = "darkslategray")
        
        if mode.message != 0:
            if mode.message == 6:
                message = "Starts"
            else:
                message = mode.message #count down number

            canvas.create_text(mode.width//2, mode.height*2//5, 
                            text = message,
                            font = "FreeMono 35 bold", fill = "light grey")
                
            canvas.create_text(mode.width//2, mode.height//2, 
                                text = "Detecting...", 
                                font = "FreeMono 35 bold", fill = "light grey")

        else:

            if int(mode.maxVolume) == 0:
                canvas.create_text(mode.width//2, mode.height//2, 
                            text = f'''
                            Voice not detected! Press mouse to restart detection

                            Volume Threshold: 0
                            ''',
                            font = "FreeMono 25 bold", fill = "light grey")
                mode.restart = True

            else:

                canvas.create_text(mode.width//2, mode.height//2, 
                                text = f'''
                                Voice detected! Press mouse to start the game

                                Volume Threshold: {mode.maxVolume}
                                ''',
                                font = "FreeMono 25 bold", fill = "light grey")
                mode.restart = False

class Player2(object):
    def __init__(self, mode, sprite):
        self.mode = mode
        self.spriteCounter = 0
        self.sprites = []
        self.spritestrip = sprite

        self.imageRowNum = 10 # num of stripped images in each row
        self.imageRow = 2 
        self.imageNum = 18  #num of stripped images in total

        self.cx = self.mode.width//2
        self.cy =  self.mode.height - 100
        self.startY =  self.mode.height - 100

        self.spriteWidth = 914
        self.spriteHeight = 205
        self.itemWidth = 40 #stripped image width
        self.itemHeight = 70 #stripped image height


        for i in range(self.imageNum): #crop sprite sheet

            if i < self.imageRowNum -1 : #9
                if i < self.imageNum//2 - 1: #8
                    cellWidth = 86
                else:
                    cellWidth = 101

                sprite = self.spritestrip.crop(((
                cellWidth*i, 
                0, 
                cellWidth*(i+1),
                self.spriteHeight//2)))
                self.sprites.append(sprite)
            
            else:
                if i == self.imageRowNum -1 : continue #9

                spriteChange = self.imageNum - 4 #14
                if i < spriteChange:
                    cellWidth = 110
                else:
                    cellWidth = 87
                
                num = i%10

                sprite = self.spritestrip.crop((
                65+(cellWidth*(num)), 
                self.spriteHeight//2, 
                65+cellWidth*((num+1)),
                self.spriteHeight))
                self.sprites.append(sprite)

    def draw(self, canvas):
 
        sprite = self.sprites[self.spriteCounter]
        sprite = self.mode.getCachedPhotoImage(sprite)
        canvas.create_image(self.cx, self.cy, 
        image= sprite)

class Rocks(object):
    def __init__(self, mode, cx, sprite):
        self.mode = mode
        self.cx = cx
        self.cy = self.mode.player.startY

        self.sprite = sprite

        self.spriteWidth = 134
        self.spriteHeight = 119
        self.itemWidth = self.sprite.size[0]
        self.itemHeight = self.sprite.size[1]

    def draw(self, canvas):
        cx = self.cx - self.mode.scrollX
        sprite = self.mode.getCachedPhotoImage(self.sprite)
        canvas.create_image(cx, self.cy, 
        image= sprite)  

class Coins(object): 

    def __init__(self, mode, cx, cy, sprite):
        self.mode = mode
        self.cx = cx
        self.cy = cy

        self.spritestrip = sprite
        self.coinSprites = []
        self.coinSpriteCounter = 0

        self.spriteWidth = self.spritestrip.size[0]
        self.spriteHeight = self.spritestrip.size[1]
        self.itemWidth = self.spriteWidth//6
        self.itemHeight = self.spriteHeight

        for i in range(6):
            sprite = self.spritestrip.crop((
                (self.itemWidth*(i)), 
                0, 
                self.itemWidth*((i+1)),
                self.spriteHeight))
            self.coinSprites.append(sprite)
    
    def draw(self, canvas):
        cx = self.cx - self.mode.scrollX
        sprite = self.coinSprites[self.coinSpriteCounter]
        sprite = self.mode.getCachedPhotoImage(sprite)
        canvas.create_image(cx, self.cy,
            image = sprite)

class Platforms(object):
    def __init__(self, mode, cx, cy, sprite):
        self.mode = mode
        self.cx = cx
        self.cy = cy

        self.sprite = sprite

        self.itemWidth = self.sprite.size[0]
        self.itemHeight = self.sprite.size[1]
    
    def draw(self, canvas):
        cx = self.cx - self.mode.scrollX
        sprite = self.mode.getCachedPhotoImage(self.sprite)
        canvas.create_image(cx, self.cy, 
        image= sprite)  

class Magnet(object):
    def __init__(self, mode, cx, cy):
        self.mode = mode
        self.cx = cx
        self.cy = cy
        sprite = mode.loadImage("magnet.gif")
        self.sprite = mode.scaleImage(sprite, 1/8)

        self.itemWidth = self.sprite.size[0]
        self.itemHeight = self.sprite.size[1]
    
    def draw(self, canvas):
        cx = self.cx - self.mode.scrollX
        sprite = self.mode.getCachedPhotoImage(self.sprite)
        canvas.create_image(cx, self.cy, 
        image= sprite)  

class Dragon(object):
    def __init__(self, mode, sprite):
        self.mode = mode
        self.cx = mode.width//2 + self.mode.scrollX + mode.width*2
        self.cy = self.mode.height//2

        self.spritestrip = sprite

        self.spriteWidth = self.spritestrip.size[0]
        self.spriteHeight = self.spritestrip.size[1]
        self.itemWidth = self.spriteWidth//4

        self.dragonSprites = []
        self.dragonSpriteCounter = 0

        for i in range(4):
            sprite = self.spritestrip.crop((
                (self.itemWidth*(i)), 
                0, 
                self.itemWidth*((i+1)),
                self.spriteHeight))
            self.dragonSprites.append(sprite)
    
    def draw(self, canvas):
        cx = self.cx - self.mode.scrollX
        sprite = self.dragonSprites[self.dragonSpriteCounter]
        sprite = self.mode.getCachedPhotoImage(sprite)
        canvas.create_image(cx, self.cy,
            image = sprite)

class Fire(object):

    def __init__(self, mode, cx, cy, sprite):
        self.mode = mode
        self.cx = cx
        self.cy = cy

        self.spritestrip = sprite

        self.itemWidth = self.spritestrip.size[0]
        self.itemHeight = self.spritestrip.size[1]
    
    def draw(self, canvas):
        cx = self.cx - self.mode.scrollX
        sprite = self.mode.getCachedPhotoImage(self.spritestrip)
        canvas.create_image(cx, self.cy,
            image = sprite)

class Cursor(object):
    def __init__(self, mode):
        self.mode = mode
        sprite = self.mode.loadImage("cursor.gif")
        sprite = self.mode.scaleImage(sprite, 1/7)
        self.sprite = self.mode.getCachedPhotoImage(sprite)
    
class Dots(object):
    def __init__(self, mode, cx, cy, color, angle, r):
        self.mode = mode
        self.cx = cx 
        self.cy = cy
        self.color = color
        self.angle = angle
        self.r = r
        
    def draw(self, canvas):
        r = random.choice([3,5,8,10])
        canvas.create_oval(self.cx-r, self.cy-r, 
                        self.cx+r, self.cy+r,
                        fill = self.color)

class GameMode(Mode):

    FORMAT = pyaudio.paInt16 #audio bit depth (usually 16)
    CHANNELS = 1 #number of audio channels
    RATE = 16000 #sampling frequency
    CHUNK_DURATION_MS = 30 #supports 10, 20 and 30 (ms)
    PADDING_DURATION_MS = 100  # 1 sec jugement
    CHUNK_SIZE = int(RATE * CHUNK_DURATION_MS/1000) #chunk to read/length of the audio buffer
    CHUNK_BYTES = CHUNK_SIZE * 2
    NUM_PADDING_CHUNKS = int(PADDING_DURATION_MS / CHUNK_DURATION_MS)
    NUM_WINDOW_CHUNKS = int(400 / CHUNK_DURATION_MS) 
    NUM_WINDOW_CHUNKS_END = NUM_WINDOW_CHUNKS * 2
    SHORT_NORMALIZE = (1.0/32768.0)

    START_OFFSET = int(NUM_WINDOW_CHUNKS * CHUNK_DURATION_MS * 0.5 * RATE)

    """
    a python interface to the WebRTC Voice Activity Detector (VAD)
    A VAD classifies a piece of audio data as being voiced or unvoiced.
    Aggressiveness mode is set to 1 (0 = least aggressive about filtering out 
    non-speech, 3 = most aggressive)
    """
    vad = webrtcvad.Vad(3) 

    def appStarted(mode):

        GameMode.createSprite(mode)

        GameMode.loadData(mode)

        mode.cursor = Cursor(mode)
        mode.mouseX = mode.width//2
        mode.mouseY = mode.height//2

        mode.player = Player2(mode, mode.playerSprite)
        mode.scrollX = 0
        mode.speed = 30

        mode.pa = pyaudio.PyAudio() #Create an instance of PyAudio
        mode.stream = stream = mode.pa.open(format=GameMode.FORMAT, 
                 channels=GameMode.CHANNELS, 
                 rate=GameMode.RATE,
                 input=True, #use the stream as input
                 start=True, #start the stream directly after opening
                 frames_per_buffer=GameMode.CHUNK_SIZE) 

        mode.gameOver = False
        mode.score = 0

        mode.rocks = []

        mode.coins = [[]]
        for i in range(7):
            c = Coins(mode, mode.player.cx + (40*i), mode.height-100, mode.coinSprite)
            mode.coins[0].append(c)
        mode.newCoins = [[] for num in range(len(mode.coins))]
        
        mode.platforms = [[]]

        mode.dragons = []
        mode.direction = 15
        mode.dragonMode = False
        mode.dragonTime = 50

        mode.fire = []

        mode.dots = []
        mode.color = ["light yellow", "DodgerBlue4", "steelblue", 
                    "darkslategray"]
        mode.prevActivity = False

        mode.magnetTime = 100
        mode.magnets = []
        mode.magnetModeTime = 100
        mode.magnetMode = False

        mode.threshold = mode.app.voiceDemoMode.maxVolume
        mode.rms_value = 0

        mode.timerDelay = 100
        mode.stop = False

    def loadData(mode):
        mode.dir = path.dirname(__file__)
        with open(path.join(mode.dir, highestScore), 'r+') as f:
            try:
                mode.highestScore = int(f.read())
            except: 
                mode.highestScore = 0

    def createSprite(mode):

        mode.playerSprite = mode.loadImage("ezgif.com-apng-to-gif.gif")

        rockSprite = mode.loadImage("rock.gif")
        mode.rockSprite = mode.scaleImage(rockSprite, 1/7)

        coinSprite = mode.loadImage("coin2.gif")
        mode.coinSprite = mode.scaleImage(coinSprite, 1/2)

        mode.platformSprite = mode.loadImage("platform.gif")

        dragonSprite = mode.loadImage("dragon.gif")
        mode.dragonSprite = dragonSprite.transpose(Image.FLIP_LEFT_RIGHT)

        fireSprite = mode.loadImage("fire.gif")
        mode.fireSprite = mode.scaleImage(fireSprite, 1/8)

        background = mode.loadImage("background.png")
        mode.background = mode.getCachedPhotoImage(background)

        question = mode.loadImage("question.gif")
        question = mode.scaleImage(question, 1/8)
        mode.question = mode.getCachedPhotoImage(question)
        mode.questionW, mode.questionH = question.size[0], question.size[1]
        mode.questionCX, mode.questionCY = mode.width//18, mode.height//15

        play = mode.loadImage("play.gif")
        play = mode.scaleImage(play, 1/6)
        mode.play = mode.getCachedPhotoImage(play)
        mode.playW, mode.playH = play.size[0], play.size[1]
        mode.playCX, mode.playCY = mode.width*2//18, mode.height//15

        plus = mode.loadImage("plus.gif")
        plus = mode.scaleImage(plus, 1/2)
        mode.plus = mode.getCachedPhotoImage(plus)
        mode.plusW, mode.plusH = plus.size[0], plus.size[1]
        mode.plusCX, mode.plusCY = mode.width*3//18, mode.height//15

        minus = mode.loadImage("minus.gif")
        minus = mode.scaleImage(minus, 1/2)
        mode.minus = mode.getCachedPhotoImage(minus)
        mode.minusW, mode.minusH = minus.size[0], minus.size[1]
        mode.minusCX, mode.minusCY = mode.width*4//18, mode.height//15

        mode.gameOverSprite = mode.loadImage("gameover.gif")
        mode.gameOverCX = mode.width//2
        mode.gameOverCY = mode.height//2
        mode.gameOverW = mode.gameOverSprite.size[0]
        mode.gameOverH = mode.gameOverSprite.size[1]

    def mouseMoved(mode, event):
        mode.mouseX = event.x
        mode.mouseY = event.y

    def mousePressed(mode, event): 

        #click screen to restart game
        if (mode.gameOver
            and abs(event.x - mode.gameOverCX) < mode.gameOverW//2
            and abs(event.y - mode.gameOverCY) < mode.gameOverH//2):
            GameMode.appStarted(mode)

        #click plus/minus sign to adjust minimum volume threshold
        elif (mode.plusCX - mode.plusW < event.x < mode.plusCX + mode.plusW
            and mode.plusCY - mode.plusH < event.y < mode.plusCY + mode.plusH):
            mode.threshold += 5
        elif (mode.minusCX - mode.minusW < event.x < mode.minusCX + mode.minusW
            and mode.minusCY - mode.minusH < event.y < mode.minusCY + mode.minusH):
            mode.threshold -= 5
            if mode.threshold < 0:
                mode.threshold = 0
        
        #clickplay button to restart game
        elif (mode.playCX - mode.playW < event.x < mode.playCX + mode.playW
            and mode.playCY - mode.playH < event.y < mode.playCY + mode.playH):
            GameMode.appStarted(mode)

        #click question button to go to help mode
        elif (mode.questionCX - mode.questionW < event.x < mode.questionCX + mode.questionW
            and mode.questionCY - mode.questionH < event.y < mode.questionCY + mode.questionH):
            mode.app.setActiveMode(mode.app.helpMode2)

    def keyPressed(mode, event):

        if event.key == "Space":
            mode.stop = not(mode.stop)
            mode.dragonTime = 0
            mode.magnetTime = 0
        elif event.key == "t":
            mode.dragonTime = 0
            mode.magnetTime = 0
        elif event.key == "s":
            mode.magnetMode = not(mode.magnetMode)
        elif event.key == "Down":
            mode.threshold -= 5
        elif event.key == "Up":
            mode.threshold += 5
        
        
    def timerFired(mode):

        if mode.gameOver or mode.stop: 
            return

        mode.player.spriteCounter = ((1+mode.player.spriteCounter)% 
        len(mode.player.sprites))

        for d in mode.dragons:
            d.dragonSpriteCounter = ((1+d.dragonSpriteCounter)% 
                len(d.dragonSprites))

        for coin in mode.coins:
            for c in coin:
                c.coinSpriteCounter = ((1+c.coinSpriteCounter)% 
                len(c.coinSprites))

        if mode.dragonTime > 0:
            if mode.dragonTime > 100: #dragonFire for 5s
                GameMode.dragonFire(mode)  
                mode.dragonMode = True
            elif mode.dragonTime == 60: #dragon leaves
                d = mode.dragons[0]
                if ((d.cx - mode.scrollX + d.itemWidth//2) < 0): #dragon dissapears out of screen
                                                                 #pop dragon out of the list
                    mode.dragons.pop(0)
                    mode.fire = []
                    mode.dragonTime -= 1
                    mode.dragonMode = False
            else:
                mode.dragonTime -= 1
        else: #new dragon for every 15s
            GameMode.makeDragon(mode)
            mode.dragonTime = 150
        
        GameMode.makeCoins(mode)
        if not mode.dragonMode: #no obstacles when dragon mode is on
            GameMode.makeRocks(mode)
            GameMode.makePlatforms(mode)
        
        GameMode.checkPlayerCollision(mode)

        GameMode.detectVoice(mode)

        GameMode.moveDots(mode)

        if mode.magnetTime > 0: 

            #pop magnet out of list when it disappears out of screen
            if mode.magnets != []: 
                GameMode.moveMagnet(mode)
                m = mode.magnets[0]
                if (m.cx + - mode.scrollX + m.itemWidth//2) < 0:
                    mode.magnets.pop(0)
            mode.magnetTime -= 1
        else: #make new magnet every 30 seconds
            GameMode.makeMagnet(mode)
            mode.magnetTime = 300
        
        if mode.magnetMode: 
            if mode.magnetModeTime > 0:
                mode.magnetModeTime -= 1
                GameMode.attractCoins(mode)
            else:
                mode.magnetMode = False
                mode.magnetModeTime = 100 #magnet mode last for 10s
                
    def moveMagnet(mode): #magnet move up and down
        m = mode.magnets[0]
        m.cy += mode.direction
        if (GameMode.checkPlatformCollision(mode, m) or GameMode.checkRockCollision(mode, m)
            or not((mode.height//4 <= m.cy <= mode.player.startY))):
            mode.direction = (-mode.direction)
        
    def moveDots(mode): #dots move outwards overtime
        for d in mode.dots:
            d.r += 10
            d.cx = mode.width//2 + d.r*math.cos(math.radians(d.angle))
            d.cy = mode.height//2 - d.r*math.sin(math.radians(d.angle))

    def makeMagnet(mode): #make new magnets
        if len(mode.magnets) < 1:
            while True:
                x = random.randrange(mode.width) + mode.scrollX + mode.width
                y = (random.randrange(mode.height//4, mode.player.startY))

                m = Magnet(mode, x, y)
                if not GameMode.checkItemCollision(mode, m):
                    mode.magnets.append(m)
                    return

    def makeDots(mode): #make new dots

        numDot = int(mode.rms_value//2) 
        

        if mode.dots != []:
            for d in mode.dots:
                if d.cx < 0 or d.cx > mode.width or d.cy < 0 or d.cy > mode.height:
                    mode.dots.remove(d) 

        if numDot != 0:

            angle = 360/numDot
            randomAngle = random.randrange(0, 90)
            
            r = 20
            
            for num in range(numDot):
                newAngle = num*angle + randomAngle
              
                color = mode.color[random.randrange(4)]
                
                x = mode.width//2 + r*math.cos(math.radians(newAngle))
                y = mode.height//2 + r*math.sin(math.radians(newAngle))
                
                d = Dots(mode,
                x, 
                y, 
                color, 
                newAngle, 
                r)

                mode.dots.append(d)

    def attractCoins(mode): #player attracts coin when magnet mode is on

        speed = 20
        for coin in mode.coins:
            for c in coin:
                
                cx = c.cx - mode.scrollX
                print(cx)
                if 0 < cx < mode.width:

                    widthDiff = abs(cx-mode.player.cx)
                    heightDiff = abs(c.cy-mode.player.cy)
                    r = (widthDiff**2 + heightDiff**2)**0.5

                    newR = r - speed
                    c.cx = mode.player.cx + newR*(widthDiff/r) + mode.scrollX
                    c.cy = mode.player.cy - newR*(heightDiff/r)

    def makeDragon(mode): #make new dragons
        if len(mode.dragons) < 1:
            dragon = Dragon(mode, mode.dragonSprite)
            mode.dragons.append(dragon)
    
    def dragonFire(mode): #dragon shoots fire

        dragon = mode.dragons[0]

        #starts firing only when dragon appears on screen
        if (dragon.cx - mode.scrollX) <= mode.width*6//7: 
            dragon.cx = mode.width*6//7 + mode.scrollX
            mode.dragonTime -= 1

        dragon.cy = mode.player.cy - 10
        
        fireTime = 8 #shoots fire every 4/5 second
        if mode.dragonTime % fireTime == 0:
            f = Fire(mode, dragon.cx, dragon.cy, mode.fireSprite)
            mode.fire.append(f)
        for fire in mode.fire:
            fire.cx -= 10

    def makePlatforms(mode): #make new platforms

        platformWidth = 70
        if mode.platforms!= []: #remove platform when platform disappears on screen
            if (len(mode.platforms[0]) == 0 
                or (mode.platforms[0][-1].cx 
                - mode.scrollX 
                + mode.platforms[0][-1].itemWidth//2 < 0)):
                    mode.platforms = mode.platforms[1:]

        platformNumLimit = 3
        if(len(mode.platforms) < platformNumLimit): #controll the number of platform elem under two
            while True:
                x = random.randrange(mode.width) + mode.scrollX + mode.width
                y = (random.randrange(mode.height//3, mode.height//2))

                num = random.randrange(1, 5) #num of platforms in each platform elem
                newPlatforms = []

                for i in range(num):
                    platformX = x + (platformWidth*i)
                    p = Platforms(mode, platformX, y, mode.platformSprite)

                    result = GameMode.checkItemCollision(mode, p)
                    if not result:
                        newPlatforms.append(p)
       
                    else: 
                        return
                mode.platforms.append(newPlatforms)
                return

    def makeRocks(mode): #make new rocks
        for rocks in mode.rocks:
            #remove rock when rock disappears on screen
            if (rocks.cx - mode.scrollX + rocks.spriteWidth//2) < 0: 
                mode.rocks.remove(rocks)

        rocksNumLimit = 5 #controll the number of rock elem under four
        if len(mode.rocks) < rocksNumLimit:
            while True:
                num = random.randrange(mode.width)
                x = num + mode.scrollX + mode.width
                r = Rocks(mode, x, mode.rockSprite)

                result = GameMode.checkItemCollision(mode, r)
                if not result:
                    mode.rocks.append(r)
                return

    def makeCoins(mode):  #make new coins

        coinWidth = 42

        if mode.coins!= []: #remove coin when coin disappears on screen
            if (len(mode.coins[0]) == 0 
                or (mode.coins[0][-1].cx 
                - mode.scrollX 
                + mode.coins[0][-1].itemWidth//2) < 0):

                    mode.coins = mode.coins[1:]

        coinNumLimit = 3
        if(len(mode.coins) < coinNumLimit): #controll the number of rock elem under four
            while True:
                x = random.randrange(mode.width) + mode.scrollX + mode.width
                
                y1 = (random.randrange(mode.app.height//3, mode.player.startY))
                y2 = mode.player.startY
                y = random.choice([y1, y2])

                num = random.randrange(3,10) #random number of coins in each coin elem

                newCoins = []

                for i in range(num):
                    coinX = x + (coinWidth*i)

                    c = Coins(mode, coinX, y, mode.coinSprite)
                    result = GameMode.checkItemCollision(mode, c)
                    if not result:
                        newCoins.append(c)
                    else: return
                mode.coins.append(newCoins)
                return
    
    def checkItemCollision(mode, item): #check if items collide with other items
        return (GameMode.checkRockCollision(mode, item) 
            or GameMode.checkPlatformCollision(mode, item)
            or (GameMode.checkCoinCollision(mode, item)))

    def checkRockCollision(mode, item):
        for rock in mode.rocks:
            rockX = rock.cx

            if item == mode.player or item == Coins:
                rockX = rock.cx - mode.scrollX

            if ((item.cy >= (rock.cy - rock.itemHeight//2)) 
                and (abs(item.cx - rockX) 
                < (item.itemWidth//2 + rock.itemWidth//2))): 
                return True

        return False
    
    def checkCoinCollision(mode, item): 

        for coin in range(len(mode.coins)):
            for cIndex in range(len(mode.coins[coin])):

                c = mode.coins[coin][cIndex]

                if item == mode.player:
                    cx = c.cx - mode.scrollX
                else:
                    cx = c.cx

                if ((abs(c.cy - item.cy) 
                    < (c.itemHeight//2 + item.itemHeight//2))
                    and (abs(cx - item.cx) 
                    < (c.itemWidth//2 + item.itemWidth//2))):

                    if type(item) != Player2: 
                        return True
                    else: 
                        mode.score += 1
                else:
                    if type(item) == Player2:
                        mode.newCoins[coin].append(c)

        return False

    def checkPlatformCollision(mode, item): 

        mode.onPlatform = False

        for platform in mode.platforms:
            for p in platform:

                pX = p.cx
                if item == mode.player:
                    pX = p.cx - mode.scrollX

                if(abs((p.cy - item.cy))
                    < (p.itemHeight//2 + item.itemHeight//2)
                    and 
                    abs(pX - item.cx) < (p.itemWidth//2 + item.itemWidth//2)):

                    if not(type(item) == Player2):
                        return True
                    else:

                        if (item.cy < (p.cy - p.itemHeight//2)):
                            item.cy = (
                            p.cy - p.itemHeight//2 - item.itemHeight//2) #stand on platform
                            mode.onPlatform = True

                        #player cannot go through the platform from the bottom
                        elif (item.cy >= (p.cy + p.itemHeight//2) 
                                and not(item.cy >= item.startY)): 
                            item.cy = p.cy + p.itemHeight//2 + 30 
        return False
    
    def checkFireCollision(mode, player):

        for f in mode.fire:
            if (abs((f.cy - mode.player.cy)) 
                < mode.player.itemHeight//2
                and abs(f.cx - mode.scrollX - mode.player.cx) 
                < mode.player.itemWidth//2):
                mode.gameOver = True
                GameMode.gameOver(mode)
                return

    def checkMagnetCollision(mode, player):

        m = mode.magnets[0]
        if (abs((m.cy - mode.player.cy)) 
                < m.itemHeight//2 + mode.player.itemHeight//2
                and abs(m.cx - mode.scrollX - mode.player.cx) 
                < (m.itemWidth//2 + mode.player.itemWidth//2)):
            return True

    def checkPlayerCollision(mode):

        if not mode.magnetMode:
            if GameMode.checkRockCollision(mode, mode.player):
                mode.gameOver = True
                GameMode.gameOver(mode)
                return
            if mode.dragonMode: 
                GameMode.checkFireCollision(mode, mode.player)
            
        mode.newCoins = [[] for num in range(len(mode.coins))]
        GameMode.checkCoinCollision(mode, mode.player)
        mode.coins = mode.newCoins

        GameMode.checkPlatformCollision(mode, mode.player)

        if mode.magnets != []:
            if GameMode.checkMagnetCollision(mode, mode.player):
                mode.magnets.pop(0) #remove magnet from screen bc player eats the magnet
                mode.magnetMode = True

    def drawCursor(mode, canvas):
        canvas.create_image(mode.mouseX, mode.mouseY, 
        image= mode.cursor.sprite)

    def drawRocks(mode, canvas):
        for rock in mode.rocks:
            rock.draw(canvas)
    
    def drawCoins(mode, canvas):
        for coin in mode.coins:
            for c in coin:
                c.draw(canvas)

    def drawPlatforms(mode, canvas):
        for platform in mode.platforms:
            for p in platform:
                p.draw(canvas)

    def drawDragon(mode, canvas):

        for fire in mode.fire:
            fire.draw(canvas)

        for dragon in mode.dragons:
            dragon.draw(canvas)

    def drawDots(mode, canvas):
        for d in mode.dots:
            d.draw(canvas)

    def drawMagnet(mode, canvas):
        for m in mode.magnets:
            m.draw(canvas)

    def drawNewHighestScore(mode, canvas):
        if mode.newHighestScore:
            canvas.create_text(mode.width//2, mode.height//3, 
            text = f'CONGRATULATION! YOU GOT THE NEW HIGHEST SCORE!',
            fill = "white",
            font = "FreeMono 24 bold")

    def drawGameOver(mode, canvas):

        canvas.create_text(mode.width//2, mode.height*2//3, 
            text = f'SCORE: {mode.score}',
            fill = "white",
            font = "FreeMono 24 bold")

        canvas.create_text(mode.width//2, mode.height*2//3 + 30, 
            text = f'HIGHEST SCORE: {mode.highestScore}',
            fill = "white",
            font = "FreeMono 24 bold")

    def getCachedPhotoImage(mode, image):
        # stores a cached version of the PhotoImage in the PIL/Pillow image
        if ('cachedPhotoImage' not in image.__dict__):
            image.cachedPhotoImage = ImageTk.PhotoImage(image)
        return image.cachedPhotoImage

    def rms(frame):
        count = len(frame)/2
        format = "%dh"%(count)
        # short is 16 bit int
        shorts = struct.unpack( format, frame )

        sum_squares = 0.0
        for sample in shorts:
            n = sample * GameMode.SHORT_NORMALIZE
            sum_squares += n*n
        # compute the rms 
        rms = math.pow(sum_squares/count,0.5)
        return rms * 1000

    def detectVoice(mode):

        start_point = 0
        mode.stream.start_stream() 

        chunk = mode.stream.read(GameMode.CHUNK_SIZE, 
        exception_on_overflow = False) #read audio data from the stream 

        mode.rms_value = GameMode.rms(chunk)

        #returns active = True if player volume is bigger than min volume threshold
        active = True if mode.rms_value > mode.threshold  else False
        
        if active: #perform actions
        
            #avoid making new dots when player makes one continuous sounds
            if not mode.prevActivity: 
                GameMode.makeDots(mode)
    
            if mode.rms_value > mode.threshold + 30: #jump  
                if ((mode.player.cy < mode.height//4) 
                and not(mode.player.cy >= mode.player.startY)): #player falls when exceeding the limit
                    mode.player.cy += 20
                else:
                    if not(mode.onPlatform): 
                        mode.player.cy -= 25 + mode.threshold//3
                mode.scrollX += mode.speed

            else: 
                mode.scrollX += mode.speed
                
            mode.prevActivity = True

        else:

            if not(mode.onPlatform):

                #player falls only when its not standing on the ground
                #or the platform
                if ((mode.player.cy < mode.player.startY)
                and not(mode.player.cy >= mode.player.startY)): 
                    mode.player.cy += 20

            mode.prevActivity = False

        sys.stdout.flush()
        mode.stream.stop_stream()
        
    def gameOver(mode):

        if mode.score > mode.highestScore:
            mode.highestScore = mode.score
            mode.newHighestScore = True

            #override the highest score in the highestscore.txt file
            with open(path.join(mode.dir, highestScore), 'r+') as f:
                f.write(str(mode.score))
        else:
            mode.newHighestScore = False

    def redrawAll(mode, canvas):
        
        mode.player.draw(canvas)
        canvas.create_image(mode.width//2, mode.height*2//5, image = mode.background)
        canvas.create_image(mode.plusCX, mode.plusCY, image = mode.plus)
        canvas.create_image(mode.minusCX, mode.minusCY, image = mode.minus)
        canvas.create_image(mode.questionCX, mode.questionCY, image = mode.question)
        canvas.create_image(mode.playCX, mode.playCY, image = mode.play)
        canvas.create_text(mode.width*2//18 - 10, mode.height*2//15 + 10, 
                            text = f'MOVE {int(mode.threshold)}', fill = "gray34", 
                            font = "FreeMono 28 bold")
        canvas.create_text(mode.width*2//18 - 10, mode.height*3//15, 
                            text = f'JUMP {int(mode.threshold) + 30}', fill = "gray34", 
                            font = "FreeMono 28 bold")

        canvas.create_text(mode.width//2, mode.height//15, 
                            text = f'VOLUME {int(mode.rms_value)}', fill = "gray25", 
                            font = "FreeMono 28 bold")

        GameMode.drawDots(mode, canvas)
        GameMode.drawCoins(mode, canvas)
        GameMode.drawRocks(mode, canvas)
        GameMode.drawPlatforms(mode, canvas)
        GameMode.drawDragon(mode, canvas)
        mode.player.draw(canvas)
        GameMode.drawMagnet(mode, canvas)
        GameMode.drawCursor(mode, canvas)

        if mode.gameOver: 
            canvas.create_image(mode.width//2, mode.height//2, 
            image = ImageTk.PhotoImage(mode.gameOverSprite))
            GameMode.drawGameOver(mode, canvas)
            GameMode.drawNewHighestScore(mode, canvas)
        
        else:
            canvas.create_text(mode.width*14/15, mode.height/20, 
            text = f'SCORE: {mode.score}',
            fill = "gray25",
            font = "FreeMono 24 bold",
            anchor = "ne")
            GameMode.drawCursor(mode, canvas)

class HelpMode(Mode):

    def appStarted(mode):
        sprite1 = mode.loadImage("help1.png")
        mode.sprite1 = mode.scaleImage(sprite1, 2/5)
        sprite2 = mode.loadImage("help2.png")
        mode.sprite2 = mode.scaleImage(sprite2, 2/5)
        sprite3 = mode.loadImage("singlePlayer.gif")
        mode.sprite3 = mode.scaleImage(sprite3, 2)

        mode.counter = 0
        mode.counterLength = 4

    def keyPressed(mode, event):
        if event.key == "Right":
            mode.counter += 1
        elif event.key == "Left":
            mode.counter -= 1
        elif event.key == "Enter":
            mode.counter = 0
            mode.app.setActiveMode(mode.app.startVoiceDemo)

        mode.counter = mode.counter % mode.counterLength

    def redrawAll(mode, canvas):
        canvas.create_rectangle(0, 0, mode.width, mode.height, fill = "lightpink3")
        if mode.counter == 0:
            canvas.create_text(mode.width//2 - 30, mode.height//2, 
                            text = 
                            """
                            Your goal is to eat as many coins as possible.

                            Each coin = 1 point

                            You can make the player move/jump by 
                            making loud-enough noises.

                            NEXT PAGE: Press right arrow ->
                            SKIP: Press Enter

                            """, fill = "white", font = "FreeMono 25 bold")
        elif mode.counter == 1:
            canvas.create_image(mode.width//2, mode.height//2, image = ImageTk.PhotoImage(mode.sprite1))
            canvas.create_text(mode.width//2 - 35, mode.height*19//20, 
                            text = 
                            """
                            NEXT PAGE: Press right arrow ->
                            LAST PAGE: Press left arrow  <-
                            SKIP: Press Enter
                            """, fill = "white", font = "FreeMono 15 bold")
        elif mode.counter == 2:
        
            canvas.create_image(mode.width//2, mode.height//2, 
                                image = ImageTk.PhotoImage(mode.sprite2))
            canvas.create_text(mode.width//2 - 35, mode.height*19//20, 
                            text = 
                            """
                            NEXT PAGE: Press right arrow ->
                            LAST PAGE: Press left arrow  <-
                            SKIP: Press Enter
                            """, fill = "white", font = "FreeMono 15 bold")
        elif mode.counter == 3:

            canvas.create_text(mode.width//2 - 30, mode.height//3, 
            text = "Press Enter to continue...",
            fill = "white", font = "FreeMono 25 bold")
            canvas.create_image(mode.width//2, mode.height//2 + 30, 
                                image = ImageTk.PhotoImage(mode.sprite3))
    
class HelpMode2(HelpMode):

    def keyPressed(mode, event):
        if event.key == "Right":
            mode.counter += 1
        elif event.key == "Left":
            mode.counter -= 1
        elif event.key == "Enter":
            mode.counter = 0
            mode.app.setActiveMode(mode.app.gameMode)

        mode.counter = mode.counter % mode.counterLength

class MyModalApp(ModalApp):

    def appStarted(app):
        mixer.init()
        mixer.music.load('music.wav')
        mixer.music.play(-1, 0.0)
        app.gameMode = GameMode()
        app.splashScreen = SplashScreenMode()
        app.voiceDemoMode = VoiceDemoMode()
        app.startVoiceDemo = startVoiceDemo()
        app.helpMode = HelpMode()
        app.helpMode2 = HelpMode2()
        app.setActiveMode(app.splashScreen)      

app = MyModalApp(width=900, height=660)
mixer.music.stop()
