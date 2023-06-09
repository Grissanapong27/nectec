#!/usr/bin/env python3

#for mac user
#xcode-select --install
#brew remove portaudio
#brew install portaudio --HEAD
#pip3 install pyaudio

from __future__ import division

import re
import sys
import configparser
import pyaudio
from six.moves import queue

import time
import re
import grpc
from threading import Thread

import PartiiService_pb2_grpc
import PartiiService_pb2

_SERVER_IP = "127.0.0.1"
_SERVER_PORT = 27080
_AUDIO_INPUT = ""
_AUDIO_SAMPLE_RATE = 16000
_AUDIO_CODEC = "LINEAR16"
_PACKAGE_SIZE = 1024
_CHUNK_LEN_SECONE = 0.2
_VERBOSE = 0

_API_KEY = ""
_CLIENT_ID = ""

_VAD_THRESHOLD = 0.5
_NUM_CHANNELS = 1
_DECODE_CHANEL = 0
_MODEL_KEY = "default"
_PROTOCOL = "partii"
_ENABLE_TEXTNORM = "true"
_ENABLE_PARTIAL = "true"
_ENABLE_VAD = "true"
_ENABLE_ENDPOINT = "true"
_NUMBER_TARGET = "english"
_VIEW = "sentent"

_ENABLE_ENGLISH_THAI_WORD_PAIR = "false"
_ENABLE_THAI_ENGLISH_WORD_PAIR = "false"
_ENABLE_EMOTION = "false"
_ENABLE_SPEAKER_DIARIZATION = "false"
_NUM_SPEAKER = 1

# Audio recording parameters
CHUNK = int(_AUDIO_SAMPLE_RATE / 10)  # 100ms
EXIT_APP_STATUS = False

def convMilliFormat(millis):
	time = (float(millis) * 1000);
	mil = time % 1000;
	sec = (time / 1000) % 60;
	minute = (time / (1000 * 60)) % 60;
	hour = (time / (1000 * 60 * 60)) % 24;
	return "{:02d}:{:02d}:{:02d},{:03d}".format(int(hour), int(minute), int(sec), int(mil));

class MicrophoneStream(object):
    """Opens a recording stream as a generator yielding the audio chunks."""
    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk
        # Create a thread-safe buffer of audio data
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            # The API currently only supports 1-channel (mono) audio
            # https://goo.gl/z757pE
            channels=1, rate=self._rate,
            input=True, frames_per_buffer=self._chunk,
            # Run the audio stream asynchronously to fill the buffer object.
            # This is necessary so that the input device's buffer doesn't
            # overflow while the calling thread makes network requests, etc.
            stream_callback=self._fill_buffer,
        )
        self.closed = False
        return self

    def __exit__(self, type, value, traceback):
        self.stop_rec()
        
    def stop_rec(self):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        # Signal the generator to terminate so that the client's
        # streaming_recognize method will not block the process termination.
        self._buff.put(None)
        self._audio_interface.terminate()
        print("Stop record...")
        
    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """Continuously collect data from the audio stream, into the buffer."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            if EXIT_APP_STATUS == True :
                self.stop_rec()
            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break
            yield PartiiService_pb2.AudioData(ByteChunk=b''.join(data), Bytelen=len(b''.join(data)), Datatype=PartiiService_pb2.AudioDataType.SPEECH)
            time.sleep(0.1)

def GetAvailable():
    available = 0
    channel = grpc.insecure_channel('{}:{}'.format(_SERVER_IP, _SERVER_PORT))
    stub = PartiiService_pb2_grpc.TranscriptionStub(channel)
    metadata = (
                    ('apikey', str(_API_KEY)),
                    ('client-id', str(_CLIENT_ID)),
                    ('modelkey', str(_MODEL_KEY)),
                    ('protocol', str(_PROTOCOL))
                   )
    response = stub.GetAvailable(PartiiService_pb2.EmptyMsg(), metadata=metadata)
    available = response.Available
    return available

def run():
    retries = 3
    timeout = 3

    while retries > 0:

        if GetAvailable() > 0 :

            if _VERBOSE != "0" : 
                print('{}:{}'.format(_SERVER_IP, _SERVER_PORT))
            
            with grpc.insecure_channel('{}:{}'.format(_SERVER_IP, _SERVER_PORT)) as channel:
                stub = PartiiService_pb2_grpc.TranscriptionStub(channel)
                
                metadata = (
                            ('apikey', str(_API_KEY)),
                            ('sampling-rate', str(_AUDIO_SAMPLING_RATE)),
                            ('client-id', str(_CLIENT_ID)),
                            ('vad-threshold', str(_VAD_THRESHOLD)),
                            ('num-channels', str(_NUM_CHANNELS)),
                            ('decode-channels', str(_DECODE_CHANEL)),
                            ('modelkey', str(_MODEL_KEY)),
                            ('audio-codec', str(_AUDIO_CODEC)),
                            ('protocol', str(_PROTOCOL)),
                            ('enable-textnorm', str(_ENABLE_TEXTNORM)),
                            ('enable-partial', str(_ENABLE_PARTIAL)),
                            ('enable-vad', str(_ENABLE_VAD)),
                            ('enable-endpoint', str(_ENABLE_ENDPOINT)),
                            ('number-target', str(_NUMBER_TARGET)),
                            ('enable-english-thai-word-pair', str(_ENABLE_ENGLISH_THAI_WORD_PAIR)),
                            ('enable-thai-english--word-pair', str(_ENABLE_THAI_ENGLISH_WORD_PAIR)),
                            ('enable-emotion', str(_ENABLE_EMOTION)),
                            ('enable-speaker-diarization', str(_ENABLE_SPEAKER_DIARIZATION)),
                            ('num-speaker', str(_NUM_SPEAKER))
                        )
                
                if _VERBOSE != "0" : 
                    print(metadata)

                with MicrophoneStream(_AUDIO_SAMPLE_RATE, CHUNK) as stream:

                    audio_generator = stream.generator()
                    print("\nStart capture audio...")
                    
                    responses = stub.SingleTranscribe( audio_generator, metadata=metadata)
                    
                    try:
                        for response in responses:
                            if(response.Status == PartiiService_pb2.StatusCode.Ok):
                                if(response.sentenceType == PartiiService_pb2.ResultType.PARTIAL):
                                    if _VERBOSE != "0" : 
                                        print("sentenceNumber %s " %(response.sentenceNumber))
                                        print("transcript %s " %(response.transcript))
                                        print("confidence %s " %(response.confidence))
                                        print("startTime %s, %s " %(response.startTime, convMilliFormat(response.startTime)))
                                        print("endTime %s, %s " %(response.endTime, convMilliFormat(response.endTime)))
                            
                                elif(response.sentenceType == PartiiService_pb2.ResultType.RESULT):
                                    EXIT_APP_STATUS = True
                                    if _VIEW == "sentent" :
                                        print("sentenceNumber %s " %(response.sentenceNumber))
                                        print("transcript %s " %(response.transcript))
                                        print("confidence %s " %(response.confidence))
                                        print("startTime %s " %(response.startTime))
                                        print("endTime %s " %(response.endTime))
                                
                                    if _VIEW == "word" :
                                        for w in response.words:
                                            print("\twordNumber %s " %(w.wordNumber))
                                            print("\tword %s " %(w.word))
                                            print("\tconfidence %s " %(w.confidence))
                                            print("\tstartTime %s " %(w.startTime))
                                            print("\tendTime %s " %(w.endTime))
                                            
                                    if _VIEW == "phone" :
                                        for w in response.words:
                                            for p in w.phones:
                                                print("\t\tphoneNumber %s " %(p.phoneNumber))
                                                print("\t\tphone %s " %(p.phone))
                                                print("\t\tconfidence %s " %(p.confidence))
                                                print("\t\tstartTime %s " %(p.startTime))
                                                print("\t\tendTime %s " %(p.endTime))
                                                
                                elif(response.sentenceType == PartiiService_pb2.ResultType.FINISHED):
                                
                                    if _VERBOSE != "0" :
                                        print("Last respond from server [%s] " %(response.transcript))

                                    retries = 0
                                    break
                            
                            elif(response.Status == PartiiService_pb2.StatusCode.Failed):
                                print("ERROR [%s] " %(response.transcript))
                                print('Waiting for %s seconds'%(timeout))
                                time.sleep(timeout)
                                retries -= 1
                        
                    except:
                        print("An exception occurred")
                        print('Waiting for %s seconds'%(timeout))
                        time.sleep(timeout)
                        retries -= 1
        
        else:
            
            print('Waiting for %s seconds'%(timeout))
            time.sleep(timeout)
            retries -= 1        
            
if __name__ == '__main__':
    start_time = time.time()
    config = configparser.ConfigParser()
    config.read('config.ini')

    _SERVER_IP = config['DEFAULT']['_SERVER_IP']
    _SERVER_PORT = int(config['DEFAULT']['_SERVER_PORT'])
    _AUDIO_INPUT = config['DEFAULT']['_AUDIO_INPUT']
    _AUDIO_SAMPLING_RATE = int(config['DEFAULT']['_AUDIO_SAMPLING_RATE'])
    _AUDIO_CODEC = config['DEFAULT']['_AUDIO_CODEC']
    _CHUNK_LEN_SECONE = config['DEFAULT']['_CHUNK_LEN_SECOND']
    _VERBOSE = config['DEFAULT']['_VERBOSE']
    
    _PACKAGE_SIZE = float(_CHUNK_LEN_SECONE) * float(_AUDIO_SAMPLE_RATE) * 2
    _API_KEY = config['DEFAULT']['_API_KEY']
    _CLIENT_ID = config['DEFAULT']['_CLIENT_ID']
    
    _VAD_THRESHOLD = config['DEFAULT']['_VAD_THRESHOLD']
    _NUM_CHANNELS = config['DEFAULT']['_NUM_CHANNELS']
    _DECODE_CHANEL = config['DEFAULT']['_DECODE_CHANEL']
    _MODEL_KEY = config['DEFAULT']['_MODEL_KEY']
    _PROTOCOL = config['DEFAULT']['_PROTOCOL']
    _ENABLE_TEXTNORM = config['DEFAULT']['_ENABLE_TEXTNORM']
    _ENABLE_PARTIAL = config['DEFAULT']['_ENABLE_PARTIAL']
    _ENABLE_VAD = config['DEFAULT']['_ENABLE_VAD']
    _ENABLE_ENDPOINT = config['DEFAULT']['_ENABLE_ENDPOINT']
    _NUMBER_TARGET = config['DEFAULT']['_NUMBER_TARGET']
    _VIEW = config['DEFAULT']['_VIEW']
    
    _ENABLE_ENGLISH_THAI_WORD_PAIR = config['DEFAULT']['_ENABLE_ENGLISH_THAI_WORD_PAIR']
    _ENABLE_THAI_ENGLISH_WORD_PAIR = config['DEFAULT']['_ENABLE_THAI_ENGLISH_WORD_PAIR']
    _ENABLE_EMOTION = config['DEFAULT']['_ENABLE_EMOTION'] #not support yet
    _ENABLE_SPEAKER_DIARIZATION = config['DEFAULT']['_ENABLE_SPEAKER_DIARIZATION'] #not support yet
    _NUM_SPEAKER = config['DEFAULT']['_NUM_SPEAKER'] #not support yet
    
    CHUNK = int(_AUDIO_SAMPLE_RATE / 10)  # 100ms
    
    run()
            
    end_time = time.time()
    print("Runtime of the program is ", (end_time - start_time))