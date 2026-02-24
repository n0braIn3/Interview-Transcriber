import os
import io
import wave
import numpy as np

from openai import AsyncOpenAI
import chainlit as cl

# ==== OpenAI Client (API key from .env or environment) ====
openai_client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ==== SILENCE DETECTION ====
SILENCE_THRESHOLD = 3500
SILENCE_TIMEOUT = 1300  # in ms

# ==== HELPER: RMS berechnen (ersetzt audioop.rms, da audioop in Python 3.13+ entfernt wurde) ====
def compute_rms(data: bytes, sample_width: int) -> int:
    """Berechnet den RMS-Wert eines Audio-Buffers (int16)."""
    audio_array = np.frombuffer(data, dtype=np.int16)
    if len(audio_array) == 0:
        return 0
    return int(np.sqrt(np.mean(audio_array.astype(np.float64) ** 2)))

# ==== TEXT-TO-SPEECH STUB ====
async def text_to_speech(text: str, format="audio/wav"):
    # In echt hier TTS einbauen, z.B. ElevenLabs oder gTTS
    return "output.wav", b"FAKE_AUDIO_BYTES"

# ==== HELPER FUNCTIONS ====
@cl.step(type="tool")
async def speech_to_text(audio_file):
    response = await openai_client.audio.transcriptions.create(
        model="whisper-1", file=("audio.wav", audio_file, "audio/wav")
    )
    return response.text

@cl.step(type="tool")
async def generate_text_answer(transcription):
    message_history = cl.user_session.get("message_history", [])

    # User-Nachricht hinzufügen
    message_history.append({"role": "user", "content": transcription})
    cl.user_session.set("message_history", message_history)

    # OpenAI Chat Completion
    response = await openai_client.chat.completions.create(
        model="gpt-4o",
        messages=message_history,
        temperature=0.2
    )

    # Assistant-Nachricht speichern
    assistant_msg = {
        "role": "assistant",
        "content": response.choices[0].message.content
    }
    message_history.append(assistant_msg)
    cl.user_session.set("message_history", message_history)

    return assistant_msg["content"]

# ==== CHAT START ====
@cl.on_chat_start
async def start():
    cl.user_session.set("message_history", [])
    await cl.Message(
        content="Welcome! Type a message or press `P` to talk."
    ).send()

# ==== TEXT INPUT ====
@cl.on_message
async def on_message(message: cl.Message):
    transcription = message.content
    answer = await generate_text_answer(transcription)
    await cl.Message(content=answer).send()

# ==== AUDIO HANDLING ====
@cl.on_audio_start
async def on_audio_start():
    cl.user_session.set("silent_duration_ms", 0)
    cl.user_session.set("is_speaking", False)
    cl.user_session.set("audio_chunks", [])
    return True

@cl.on_audio_chunk
async def on_audio_chunk(chunk: cl.InputAudioChunk):
    audio_chunks = cl.user_session.get("audio_chunks", [])
    audio_chunk = np.frombuffer(chunk.data, dtype=np.int16)
    audio_chunks.append(audio_chunk)
    cl.user_session.set("audio_chunks", audio_chunks)

    # Silence detection
    last_elapsed_time = cl.user_session.get("last_elapsed_time", chunk.elapsedTime)
    silent_duration_ms = cl.user_session.get("silent_duration_ms", 0)
    is_speaking = cl.user_session.get("is_speaking", False)

    time_diff_ms = chunk.elapsedTime - last_elapsed_time
    cl.user_session.set("last_elapsed_time", chunk.elapsedTime)

    # RMS mit numpy statt audioop (Python 3.13+ kompatibel)
    audio_energy = compute_rms(chunk.data, 2)
    if audio_energy < SILENCE_THRESHOLD:
        silent_duration_ms += time_diff_ms
        cl.user_session.set("silent_duration_ms", silent_duration_ms)
        if silent_duration_ms >= SILENCE_TIMEOUT and is_speaking:
            cl.user_session.set("is_speaking", False)
            await process_audio()
    else:
        cl.user_session.set("silent_duration_ms", 0)
        cl.user_session.set("is_speaking", True)

@cl.on_audio_end
async def on_audio_end():
    """Wird aufgerufen wenn der Nutzer das Mikrofon stoppt."""
    await process_audio()

async def process_audio():
    if not (audio_chunks := cl.user_session.get("audio_chunks")):
        return

    concatenated = np.concatenate(audio_chunks)
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(24000)
        wav_file.writeframes(concatenated.tobytes())
        frames = wav_file.getnframes()
        rate = wav_file.getframerate()

    wav_buffer.seek(0)
    cl.user_session.set("audio_chunks", [])

    duration = frames / float(rate)
    if duration <= 1.5:
        await cl.Message(content="Audio too short, please try again.").send()
        return

    transcription = await speech_to_text(wav_buffer)
    input_audio_el = cl.Audio(content=wav_buffer.getvalue(), mime="audio/wav")
    await cl.Message(author="You", type="user_message", content=transcription, elements=[input_audio_el]).send()

    answer = await generate_text_answer(transcription)
    output_name, output_audio = await text_to_speech(answer)
    output_audio_el = cl.Audio(auto_play=True, mime="audio/wav", content=output_audio)
    await cl.Message(content=answer, elements=[output_audio_el]).send()