import os
import math
import wave
import struct

def generate_tone(freq: float, duration: float, sample_rate: int = 44100, volume: float = 0.5, decay: float = 2.0) -> list[float]:
    samples = []
    num_samples = int(duration * sample_rate)
    for i in range(num_samples):
        t = i / sample_rate
        env = math.exp(-decay * t)
        val = volume * env * math.sin(2 * math.pi * freq * t)
        samples.append(val)
    return samples

def generate_chord_chime(notes: list[float], duration: float = 1.0, sample_rate: int = 44100, volume: float = 0.4) -> list[float]:
    num_samples = int(duration * sample_rate)
    samples = [0.0] * num_samples
    for note in notes:
        for i in range(num_samples):
            t = i / sample_rate
            env = math.exp(-3.5 * t)
            samples[i] += (volume / len(notes)) * env * math.sin(2 * math.pi * note * t)
    return samples

def generate_clock_tick(duration: float = 0.08, sample_rate: int = 44100, volume: float = 0.6) -> list[float]:
    num_samples = int(duration * sample_rate)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        env = math.exp(-50.0 * t)
        # High-pitch click + hollow body tone
        val = volume * env * (0.6 * math.sin(2 * math.pi * 1800 * t) + 0.4 * math.sin(2 * math.pi * 900 * t))
        samples.append(val)
    return samples

def generate_whoosh(duration: float = 0.4, sample_rate: int = 44100, volume: float = 0.35) -> list[float]:
    import random
    num_samples = int(duration * sample_rate)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        # Hanning window envelope
        env = 0.5 * (1 - math.cos(2 * math.pi * i / num_samples))
        # Sweeping noise band
        freq = 300 + 1200 * math.sin(math.pi * i / num_samples)
        noise = (random.random() * 2 - 1)
        val = volume * env * noise * 0.4 + volume * env * 0.6 * math.sin(2 * math.pi * freq * t)
        samples.append(val)
    return samples

def generate_outro_riser(duration: float = 1.2, sample_rate: int = 44100, volume: float = 0.4) -> list[float]:
    num_samples = int(duration * sample_rate)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        env = 0.5 * (1 - math.cos(math.pi * i / num_samples))
        freq = 400 + 600 * (t / duration) ** 1.5
        val = volume * env * math.sin(2 * math.pi * freq * t)
        samples.append(val)
    return samples

def write_wav(file_path: str, samples: list[float], sample_rate: int = 44100):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with wave.open(file_path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        raw = bytearray()
        for s in samples:
            # Clip between -1.0 and 1.0
            clamped = max(-1.0, min(1.0, s))
            int_val = int(clamped * 32767.0)
            raw.extend(struct.pack("<h", int_val))
        wf.writeframes(raw)

def ensure_sfx_assets(output_dir: str = "data/assets/sfx") -> dict[str, str]:
    """Generates all needed royalty-free SFX if they don't already exist."""
    os.makedirs(output_dir, exist_ok=True)
    
    paths = {
        "whoosh": os.path.join(output_dir, "whoosh.wav"),
        "clock_tick": os.path.join(output_dir, "clock_tick.wav"),
        "correct_bell": os.path.join(output_dir, "correct_bell.wav"),
        "outro_riser": os.path.join(output_dir, "outro_riser.wav")
    }
    
    if not os.path.exists(paths["whoosh"]):
        write_wav(paths["whoosh"], generate_whoosh())
        
    if not os.path.exists(paths["clock_tick"]):
        write_wav(paths["clock_tick"], generate_clock_tick())
        
    if not os.path.exists(paths["correct_bell"]):
        # Major chord bell (E5=659Hz, G#5=830Hz, B5=987Hz, E6=1318Hz)
        write_wav(paths["correct_bell"], generate_chord_chime([659.25, 830.61, 987.77, 1318.51], duration=1.2))
        
    if not os.path.exists(paths["outro_riser"]):
        write_wav(paths["outro_riser"], generate_outro_riser())
        
    return paths

if __name__ == "__main__":
    ensure_sfx_assets()
    print("SFX assets generated successfully.")
