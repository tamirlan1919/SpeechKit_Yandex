import io
import grpc
import pydub
import argparse

import yandex.cloud.ai.tts.v3.tts_pb2 as tts_pb2
import yandex.cloud.ai.tts.v3.tts_service_pb2_grpc as tts_service_pb2_grpc

# Задайте настройки синтеза.
# Вместо iam_token передавайте api_key при аутентификации с API-ключом 
def synthesize(api_key, text) -> pydub.AudioSegment: 
    request = tts_pb2.UtteranceSynthesisRequest(
        text=text,
        output_audio_spec=tts_pb2.AudioFormatOptions(
            container_audio=tts_pb2.ContainerAudio(
                container_audio_type=tts_pb2.ContainerAudio.WAV
            )
        ),
        # Параметры синтеза
       hints=[
    tts_pb2.Hints(voice='alexander'),  # (Опционально) Задайте голос. Значение по умолчанию marina
    tts_pb2.Hints(role='good'),        # (Опционально) Укажите амплуа, только если голос их имеет
    tts_pb2.Hints(speed=1.1)           # (Опционально) Задайте скорость синтеза
],

        loudness_normalization_type=tts_pb2.UtteranceSynthesisRequest.LUFS
    )

    # Установите соединение с сервером.
    cred = grpc.ssl_channel_credentials()
    channel = grpc.secure_channel('tts.api.cloud.yandex.net:443', cred)
    stub = tts_service_pb2_grpc.SynthesizerStub(channel)

    # Отправьте данные для синтеза.
    it = stub.UtteranceSynthesis(request, metadata=(

    # Параметры для аутентификации с IAM-токеном
    # Параметры для аутентификации с API-ключом от имени сервисного аккаунта
      ('authorization', f'Api-Key {api_key}'),
    ))

    # Соберите аудиозапись по порциям.
    try:
        audio = io.BytesIO()
        for response in it:
            audio.write(response.audio_chunk.data)
        audio.seek(0)
        return pydub.AudioSegment.from_wav(audio)
    except grpc._channel._Rendezvous as err:
        print(f'Error code {err._state.code}, message: {err._state.details}')
        raise err


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--token', required=True, help='IAM token or API key')
    parser.add_argument('--text', required=True, help='Text for synthesis')
    parser.add_argument('--output', required=True, help='Output file')
    args = parser.parse_args()

    audio = synthesize('AQVN0fiGepILDWchpaGpBf81jITFo_SQY6AruXBb', 'Привет дружище')
    with open(args.output, 'wb') as fp:
        audio.export(fp, format='wav')
