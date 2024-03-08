import sys
import os
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from abc import abstractmethod
import sounddevice as sd
import numpy as np
import soundfile as sf
import threading
import queue
from scipy.io import savemat
from loguru import logger

from audio.wave import FMCW
from audio.wave import Kasami_sequence
import utils as utils
import math

# To see the size of the saved pickle
def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"


class Audio:
    def __init__(self,
                 playargs
                 ):
        self.playargs = playargs
        self.event = threading.Event()
        self._thread = False
        self._sampling_rate = playargs.sampling_rate
        self._blocksize = playargs.blocksize
        self._buffersize = playargs.buffersize
        self._nchannels = playargs.nchannels
        self._q = queue.Queue(maxsize=self._buffersize)  # buffer queue
        self.datarec = np.array([], dtype=np.float32)

    def begin(self):
        if not self._thread:
            self._thread = True
        threading.Thread(target=self._run).start()

    def end(self):
        self._thread = False
        self.event.set()

    def getData(self):
        try:
            # logger.debug(f"self._q.size(): {self._q.qsize()}")
            return self._q.get_nowait()
        except queue.Empty:
            print("Buffer is empty: increase buffersize", file=sys.stderr)
            return np.zeros(self._buffersize)

    @abstractmethod
    def _run(self):
        pass

    @abstractmethod
    def _callback(self, indata, outdata, frames, time, status):
        pass

    def _get_buffer(self):
        return self._q.get()

    def get_record(self):
        return self.datarec

    def __str__(self):
        return str(self.__class__.__name__)


class AudioPlayer(Audio):

    def __init__(self,
                 playargs
                 ):
        super(AudioPlayer, self).__init__(
            playargs)
        self.load_audio_clip()
        self.stream = sd.OutputStream(
            samplerate=self._sampling_rate,
            blocksize=self._blocksize,
            dtype=np.float32,
            callback=self._callback,
            finished_callback=self.event.set,
        )
        logger.debug("AudioPlayer::data_shape: {}".format(self._data.shape))
    
    def load_audio_clip(self):
        dataplay_loader = AcousticDataplayLoader()
        logger.debug("Loading audio clip...")
        self._data, _ = dataplay_loader(self.playargs)
        
    def begin(self):
        if not self._thread:
            self._thread = True
        threading.Thread(target=self._run).start()

    def _run(self):
        try:
            self.stream.start()
            for _ in range(self._buffersize):
                data = self._data[:self._blocksize].astype(np.float32)
                self._q.put_nowait(data)
                self._data = np.roll(self._data, -self._blocksize)
                # assert ((self._data[-self._blocksize:] == 0).all())
            # logger.debug(f"self._data.shape: {self._data.shape}")
            timeout = self._blocksize * self._buffersize / self._sampling_rate
            while self._thread:
                data = self._data[:self._blocksize].astype(np.float32)
                # logger.debug(f"data.shape: {data.shape}")
                self._q.put(data, block=True, timeout=timeout)
                self._data = np.roll(self._data, -self._blocksize)
            # self.event.wait()

        except queue.Full:
            pass
        except Exception as e:
            print(type(e).__name__ + ': ' + str(e))
        finally:
            logger.info("End")
            self.stream.stop()
            self.stream.close()
            self.end()
    
    def _callback(self, outdata, frames, time, status):
        '''
        record simutaneously while playing
        '''
        assert frames == self._blocksize, "frames: {}, blocksize: {}".format(frames, self._blocksize)
        if status.output_underflow:
            print('Output underflow: increase blocksize', file=sys.stderr)
            raise sd.CallbackAbort
        if status.output_overflow:
            print('Output overflow: increase buffersize', file=sys.stderr)
            raise sd.CallbackAbort
        assert not status
        if not self._thread:
            raise sd.CallbackStop
        data = self.getData().reshape(-1, self._nchannels)
        # logger.debug(f"data.shape: {data.shape}")
        if len(data) < len(outdata):
            outdata[:len(data)] = data
            outdata[len(data):] = np.zeros(
                len(outdata) - len(data)).reshape(-1, self._nchannels)
            raise sd.CallbackStop
        else:
            outdata[:] = data

 
            


class AudioPlayandRecord(Audio):
    def __init__(self,
                 playargs,
                 path):
        super().__init__(playargs)
        self.stream = sd.Stream(
            samplerate=self._sampling_rate,
            blocksize=self._blocksize,
            dtype=np.float32,
            callback=self._callback,
            finished_callback=self.event.set,
        )
        dataplay_loader = AcousticDataplayLoader()
        self._data, _ = dataplay_loader(self.playargs)
        self.datarec = np.array([]).reshape(-1, 1)
        self.path = path # path to save the recorded data
        print(self.__dict__)

    def _run(self):
        try:
            self.stream.start()
            for _ in range(self._buffersize):
                data = self._data[:self._blocksize].astype(np.float32)
                self._q.put_nowait(data)
                self._data = utils.roll(self._data, -self._blocksize)
                assert ((self._data[-self._blocksize:] == 0).all())
            timeout = self._blocksize * self._buffersize / self._sampling_rate
            while self._thread:
                data = self._data[:self._blocksize].astype(np.float32)
                self._q.put(data, block=True, timeout=timeout)
                self._data = utils.roll(self._data, -self._blocksize)
            self.event.wait()

        except queue.Full:
            pass
        except Exception as e:
            print(type(e).__name__ + ': ' + str(e))
        finally:
            logger.info("End")
            self.stream.stop()
            self.stream.close()
            self.end()

    def _callback(self, indata, outdata, frames, time, status):
        '''
        record simutaneously while playing
        '''
        assert frames == self._blocksize
        if status.output_underflow:
            print('Output underflow: increase blocksize', file=sys.stderr)
            raise sd.CallbackAbort
        if status.output_overflow:
            print('Output overflow: increase buffersize', file=sys.stderr)
            raise sd.CallbackAbort
        assert not status
        if not self._thread:
            raise sd.CallbackStop

        data = self.getData().reshape(-1, self._nchannels)
        if len(data) < len(outdata):
            outdata[:len(data)] = data
            outdata[len(data):] = np.zeros(
                len(outdata) - len(data)).reshape(-1, self._nchannels)
            raise sd.CallbackStop
        else:
            outdata[:] = data
        self.datarec = np.append(self.datarec, indata.copy())

    def get_record(self):
        return self.datarec

    def save_record(self):
        # print(">" * 50 + "Saving..." + "<" * 50)
        sf.write(self.path + ".wav", self.datarec, self._sampling_rate)  # PCM
        savemat(self.path + ".mat", {"data_rec": self.datarec})
        logger.info("Saved at {}".format(self.path))


class AudioRecorder(Audio):
    def __init__(self,
                 playargs,
                 path):
        super().__init__(playargs)
        self.datarec = np.array([]).reshape(-1, 1)
        self.path = path # path to save the recorded data
        self.stream = sd.InputStream(
            samplerate=self._sampling_rate,
            blocksize=self._blocksize,
            dtype=np.float32,
            callback=self._callback,
            # finished_callback=self.event.set,
        )
        self.file = sf.SoundFile(self.path + ".wav", mode="w", samplerate=self._sampling_rate, channels=1)
        print(self.__dict__)
        
    def begin(self):
        self._thread = True
        threading.Thread(target=self._run).start()
        

    def _run(self):
        try:
            self.stream.start()
            while self._thread:
                pass
            self.event.wait()
            

        except queue.Full:
            pass
        except KeyboardInterrupt:
            pass
        # except Exception as e:
        #     print(type(e).__name__ + ': ' + str(e))
        finally:
            logger.info("End")
            self.stream.stop()
            self.stream.close()
            self.file.close()
    
    def end(self):
        self._thread = False
        self.event.set()

    def _callback(self, indata, frames, time, status):
        '''
        record 
        '''
        assert frames == self._blocksize
        if not self._thread:
            raise sd.CallbackStop

        self.file.write(indata[:])

    def get_record(self):
        return self.datarec

    def save_record(self):
        # print(">" * 50 + "Saving..." + "<" * 50)
        # sf.write(self.path + ".wav", self.datarec, self._sampling_rate)  # PCM
        file_size = os.path.getsize(self.path + ".wav")
        human_readable_size = convert_size(file_size)
        if file_size is not None:
            with open(os.path.join(os.path.dirname(__file__), "acoustic_data_saved_status.txt"), "w") as f:
                f.write(f"File can be found at{self.path}. \n")
                f.write(f"File size of {self.path}.wav is: {human_readable_size} \n")
                logger.info(f"File size written to {f}")
        # savemat(self.path + ".mat", {"data_rec": self.datarec}) # MAT
        logger.info("Saved at {}".format(self.path))


class AcousticDataplayLoader():
    def __init__(self) -> None:
        pass

    def _parse_args(self, play_arg):
        if play_arg.wave == "Kasami":
            self._set_Kasami_player(play_arg)
        elif play_arg.wave == "chirp":
            self._set_FMCW_player(play_arg)

    def _set_Kasami_player(self, play_arg):
        logger.debug("Set Kasami player")
        self.player = Kasami_sequence(play_arg)

    def _set_FMCW_player(self, play_arg):
        self.player = FMCW(play_arg)

    def __call__(self, play_arg):
        self._dataseq = None
        if play_arg.load_dataplay:
            if hasattr(play_arg, "load_data_seq") and play_arg.load_data_seq:
                dataseq_path = os.path.join(
                    play_arg.dataplay_path, play_arg.dataplay_name[:-4] +
                    "_dataseq.mat"
                )
                try:
                    from scipy.io import loadmat
                    self._dataseq = loadmat(dataseq_path)["data_seq"]
                except FileNotFoundError:
                    raise FileNotFoundError(
                        "File {} not found".format(dataseq_path))

            dataplay_path = os.path.join(
                play_arg.dataplay_path, play_arg.dataplay_name)
            try:
                self._dataplay, _ = sf.read(dataplay_path)
            except FileNotFoundError:
                raise FileNotFoundError(
                    "File {} not found".format(dataplay_path))
        else:
            self._parse_args(play_arg)
            self._dataplay = self.player()
        self._dataplay = self._dataplay.reshape(-1, play_arg.nchannels)
        return self._dataplay, self._dataseq


