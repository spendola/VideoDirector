# requisites
# pip install moviepy
import os
import sys
import pytube
import moviepy
import shutil
from moviepy.editor import VideoFileClip
from moviepy.editor import AudioFileClip
from moviepy.editor import CompositeAudioClip
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import imagehash
from gtts import gTTS
import cv2 as cv
import numpy as np
from sklearn.cluster import KMeans
import statistics
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip

def main():
	localPath = os.path.dirname(os.path.realpath(__file__))
	if(len(sys.argv) > 1):
		action = sys.argv[1]
		if(action == "merge"):
			output = sys.argv[2]
			files = sys.argv[3]
			Concatenate(files.replace(" ", "").split(","), os.path.join(localPath, output))
		elif(action == "downloadslice"):
			output = sys.argv[2]
			link = sys.argv[3]
			name = sys.argv[4]
			labels = sys.argv[5]
			DownloadSource(link, os.path.join(localPath, output))
			videoname = os.listdir(os.path.join(localPath, output))
			SliceVideo(os.path.join(localPath, output, videoname[0]), name, labels)		
		elif(action == "download"):
			output = sys.argv[2]
			link = sys.argv[3]
			DownloadSource(link, os.path.join(localPath, output))
		elif(action == "slice"):
			source = sys.argv[2]
			name = sys.argv[3]
			labels = sys.argv[4]
			SliceVideo(source, name, labels)
		elif(action == "overlay"):
			source = sys.argv[2]
			output = sys.argv[3]
			overlay = sys.argv[4]
			start = sys.argv[5]
			duration = sys.argv[6]
			OverlayImage(source, output, overlay, int(start), int(duration))
		elif(action == "text"):
			source = sys.argv[2]
			output = sys.argv[3]
			top = sys.argv[4]
			left = sys.argv[5]
			text = sys.argv[6]
			DrawText(source, output, int(top), int(left), text)
		elif(action == "speech"):
			output = sys.argv[2]
			text = sys.argv[3]
			GenSpeech(output, text)
		elif(action == "mix"):
			output = sys.argv[2]
			video = sys.argv[3]
			audio = sys.argv[4]
			composite = (sys.argv[5] == "True")
			MixAudio(output, video, audio, composite, 1.0)
		else:
			print("Unknown action")
	else:
		print("Arguments found")

                
def PresentMenu():
	print("Video Director 0.1\n")
	localPath = os.path.dirname(os.path.realpath(__file__))
	sources = os.path.join(localPath, "videos")
	print("1) Download Source Videos")
	print("2) Concatenate Videos")
	print("3) Split Videos")
	choice = int(input("> "))
	if(choice == 1):
		link = input("YouTube link: ")
		output = input("Name: ")
		DownloadSource(link, os.path.join(sources, output))
	if(choice == 2):
		videos = input("Sources: ")
		output = input("Output: ")
		Concatenate(videos.replace(" ", "").split(","), output)
	if(choice == 3):
		video = input("Source: ")
		clips = int(input("Clips: "))
		length = int(input("Seconds: "))
		SplitVideo(video, clips, length)
	if(choice == 4):
		FindFrameBreaks()

def SliceVideo(source, name, labels, step=2):
	localPath = os.path.dirname(os.path.realpath(__file__))
	source = VideoFileClip(os.path.join(localPath, source))
	print("Video duration: " + str(source.duration))
	
	print("preparing temporary directory")
	if(os.path.exists(os.path.join(localPath, "temp_slice"))):
		shutil. rmtree(os.path.join(localPath, "temp_slice"))
	os.mkdir(os.path.join(localPath, "temp_slice"))
	
	print("calculating histograms")
	histograms = []
	for i in range(int(source.duration/step)-1):
		framepath = os.path.join(localPath, "temp_slice", "frame_" + str(i) + ".png")
		source.save_frame(framepath, t=i*step)
		
		if(i > 0):
			prevframe = os.path.join(localPath, "temp_slice", "frame_" + str(i-1) + ".png")
			img1 = cv.imread(prevframe)
			img2 = cv.imread(framepath)
			img1 = cv.cvtColor(img1, cv.COLOR_BGR2RGB)
			img2 = cv.cvtColor(img2, cv.COLOR_BGR2RGB)
			h1 = hist = cv.calcHist([img1], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
			h2 = hist = cv.calcHist([img2], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
			histograms.append(cv.compareHist(h1, h2, cv.HISTCMP_CHISQR))
	
	print("calculate median")
	breaks = []
	median = statistics.median(histograms)
	for i in range(len(histograms)):
		if(histograms[i]>median):
			breaks.append(i)
			print(i)
	
	print("extracting video slices")
	for i in range(1, len(breaks)):
		if( (breaks[i] - breaks[i-1]) >= 3):
			print("capture from " + str(breaks[i-1]) + " to " + str(breaks[i]))
			subclip = source.subclip(breaks[i-1]+1, breaks[i])
			subclip.write_videofile(os.path.join(localPath, "temp_slice", "test_" + str(i) + ".mp4"))
	print("done")

	
def FindFrameBreaks(step=2, tolerance=10):
	localPath = os.path.dirname(os.path.realpath(__file__))
	source = VideoFileClip(os.path.join(localPath, "videos", "temuco.mp4"))
	print("Video Duration: " + str(source.duration))
	lastframe = 0
	for i in range(int(source.duration/step)-1):
		source.save_frame(os.path.join(localPath, "frame_1.png"), t = i*step)
		hash1 = imagehash.average_hash(Image.open(os.path.join(localPath, "frame_1.png"))) 
		source.save_frame(os.path.join(localPath, "frame_2.png"), t = (i+1)*step)
		hash2 = imagehash.average_hash(Image.open(os.path.join(localPath, "frame_2.png")))
		if(hash1 - hash2 > tolerance):
			print("change " + str(hash1 - hash2) + " at " + str((i+1)*step) + " seconds")
			if(lastframe > 0 and ((i*step)-lastframe) > 4):
				subclip = source.subclip(lastframe, i*step)
				subclip.write_videofile(os.path.join(localPath, str(lastframe) + ".mp4"))
			lastframe = (i+1)+step
			
	
def DownloadSource(link, output):
	print("Downloading Video Source")
	print(link)
	
	try:
		yt = pytube.YouTube(link)
	except:
		print("Unable to create connection to YouTube")
	
	mp4files = yt.streams.filter(file_extension="mp4")
	mp4files360 = mp4files.get_by_resolution("360p")
	
	try: 
		# downloading the video 
		mp4files360.download(output) 
	except: 
		print("Some Error!") 
	print('Task Completed!') 
	
	
def Concatenate(videoPaths, outputPath, method="compose"):
	print("Initializing Video Concatenation")
	localPath = os.path.dirname(os.path.realpath(__file__))
	sources = [os.path.join(os.path.join(localPath, "videos"), source) for source in videoPaths] 
	print("loading clips")
	clips = [VideoFileClip(video) for video in sources]
	if(method == "reduce"):
		print("reducing videos")
		# calculate minimum width & height across all clips
		minHeight = min([c.h for c in clips])
		minWidth = min([c.w for c in clips])
		clips = [c.resize(newsize=(min_width, min_height)) for c in clips]
		# concatenate the final video
		final_clip = Concatenate(clips, outputPath, method="compose")
	elif(method == "compose"):
		print("composing video")
		final_clip = moviepy.editor.concatenate_videoclips(clips)
		print("saving video")
		final_clip.write_videofile(os.path.join(localPath, outputPath))
		
def MixAudio(output, videosource, audiosource, composite=False, volumefactor=1.0):
	video = VideoFileClip(videosource)
	audio = AudioFileClip(audiosource)
	if(volumefactor != 1.0):
		audio = audio.volumex(volumefactor)
	
	if(composite):
		final_audio = CompositeAudioClip([video.audio, audio])
	else:
		final_audio = audio
	
	final_video = video.set_audio(audio)
	final_video.write_videofile(output, audio_codec='aac')
	
	
			
def SplitVideo(source, clips, length):
	localPath = os.path.dirname(os.path.realpath(__file__))
	originalVideo = os.path.join(localPath, "videos", source)
	for i in range(clips):
		start = i * length
		end = (i+1) * length
		clipPath = os.path.join(localPath, str(start) + "_to_" +str(end) + ".mp4")
		moviepy.video.io.ffmpeg_tools.ffmpeg_extract_subclip(originalVideo, start, end, clipPath)
		
def OverlayImage(source, output, overlay, start, duration):
	video = VideoFileClip(source)
	title = moviepy.editor.ImageClip(overlay).set_start(start).set_duration(duration).set_pos(("center","center"))
	#.resize(height=50) # if you need to resize...

	final = moviepy.editor.CompositeVideoClip([video, title])
	final.write_videofile(output)

def DrawText(source, output, top, left, text):
        localPath = os.path.dirname(os.path.realpath(__file__))
        img = Image.open(source)
        draw = ImageDraw.Draw(img)
        myFont = ImageFont.truetype(os.path.join(localPath, "Fonts", "Aller_Bd.ttf"), 24)
        draw.text((top, left), text, font=myFont, fill=(0, 0, 0))
        img.show()

#accent could be es for spain of com.mx for mexico
def GenSpeech(output, text, accent='es'):
        tts = gTTS(text, lang='es', tld=accent)
        tts.save(output)

if __name__ == "__main__":
	main()
