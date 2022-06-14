# LedMusicColor
Changes a WIFI led device color based on the microphone input notes and amplitude.

## How it works
The script will listen to the microphone input, calculate the amplitude and the musical note of the sound with pyaudio, and change the connected led device color and brightness based on it.

**Demonstration**: [Youtube Video](https://www.youtube.com/watch?v=tWj2dWr6zkU)

## How to install

**Dependencies:**
```
pip install -r requirements.txt
```

**Nmap:** https://nmap.org/download.html

**Used device**: https://www.amazon.com.br/Super-Colorida-Prova-Controle-Fonte/dp/B07XBTYGQ2/ref=pd_sbs_sccl_3_1/134-0645885-7430560

Used to discover the led device in the network.

## How to run

```
python3 MusicNotesAndAmplitude.py
```
