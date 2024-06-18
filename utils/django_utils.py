from django.core.files.storage import FileSystemStorage

from ReganamKevolehc_BE import settings

contenting_temp_storage = FileSystemStorage(location=settings.CONTENTING_TEMP_MEDIA_ROOT,
                                            base_url=settings.CONTENTING_TEMP_MEDIA_URL)
contenting_video_storage = FileSystemStorage(location=settings.CONTENTING_VIDEO_MEDIA_ROOT,
                                             base_url=settings.CONTENTING_VIDEO_MEDIA_URL)
contenting_audio_storage = FileSystemStorage(location=settings.CONTENTING_AUDIO_MEDIA_ROOT,
                                             base_url=settings.CONTENTING_AUDIO_MEDIA_URL)
playlist_storage = FileSystemStorage(location=settings.PLAYLIST_MEDIA_ROOT,
                                     base_url=settings.PLAYLIST_MEDIA_URL)
