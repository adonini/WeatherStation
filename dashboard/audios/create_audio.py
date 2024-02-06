from gtts import gTTS
import subprocess

# Function to create audio file with gTTS and convert it to WAV
def create_and_save_wav(message, filename):
    # Create MP3 file using gTTS
    tts = gTTS(text=message, lang="en")
    mp3_filename = f"{filename}.mp3"
    tts.save(mp3_filename)

    # Convert MP3 to WAV using ffmpeg
    wav_filename = f"{filename}.wav"
    subprocess.run(["ffmpeg", "-i", mp3_filename, wav_filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Remove the temporary MP3 file
    subprocess.run(["rm", mp3_filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    return wav_filename

# Messages and filenames
messages_and_filenames = {
    "humidity": "Hey, attention! The outside humidity is above the safety limit for observation.",
    "rain": "Hey, what's up? Just telling you that it's raining outside. I repeat, it's raining.",
    "hum_rain": "Hey, Attention! The outside condition is beyond several safety limits: humidity is too high and it's raining.",
    "wind": "Hey, attention! The wind speed is above the safety limit for observation.",
    "hum_wind": "Hey, attention! The wind speed is above the safety limits and so is humidity. I repeat wind speed and humidity are too high.",
    "wind_rain": "Hey, attention! It's raining outside and the wind speed is above the safety limits.",
    "hum_wind_rain": "Hey, attention! Weather is above all the safety limits. Stop operation and abandon the ship."
}

# Create and save WAV files
for key, message in messages_and_filenames.items():
    wav_filename = create_and_save_wav(message, key)
    print(f"{key} audio saved as {wav_filename}")