import aiofiles
import logging
import os
import datetime

import ffmpeg
from fastapi import UploadFile, File
import azure.cognitiveservices.speech as speechsdk
from azure.storage.blob import BlobClient, ContainerClient
from ..config import get_config, AppConfig
from ..helpers.singleton import singleton
from ..helpers.service import get_storage_client
from ..helpers.filename import get_filename_hash


config: AppConfig = get_config()


@singleton
class FileUpload:
    def __init__(self):
        self.uploads: ContainerClient = get_storage_client(config.env.st_connection_string, config.env.uploads_container)

    async def upload_file(self, user_id: str, username: str, file: UploadFile = File(...)):
        file_content: bytes = await file.read()
        date_now = str(datetime.datetime.now())
        hashed_filename, digest = get_filename_hash(date_now, file_extension=".webm")
        file_path = os.path.join(config.env.tmp_upload_dir, f"{hashed_filename}.webm")

        async with aiofiles.open(file_path, mode='wb') as input_file:
            await input_file.write(file_content)

        try:
            wav_file = os.path.join(config.env.tmp_upload_dir, f"{hashed_filename}.wav")
            ffmpeg.input(file_path).output(wav_file).run()
            os.remove(file_path)

            blob_client: BlobClient = self.uploads.get_blob_client(f"{hashed_filename}.wav")
            blob_client.upload_blob(
                file_content,
                overwrite=True,
                metadata={
                    "user_id": user_id,
                    "username": username,
                    "filename": file.filename,
                    "id": digest
                }
            )

            return wav_file, blob_client.url
        except ffmpeg.Error as e:
            raise e

    async def get_audio_transcription(self, file_path: str, language_code: str = "en-US"):
        speech_config = speechsdk.SpeechConfig(subscription=config.env.azure_stt_key, region=config.env.azure_stt_region)
        speech_config.speech_recognition_language=language_code
        audio_config = speechsdk.audio.AudioConfig(filename=file_path)
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
        speech_recognition_result = speech_recognizer.recognize_once_async().get()
        os.remove(file_path)
        if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return {"status": "success", "data": speech_recognition_result.text, "error": None}
        elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
            logging.error("No speech could be recognized: {}".format(speech_recognition_result.no_match_details))
            return {"status": "failed", "data": None, "error": speech_recognition_result.no_match_details}
        elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = speech_recognition_result.cancellation_details
            logging.error("Speech Recognition canceled: {}".format(cancellation_details.reason))
            if cancellation_details.reason ==  speechsdk.CancellationReason.Error:
                logging.error("Error details: {}".format(cancellation_details.error_details))
                logging.error("Did you set the speech resource key and region values?")
                return {"status": "failed", "data": None, "error": cancellation_details.error_details}
            return {"status": "failed", "data": None, "error": cancellation_details.reason}
